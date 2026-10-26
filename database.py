"""
STAGE 1: Database Layer (database.py)
Handles SQLite persistence, Step 0 PICO configuration, query versions,
record storage, duplicate groups, machine vs. human decisions, and audit logs.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

DB_PATH = os.environ.get("MINI_RAYYAN_DB", "mini_rayyan.db")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Create a thread-safe SQLite connection with dictionary-like row access."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Initialize all tables required for Level 1 and Level 2."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    # 1. Step 0: Review Question, PICO & Criteria Configuration
    cur.execute("""
    CREATE TABLE IF NOT EXISTS project_config (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        review_question TEXT NOT NULL,
        population_text TEXT NOT NULL,
        intervention_text TEXT NOT NULL,
        comparator_text TEXT NOT NULL,
        outcome_text TEXT NOT NULL,
        criteria_json TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 2. Step 1: Query Versions (Saves hit counts & supports Level 2 versioning)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS query_versions (
        version_id INTEGER PRIMARY KEY AUTOINCREMENT,
        version_name TEXT NOT NULL,
        boolean_query TEXT NOT NULL,
        date_from INTEGER NOT NULL,
        date_to INTEGER NOT NULL,
        sources TEXT NOT NULL,
        pubmed_hits INTEGER DEFAULT 0,
        epmc_hits INTEGER DEFAULT 0,
        approved INTEGER DEFAULT 0,
        fetched INTEGER DEFAULT 0,
        parent_version_id INTEGER,
        created_at TEXT NOT NULL
    );
    """)

    # 3. Step 2 & 3: Paper Records (Nothing is ever deleted)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS records (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        pmid TEXT,
        doi TEXT,
        title TEXT NOT NULL,
        norm_title TEXT NOT NULL,
        abstract TEXT,
        authors TEXT,
        first_author TEXT,
        pub_year INTEGER,
        journal TEXT,
        pages TEXT,
        language TEXT DEFAULT 'eng',
        pub_types TEXT,
        source TEXT NOT NULL,
        duplicate_group_id INTEGER,
        is_hidden_duplicate INTEGER DEFAULT 0,
        dup_confidence REAL DEFAULT 1.0,
        dup_match_reason TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # 4. Many-to-Many Link between Query Versions and Records
    cur.execute("""
    CREATE TABLE IF NOT EXISTS query_records (
        version_id INTEGER NOT NULL,
        record_id INTEGER NOT NULL,
        discovered_at TEXT NOT NULL,
        PRIMARY KEY (version_id, record_id),
        FOREIGN KEY (version_id) REFERENCES query_versions(version_id),
        FOREIGN KEY (record_id) REFERENCES records(record_id)
    );
    """)

    # 5. Step 4: Duplicate Groups (Decisions attach to groups)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS duplicate_groups (
        group_id INTEGER PRIMARY KEY AUTOINCREMENT,
        representative_record_id INTEGER NOT NULL,
        status TEXT DEFAULT 'auto_confirmed', -- auto_confirmed, uncertain, human_confirmed, human_split
        match_method TEXT,
        has_conflict INTEGER DEFAULT 0,
        conflict_details TEXT,
        updated_at TEXT NOT NULL
    );
    """)

    # 6. Step 5: Machine Screening Results (Kept separate from human decisions)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS machine_screening (
        record_id INTEGER PRIMARY KEY,
        decision TEXT NOT NULL, -- Include, Exclude, Maybe
        exclusion_reasons TEXT,
        detection_source TEXT,  -- metadata, algorithm, or both
        evaluated_at TEXT NOT NULL,
        FOREIGN KEY (record_id) REFERENCES records(record_id)
    );
    """)

    # 7. Step 6: Machine PICO Extractions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS machine_pico (
        record_id INTEGER PRIMARY KEY,
        population_span TEXT,
        intervention_span TEXT,
        comparator_span TEXT,
        outcome_span TEXT,
        uncertainty_flags TEXT,
        extracted_at TEXT NOT NULL,
        FOREIGN KEY (record_id) REFERENCES records(record_id)
    );
    """)

    # 8. Step 7: Human-in-the-Loop Decisions (Keyed by group_id to survive query changes)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reviewer_decisions (
        group_id INTEGER PRIMARY KEY,
        record_id INTEGER NOT NULL,
        screening_decision TEXT, -- Include, Exclude, Maybe
        exclusion_reason TEXT,
        reviewer_notes TEXT,
        pico_p TEXT,
        pico_i TEXT,
        pico_c TEXT,
        pico_o TEXT,
        reviewer_name TEXT DEFAULT 'Lead Reviewer',
        updated_at TEXT NOT NULL
    );
    """)

    # 9. Human Override Audit Log & Pipeline Run Log
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        reviewer_name TEXT NOT NULL,
        action_type TEXT NOT NULL, -- screening_override, duplicate_override, pico_edit
        target_id INTEGER NOT NULL,
        old_value TEXT,
        new_value TEXT,
        reason TEXT,
        timestamp TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS run_log (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        version_id INTEGER,
        step_name TEXT NOT NULL,
        details TEXT,
        timestamp TEXT NOT NULL
    );
    """)

    # Seed default Step 0 configuration if empty (Type 2 Diabetes Metformin example from spec)
    cur.execute("SELECT COUNT(*) as cnt FROM project_config WHERE id = 1;")
    if cur.fetchone()["cnt"] == 0:
        default_criteria = {
            "exclude_animal": {
                "active": True,
                "label": "Exclude animal / non-human studies",
                "reason": "The review question is strictly about human adult patients.",
                "keywords": ["mice", "murine", "rat", "rats", "wistar", "sprague-dawley", "canine", "porcine", "animal model", "in vitro", "xenograft"]
            },
            "exclude_simulation": {
                "active": True,
                "label": "Exclude simulation / in-silico studies",
                "reason": "Simulation studies model mathematical results and do not measure real patients.",
                "keywords": ["monte carlo simulation", "in silico", "computer simulation", "markov model simulation", "mathematical model only", "simulated cohort"]
            },
            "exclude_non_english": {
                "active": True,
                "label": "Exclude non-English studies",
                "reason": "The review team cannot reliably verify non-English full text.",
                "keywords": []
            },
            "exclude_case_reports": {
                "active": True,
                "label": "Exclude single-patient case reports",
                "reason": "A single patient case report cannot demonstrate an average treatment effect.",
                "keywords": ["case report", "a case of", "year-old male presented", "year-old female presented", "single patient case"]
            },
            "custom_exclusion": {
                "active": False,
                "label": "Exclude pediatric / gestational populations",
                "reason": "Target population is restricted to adults with type 2 diabetes.",
                "keywords": ["gestational diabetes", "pediatric", "adolescents", "neonatal"]
            }
        }
        cur.execute("""
        INSERT INTO project_config (
            id, review_question, population_text, intervention_text,
            comparator_text, outcome_text, criteria_json, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            1,
            "In adults with type 2 diabetes, does metformin, compared with placebo or sulfonylurea, lower HbA1c?",
            "Adults with type 2 diabetes, T2DM, diabetic patients, type II diabetes",
            "Metformin, glucophage, biguanide",
            "Placebo, sulfonylurea, glimepiride, glipizide, sitagliptin, standard care, insulin",
            "HbA1c, glycated haemoglobin, glycosylated hemoglobin, fasting blood glucose, glycemic control",
            json.dumps(default_criteria),
            datetime.now().isoformat(timespec="seconds")
        ))

    conn.commit()
    conn.close()


def get_project_config(db_path: str = DB_PATH) -> Dict[str, Any]:
    conn = get_connection(db_path)
    row = conn.execute("SELECT * FROM project_config WHERE id = 1;").fetchone()
    conn.close()
    data = dict(row)
    data["criteria"] = json.loads(data["criteria_json"])
    return data


def save_project_config(
    review_question: str,
    population_text: str,
    intervention_text: str,
    comparator_text: str,
    outcome_text: str,
    criteria: Dict[str, Any],
    db_path: str = DB_PATH
) -> None:
    conn = get_connection(db_path)
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute("""
    UPDATE project_config
    SET review_question = ?, population_text = ?, intervention_text = ?,
        comparator_text = ?, outcome_text = ?, criteria_json = ?, updated_at = ?
    WHERE id = 1;
    """, (
        review_question, population_text, intervention_text,
        comparator_text, outcome_text, json.dumps(criteria), now
    ))
    conn.commit()
    conn.close()


def log_pipeline_run(version_id: Optional[int], step_name: str, details: str, db_path: str = DB_PATH) -> None:
    conn = get_connection(db_path)
    conn.execute("""
    INSERT INTO run_log (version_id, step_name, details, timestamp)
    VALUES (?, ?, ?, ?);
    """, (version_id, step_name, details, datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    conn.close()


def log_human_audit(
    reviewer_name: str,
    action_type: str,
    target_id: int,
    old_value: str,
    new_value: str,
    reason: str,
    db_path: str = DB_PATH
) -> None:
    conn = get_connection(db_path)
    conn.execute("""
    INSERT INTO audit_log (reviewer_name, action_type, target_id, old_value, new_value, reason, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (
        reviewer_name, action_type, target_id,
        str(old_value), str(new_value), reason,
        datetime.now().isoformat(timespec="seconds")
    ))
    conn.commit()
    conn.close()


def create_query_version(
    version_name: str,
    boolean_query: str,
    date_from: int,
    date_to: int,
    sources: List[str],
    pubmed_hits: int,
    epmc_hits: int,
    parent_version_id: Optional[int] = None,
    db_path: str = DB_PATH
) -> int:
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    cur.execute("""
    INSERT INTO query_versions (
        version_name, boolean_query, date_from, date_to,
        sources, pubmed_hits, epmc_hits, approved, fetched,
        parent_version_id, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?);
    """, (
        version_name, boolean_query, date_from, date_to,
        ",".join(sources), pubmed_hits, epmc_hits, parent_version_id, now
    ))
    vid = cur.lastrowid
    conn.commit()
    conn.close()
    log_pipeline_run(vid, "1. Query Created", f"Query '{boolean_query}' ({date_from}-{date_to}) -> PubMed: {pubmed_hits}, EuropePMC: {epmc_hits}", db_path)
    return vid


def store_fetched_records(version_id: int, papers: List[Dict[str, Any]], db_path: str = DB_PATH) -> Dict[str, int]:
    """
    Incremental storage: if a record with the same (source + PMID/DOI + norm_title)
    already exists in `records`, reuse its `record_id` and link it in `query_records`.
    Nothing is ever duplicated in storage or deleted.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    new_count = 0
    reused_count = 0

    for p in papers:
        pmid = (p.get("pmid") or "").strip() or None
        doi = (p.get("doi") or "").strip().lower() or None
        norm_title = p.get("norm_title", "").strip()
        source = p.get("source", "Unknown")

        # Check if exact same record from same source or exact same PMID+DOI+Title is already stored
        existing = None
        if pmid and doi:
            existing = cur.execute(
                "SELECT record_id FROM records WHERE pmid = ? AND doi = ? AND source = ?;",
                (pmid, doi, source)
            ).fetchone()
        elif pmid:
            existing = cur.execute(
                "SELECT record_id FROM records WHERE pmid = ? AND source = ?;",
                (pmid, source)
            ).fetchone()
        elif doi:
            existing = cur.execute(
                "SELECT record_id FROM records WHERE doi = ? AND source = ?;",
                (doi, source)
            ).fetchone()
        else:
            existing = cur.execute(
                "SELECT record_id FROM records WHERE norm_title = ? AND pub_year = ? AND source = ?;",
                (norm_title, p.get("pub_year"), source)
            ).fetchone()

        if existing:
            record_id = existing["record_id"]
            reused_count += 1
        else:
            cur.execute("""
            INSERT INTO records (
                pmid, doi, title, norm_title, abstract, authors, first_author,
                pub_year, journal, pages, language, pub_types, source, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                pmid, doi, p.get("title", "Untitled"), norm_title,
                p.get("abstract", ""), p.get("authors", ""), p.get("first_author", ""),
                p.get("pub_year"), p.get("journal", ""), p.get("pages", ""),
                p.get("language", "eng"), p.get("pub_types", "Journal Article"),
                source, now
            ))
            record_id = cur.lastrowid
            new_count += 1

        # Link record to this query version
        cur.execute("""
        INSERT OR IGNORE INTO query_records (version_id, record_id, discovered_at)
        VALUES (?, ?, ?);
        """, (version_id, record_id, now))

    cur.execute("UPDATE query_versions SET approved = 1, fetched = 1 WHERE version_id = ?;", (version_id,))
    conn.commit()
    conn.close()
    log_pipeline_run(
        version_id,
        "2. Fetch & Store",
        f"Stored {new_count} new records, linked {reused_count} existing records.",
        db_path
    )
    return {"new": new_count, "reused": reused_count, "total": len(papers)}