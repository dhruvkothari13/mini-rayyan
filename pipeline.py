"""
STAGE 3: Deduplication & Rule-Based Study Screening (pipeline.py)
Implements multi-tier duplicate grouping and metadata + keyword screening.
Preserves human decisions across re-runs.
"""

import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Any, Optional
from database import get_connection, get_project_config, log_pipeline_run, DB_PATH


# ==============================================================================
# STEP 4: DEDUPLICATION ENGINE
# ==============================================================================
def is_conference_vs_journal(rec_a: Dict[str, Any], rec_b: Dict[str, Any]) -> bool:
    """
    Hackathon Rule (Step 4): 'Further reports of one study (for example a journal
    paper and its conference version) are not duplicates.'
    """
    types_a = (rec_a.get("pub_types") or "").lower() + " " + (rec_a.get("journal") or "").lower()
    types_b = (rec_b.get("pub_types") or "").lower() + " " + (rec_b.get("journal") or "").lower()
    conf_terms = ("conference", "proceedings", "meeting", " congress", "symposium")
    a_is_conf = any(t in types_a for t in conf_terms)
    b_is_conf = any(t in types_b for t in conf_terms)
    return a_is_conf != b_is_conf


def check_pair_duplicate(rec_a: Dict[str, Any], rec_b: Dict[str, Any]) -> Tuple[bool, float, str, str]:
    """
    Compare two records and return:
    (is_match, confidence, status, reason)
    status is 'auto_confirmed' or 'uncertain'
    """
    pmid_a, pmid_b = (rec_a.get("pmid") or "").strip(), (rec_b.get("pmid") or "").strip()
    doi_a, doi_b = (rec_a.get("doi") or "").strip().lower(), (rec_b.get("doi") or "").strip().lower()

    # 1. Exact PMID match
    if pmid_a and pmid_b and pmid_a == pmid_b:
        return True, 1.0, "auto_confirmed", f"Exact PMID match ({pmid_a})"

    # 2. Exact DOI match
    if doi_a and doi_b and doi_a == doi_b:
        return True, 1.0, "auto_confirmed", f"Exact DOI match ({doi_a})"

    # 3. Missing DOI/PMID on at least one record -> Multi-field comparison
    title_a, title_b = rec_a.get("norm_title", ""), rec_b.get("norm_title", "")
    if not title_a or not title_b:
        return False, 0.0, "", ""

    title_sim = SequenceMatcher(None, title_a, title_b).ratio()
    year_a, year_b = rec_a.get("pub_year"), rec_b.get("pub_year")
    year_match = (year_a == year_b) if (year_a and year_b) else True
    auth_a, auth_b = (rec_a.get("first_author") or "").lower(), (rec_b.get("first_author") or "").lower()
    auth_match = (auth_a == auth_b) if (auth_a and auth_b) else False

    if title_sim >= 0.92 and year_match and auth_match:
        # Check if one is a conference report and one is a journal article
        if is_conference_vs_journal(rec_a, rec_b):
            return (
                True,
                0.75,
                "uncertain",
                "Same title/author/year, but one appears to be a Conference Abstract and one a Journal Paper (requires human review)"
            )
        if not doi_a or not doi_b:
            return (
                True,
                0.95,
                "auto_confirmed",
                f"Multi-field match: Normalized Title ({title_sim:.0%}) + Year ({year_a}) + First Author ({auth_a})"
            )
        # Different DOIs but identical title/author/year -> uncertain pair for human review
        return (
            True,
            0.82,
            "uncertain",
            f"High title similarity ({title_sim:.0%}) + Year + First Author, but distinct DOIs ({doi_a} vs {doi_b})"
        )

    return False, 0.0, "", ""


def choose_representative(group_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Keep the record with the richest metadata (DOI + PMID + longest abstract) visible."""
    def score_record(r: Dict[str, Any]) -> Tuple[int, int, int, int]:
        has_doi = 1 if r.get("doi") else 0
        has_pmid = 1 if r.get("pmid") else 0
        abs_len = len(r.get("abstract") or "")
        # Prefer earlier record_id as tie-breaker for stability across reruns
        return (has_doi, has_pmid, abs_len, -int(r["record_id"]))

    return sorted(group_records, key=score_record, reverse=True)[0]


def run_deduplication(version_id: Optional[int] = None, db_path: str = DB_PATH) -> Dict[str, int]:
    """
    Group duplicate records across the database.
    Preserves human-confirmed or human-split decisions and detects Level 2 merge conflicts.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")

    rows = cur.execute("SELECT * FROM records ORDER BY record_id ASC;").fetchall()
    records = [dict(r) for r in rows]

    # Fetch existing human decisions by record_id so we can preserve them and check conflicts
    existing_decisions = {}
    for row in cur.execute("SELECT * FROM reviewer_decisions;").fetchall():
        existing_decisions[row["record_id"]] = dict(row)

    # Fetch groups already manually split by human so we don't re-merge them
    split_record_ids = set()
    for row in cur.execute("SELECT representative_record_id FROM duplicate_groups WHERE status = 'human_split';").fetchall():
        split_record_ids.add(row["representative_record_id"])

    visited = set()
    groups: List[Dict[str, Any]] = []

    for i, rec_a in enumerate(records):
        rid_a = rec_a["record_id"]
        if rid_a in visited:
            continue

        current_group = [rec_a]
        visited.add(rid_a)
        group_status = "auto_confirmed"
        group_reasons = []
        conf_score = 1.0

        if rid_a not in split_record_ids:
            for j in range(i + 1, len(records)):
                rec_b = records[j]
                rid_b = rec_b["record_id"]
                if rid_b in visited or rid_b in split_record_ids:
                    continue

                is_dup, conf, status, reason = check_pair_duplicate(rec_a, rec_b)
                if is_dup:
                    current_group.append(rec_b)
                    visited.add(rid_b)
                    group_reasons.append(reason)
                    conf_score = min(conf_score, conf)
                    if status == "uncertain":
                        group_status = "uncertain"

        groups.append({
            "members": current_group,
            "status": group_status if len(current_group) > 1 else "singleton",
            "reason": "; ".join(set(group_reasons)) if group_reasons else "Unique record",
            "confidence": conf_score
        })

    # Rebuild duplicate_groups while preserving group_id for existing representatives
    auto_hidden_count = 0
    uncertain_count = 0
    conflict_count = 0

    for g in groups:
        members = g["members"]
        rep = choose_representative(members)
        rep_id = rep["record_id"]

        # Check if any member already had a group_id we should reuse
        existing_gid = rep.get("duplicate_group_id")
        if not existing_gid:
            for m in members:
                if m.get("duplicate_group_id"):
                    existing_gid = m["duplicate_group_id"]
                    break

        # Check if members have conflicting human screening decisions
        member_decisions = {}
        for m in members:
            d = existing_decisions.get(m["record_id"])
            if d and d.get("screening_decision"):
                member_decisions[m["record_id"]] = d["screening_decision"]

        unique_human_decisions = set(member_decisions.values())
        has_conflict = 1 if len(unique_human_decisions) > 1 else 0
        conflict_details = ""
        if has_conflict:
            conflict_count += 1
            parts = [f"Record #{k}: {v}" for k, v in member_decisions.items()]
            conflict_details = "Conflicting human decisions in merged group: " + " vs. ".join(parts)

        if existing_gid:
            # Preserve 'human_confirmed' or 'human_split' if previously set by reviewer
            prev = cur.execute("SELECT status FROM duplicate_groups WHERE group_id = ?;", (existing_gid,)).fetchone()
            final_status = prev["status"] if (prev and prev["status"] in ("human_confirmed", "human_split")) else g["status"]
            cur.execute("""
            UPDATE duplicate_groups
            SET representative_record_id = ?, status = ?, match_method = ?,
                has_conflict = ?, conflict_details = ?, updated_at = ?
            WHERE group_id = ?;
            """, (rep_id, final_status, g["reason"], has_conflict, conflict_details, now, existing_gid))
            gid = existing_gid
        else:
            cur.execute("""
            INSERT INTO duplicate_groups (
                representative_record_id, status, match_method, has_conflict, conflict_details, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?);
            """, (rep_id, g["status"], g["reason"], has_conflict, conflict_details, now))
            gid = cur.lastrowid

        if g["status"] == "uncertain":
            uncertain_count += 1

        # Update member records (hide non-representatives unless status is uncertain/human_split)
        for m in members:
            is_rep = (m["record_id"] == rep_id)
            hide = 0 if (is_rep or g["status"] in ("uncertain", "human_split")) else 1
            if hide:
                auto_hidden_count += 1
            cur.execute("""
            UPDATE records
            SET duplicate_group_id = ?, is_hidden_duplicate = ?, dup_confidence = ?, dup_match_reason = ?
            WHERE record_id = ?;
            """, (gid, hide, g["confidence"], g["reason"], m["record_id"]))

    conn.commit()
    conn.close()
    log_pipeline_run(
        version_id,
        "4. Deduplicate",
        f"Formed {len(groups)} groups, hidden {auto_hidden_count} duplicates, {uncertain_count} uncertain pairs, {conflict_count} conflicts.",
        db_path
    )
    return {
        "total_records": len(records),
        "unique_groups": len(groups),
        "hidden_duplicates": auto_hidden_count,
        "uncertain_pairs": uncertain_count,
        "conflicts": conflict_count,
    }


# ==============================================================================
# STEP 5: TRANSPARENT RULE-BASED STUDY SCREENING
# ==============================================================================
def evaluate_record_screening(record: Dict[str, Any], config: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Evaluate a single paper against Step 0 active criteria.
    Uses record metadata first (language, publication type), then documented keyword rules.
    Returns (decision, exclusion_reason, detection_source).
    """
    criteria = config["criteria"]
    title = (record.get("title") or "").lower()
    abstract = (record.get("abstract") or "").lower()
    combined_text = f"{title} {abstract}"
    lang = (record.get("language") or "eng").lower()
    pub_types = (record.get("pub_types") or "").lower()

    reasons = []
    sources = set()

    # 1. Non-English Check (Metadata first, then German/French/Spanish stopword heuristic)
    if criteria.get("exclude_non_english", {}).get("active", True):
        if lang not in ("eng", "en", "english", ""):
            reasons.append(f"non-English (metadata language='{lang}')")
            sources.add("metadata")
        else:
            non_eng_markers = [
                r"\bhintergrund\b", r"\bpatienten\b", r"\bwirksamkeit\b",
                r"\bétude\b", r"\bméthodes\b", r"\bpacientes\b"
            ]
            if any(re.search(pat, combined_text) for pat in non_eng_markers):
                reasons.append("non-English (detected non-English text patterns)")
                sources.add("algorithm")

    # 2. Case Report Check (Metadata PublicationType first, then text pattern)
    if criteria.get("exclude_case_reports", {}).get("active", True):
        if "case reports" in pub_types or "case report" in pub_types:
            reasons.append("case report (metadata pub_type='Case Reports')")
            sources.add("metadata")
        else:
            case_kws = criteria["exclude_case_reports"].get("keywords", [])
            for kw in case_kws:
                if kw.lower() in combined_text:
                    reasons.append(f"case report (matched phrase '{kw}')")
                    sources.add("algorithm")
                    break

    # 3. Animal / Non-Human Study Check
    if criteria.get("exclude_animal", {}).get("active", True):
        animal_kws = criteria["exclude_animal"].get("keywords", [])
        matched_animal = [kw for kw in animal_kws if re.search(rf"\b{re.escape(kw.lower())}\b", combined_text)]
        human_trial_signals = any(
            w in combined_text for w in ["adults with", "patients were randomized", "human subjects", "multicenter trial"]
        )
        if matched_animal and not human_trial_signals:
            reasons.append(f"non-human / animal study (matched '{matched_animal[0]}')")
            sources.add("algorithm")

    # 4. Simulation / In-Silico Check
    if criteria.get("exclude_simulation", {}).get("active", True):
        sim_kws = criteria["exclude_simulation"].get("keywords", [])
        matched_sim = [kw for kw in sim_kws if kw.lower() in combined_text]
        if matched_sim:
            reasons.append(f"simulation study (matched '{matched_sim[0]}')")
            sources.add("algorithm")

    # 5. Optional Custom Criterion
    if criteria.get("custom_exclusion", {}).get("active", False):
        cust_kws = criteria["custom_exclusion"].get("keywords", [])
        matched_cust = [kw for kw in cust_kws if kw.lower() in combined_text]
        if matched_cust:
            reasons.append(f"custom exclusion ({criteria['custom_exclusion']['label']}: '{matched_cust[0]}')")
            sources.add("algorithm")

    if reasons:
        return "Exclude", "; ".join(reasons), "+".join(sorted(sources))

    # If no exclusion triggered, check inclusion relevance (Population + Intervention + Comparator/Outcome)
    if not abstract.strip():
        return "Maybe", "Missing abstract text — requires manual full-text or metadata verification", "metadata"

    pop_terms = [t.strip().lower() for t in config["population_text"].split(",") if t.strip()]
    int_terms = [t.strip().lower() for t in config["intervention_text"].split(",") if t.strip()]
    comp_terms = [t.strip().lower() for t in config["comparator_text"].split(",") if t.strip()]

    has_pop = any(t in combined_text for t in pop_terms) if pop_terms else True
    has_int = any(t in combined_text for t in int_terms) if int_terms else True
    has_comp = any(t in combined_text for t in comp_terms) if comp_terms else True

    if has_pop and has_int and has_comp:
        return "Include", "Meets PICO inclusion criteria (Population, Intervention, and Comparator detected)", "algorithm"
    elif has_int and (has_pop or has_comp):
        return "Maybe", "Uncertain eligibility: Intervention found, but Population or Comparator is unclear — flagged for human review", "algorithm"
    else:
        return "Maybe", "Uncertain relevance to Step 0 PICO terms — flagged for human review", "algorithm"


def run_screening(version_id: Optional[int] = None, only_unscreened: bool = False, db_path: str = DB_PATH) -> Dict[str, int]:
    """
    Run Step 5 screening across records.
    Machine results are saved in `machine_screening`; existing entries in `reviewer_decisions` are untouched.
    """
    config = get_project_config(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")

    if only_unscreened:
        rows = cur.execute("""
        SELECT r.* FROM records r
        LEFT JOIN machine_screening ms ON r.record_id = ms.record_id
        WHERE ms.record_id IS NULL;
        """).fetchall()
    else:
        rows = cur.execute("SELECT * FROM records;").fetchall()

    counts = {"Include": 0, "Exclude": 0, "Maybe": 0}
    for row in rows:
        rec = dict(row)
        decision, reason, source = evaluate_record_screening(rec, config)
        counts[decision] = counts.get(decision, 0) + 1
        cur.execute("""
        INSERT INTO machine_screening (record_id, decision, exclusion_reasons, detection_source, evaluated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(record_id) DO UPDATE SET
            decision = excluded.decision,
            exclusion_reasons = excluded.exclusion_reasons,
            detection_source = excluded.detection_source,
            evaluated_at = excluded.evaluated_at;
        """, (rec["record_id"], decision, reason, source, now))

    conn.commit()
    conn.close()
    log_pipeline_run(
        version_id,
        "5. Screen",
        f"Screened {len(rows)} records -> Include: {counts['Include']}, Exclude: {counts['Exclude']}, Maybe: {counts['Maybe']}",
        db_path
    )
    return counts