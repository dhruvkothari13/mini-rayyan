"""
STAGE 4A: Rule-Based PICO Extraction & Futuristic Span Highlighter (pico_extractor.py)
Extracts Population, Intervention, Comparator, and Outcome spans from abstracts
and renders high-contrast neon pill highlights for human review.
"""

import re
import html
from datetime import datetime
from typing import Dict, List, Optional
from database import get_connection, get_project_config, log_pipeline_run, DB_PATH


def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def extract_pico_from_text(title: str, abstract: str, config: Dict[str, str]) -> Dict[str, str]:
    """
    Transparent keyword and pattern-matching rules for P, I, C, O extraction.
    Flags missing or uncertain fields clearly for human review.
    """
    full_text = f"{title}. {abstract}".strip()
    sentences = split_sentences(abstract) or [title]

    pop_terms = [t.strip() for t in config.get("population_text", "").split(",") if t.strip()]
    int_terms = [t.strip() for t in config.get("intervention_text", "").split(",") if t.strip()]
    comp_terms = [t.strip() for t in config.get("comparator_text", "").split(",") if t.strip()]
    out_terms = [t.strip() for t in config.get("outcome_text", "").split(",") if t.strip()]

    # 1. Population extraction
    pop_span = ""
    pop_patterns = [
        r"((?:overweight |elderly |adult )?(?:patients|adults|participants|subjects|individuals|men|women) with [a-zA-Z0-9\s\-]+?(?:\([nN]\s*=\s*\d+\))?)(?=[,;.]|\s+were|\s+received)",
        r"(\d+\s+(?:adult\s+)?(?:patients|participants|adults|subjects) with [a-zA-Z0-9\s\-]+?)(?=[,;.]|\s+were|\s+received)"
    ]
    for pat in pop_patterns:
        m = re.search(pat, full_text, flags=re.IGNORECASE)
        if m:
            pop_span = m.group(1).strip()
            break
    if not pop_span:
        for s in sentences:
            if any(t.lower() in s.lower() for t in pop_terms):
                pop_span = s
                break

    # 2. Intervention extraction
    int_span = ""
    int_patterns = [
        r"(?:received|assigned to|randomized to|treated with)\s+([a-zA-Z0-9\-\s]+?(?:\d+\s*mg(?:/day|/kg|\s+twice daily|\s+daily)?)?)(?=\s+or\s+|\s+versus\s+|\s+vs\.?\s+|\s+for\s+|[,;.])",
    ]
    for pat in int_patterns:
        m = re.search(pat, full_text, flags=re.IGNORECASE)
        if m:
            int_span = m.group(1).strip()
            break
    if not int_span:
        for t in int_terms:
            m = re.search(rf"(\b{re.escape(t)}\b(?:\s+\d+\s*mg(?:/day|\s+daily|\s+twice daily)?)?)", full_text, flags=re.IGNORECASE)
            if m:
                int_span = m.group(1).strip()
                break

    # 3. Comparator extraction
    comp_span = ""
    comp_patterns = [
        r"(?:compared with|versus|vs\.?|or matching|or)\s+((?:matching\s+)?(?:placebo|sulfonylurea|glimepiride|glipizide|sitagliptin|insulin|standard care|vehicle placebo|warfarin|chemotherapy|docetaxel)(?:\s+\d+\s*mg(?:/day)?)?)",
    ]
    for pat in comp_patterns:
        m = re.search(pat, full_text, flags=re.IGNORECASE)
        if m:
            comp_span = m.group(1).strip()
            break
    if not comp_span:
        for t in comp_terms:
            if re.search(rf"\b{re.escape(t)}\b", full_text, flags=re.IGNORECASE):
                comp_span = t
                break

    # 4. Outcome extraction
    out_span = ""
    out_patterns = [
        r"(?:primary outcome was|primary endpoint was|measured)\s+([^.;]+)",
        r"((?:change|reduction|improvement) in (?:HbA1c|glycated haemoglobin|fasting blood glucose|overall survival|stroke)[^.;]*)"
    ]
    for pat in out_patterns:
        m = re.search(pat, full_text, flags=re.IGNORECASE)
        if m:
            out_span = m.group(1).strip()
            break
    if not out_span:
        for s in sentences:
            if any(t.lower() in s.lower() for t in out_terms):
                out_span = s
                break

    missing = []
    if not pop_span:
        pop_span = "[Uncertain / Not found — needs human review]"
        missing.append("Population")
    if not int_span:
        int_span = "[Uncertain / Not found — needs human review]"
        missing.append("Intervention")
    if not comp_span:
        comp_span = "[Uncertain / No explicit comparator found]"
        missing.append("Comparator")
    if not out_span:
        out_span = "[Uncertain / Not found — needs human review]"
        missing.append("Outcome")

    uncertainty = "All 4 PICO elements extracted" if not missing else f"Uncertain/Missing: {', '.join(missing)}"
    return {
        "population": pop_span,
        "intervention": int_span,
        "comparator": comp_span,
        "outcome": out_span,
        "uncertainty": uncertainty,
    }


def run_pico_extraction(version_id: Optional[int] = None, only_untagged: bool = False, db_path: str = DB_PATH) -> int:
    """Run Step 6 PICO extraction across records in the database."""
    config = get_project_config(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")

    if only_untagged:
        rows = cur.execute("""
        SELECT r.* FROM records r
        LEFT JOIN machine_pico mp ON r.record_id = mp.record_id
        WHERE mp.record_id IS NULL;
        """).fetchall()
    else:
        rows = cur.execute("SELECT * FROM records;").fetchall()

    for row in rows:
        rec = dict(row)
        pico = extract_pico_from_text(rec.get("title", ""), rec.get("abstract", ""), config)
        cur.execute("""
        INSERT INTO machine_pico (
            record_id, population_span, intervention_span, comparator_span, outcome_span, uncertainty_flags, extracted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(record_id) DO UPDATE SET
            population_span = excluded.population_span,
            intervention_span = excluded.intervention_span,
            comparator_span = excluded.comparator_span,
            outcome_span = excluded.outcome_span,
            uncertainty_flags = excluded.uncertainty_flags,
            extracted_at = excluded.extracted_at;
        """, (
            rec["record_id"],
            pico["population"],
            pico["intervention"],
            pico["comparator"],
            pico["outcome"],
            pico["uncertainty"],
            now
        ))

    conn.commit()
    conn.close()
    log_pipeline_run(version_id, "6. PICO Extraction", f"Extracted PICO spans for {len(rows)} records.", db_path)
    return len(rows)


def highlight_pico_html(abstract: str, p_span: str, i_span: str, c_span: str, o_span: str) -> str:
    """Return dark-mode futuristic HTML with glowing P, I, C, O spans inside the abstract."""
    if not abstract:
        return '<div style="color:#94a3b8; font-style:italic;">No abstract available for this record.</div>'

    safe_text = html.escape(abstract)
    badges = [
        (p_span, "rgba(56, 189, 248, 0.22)", "#7dd3fc", "#38bdf8", "P"),
        (i_span, "rgba(16, 185, 129, 0.22)", "#6ee7b7", "#10b981", "I"),
        (c_span, "rgba(245, 158, 11, 0.22)", "#fcd34d", "#f59e0b", "C"),
        (o_span, "rgba(168, 85, 247, 0.25)", "#d8b4fe", "#a855f7", "O"),
    ]
    for span, bg, fg, border, label in badges:
        if not span or span.startswith("[Uncertain"):
            continue
        clean_span = html.escape(span.strip())
        if len(clean_span) >= 4:
            pattern = re.compile(re.escape(clean_span), re.IGNORECASE)
            replacement = (
                f'<span style="background:{bg}; color:{fg}; border:1px solid {border}; '
                f'padding:2px 7px; border-radius:6px; font-weight:600; font-size:0.92em;">'
                f'[{label}] {clean_span}</span>'
            )
            safe_text = pattern.sub(replacement, safe_text, count=1)

    return (
        f'<div style="line-height:1.75; font-size:0.96rem; padding:14px 18px; '
        f'background:rgba(15, 23, 42, 0.85); color:#e2e8f0; border-radius:10px; '
        f'border:1px solid rgba(56, 189, 248, 0.25); box-shadow: inset 0 0 15px rgba(0,0,0,0.4);">'
        f'{safe_text}</div>'
    )