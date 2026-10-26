"""
STAGE 5: Level 2 Query-Change Loop, Diff View & Conflict Resolution (level2_loop.py)
Implements query versioning, incremental fetch, group merge conflict detection,
version diffs, and 1-click state reversion.
"""

from typing import Dict, List, Any, Optional
from database import get_connection, log_pipeline_run, DB_PATH
from pipeline import run_deduplication, run_screening
from pico_extractor import run_pico_extraction


def get_query_version_details(version_id: int, db_path: str = DB_PATH) -> Dict[str, Any]:
    """Fetch metadata and hit statistics for a specific query version."""
    conn = get_connection(db_path)
    q = conn.execute("SELECT * FROM query_versions WHERE version_id = ?;", (version_id,)).fetchone()
    if not q:
        conn.close()
        return {}
    
    records = conn.execute("""
    r.*, qr.discovered_at
    FROM query_records qr
    JOIN records r ON qr.record_id = r.record_id
    WHERE qr.version_id = ?;
    """, (version_id,)).fetchall()
    conn.close()

    return {
        "version": dict(q),
        "records": [dict(r) for r in records],
        "record_count": len(records)
    }


def compute_query_diff(old_version_id: int, new_version_id: int, db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Compute diff between two query versions (Required by Level 2 spec):
    - Added records
    - Removed records (found in old, not in new)
    - Newly merged duplicate groups
    """
    conn = get_connection(db_path)
    old_ids = {row["record_id"] for row in conn.execute("SELECT record_id FROM query_records WHERE version_id = ?;", (old_version_id,)).fetchall()}
    new_ids = {row["record_id"] for row in conn.execute("SELECT record_id FROM query_records WHERE version_id = ?;", (new_version_id,)).fetchall()}
    conn.close()

    added_ids = new_ids - old_ids
    removed_ids = old_ids - new_ids

    conn = get_connection(db_path)
    added_records = []
    if added_ids:
        placeholders = ",".join("?" * len(added_ids))
        added_records = [dict(r) for r in conn.execute(f"SELECT * FROM records WHERE record_id IN ({placeholders});", list(added_ids)).fetchall()]

    removed_records = []
    if removed_ids:
        placeholders = ",".join("?" * len(removed_ids))
        removed_records = [dict(r) for r in conn.execute(f"SELECT * FROM records WHERE record_id IN ({placeholders});", list(removed_ids)).fetchall()]

    # Check for conflicts in duplicate groups
    conflicts = conn.execute("SELECT * FROM duplicate_groups WHERE has_conflict = 1;").fetchall()
    conflict_list = [dict(c) for c in conflicts]
    conn.close()

    return {
        "added_count": len(added_ids),
        "removed_count": len(removed_ids),
        "added_records": added_records,
        "removed_records": removed_records,
        "conflicts": conflict_list,
    }


def resolve_duplicate_conflict(group_id: int, chosen_record_id: int, reviewer_name: str, db_path: str = DB_PATH) -> None:
    """Resolve a group merge conflict by confirming the representative record and clearing conflict flags."""
    conn = get_connection(db_path)
    conn.execute("""
    UPDATE duplicate_groups
    SET representative_record_id = ?, has_conflict = 0, conflict_details = NULL, status = 'human_confirmed', updated_at = CURRENT_TIMESTAMP
    WHERE group_id = ?;
    """, (chosen_record_id, group_id))
    conn.execute("""
    UPDATE records
    SET is_hidden_duplicate = CASE WHEN record_id = ? THEN 0 ELSE 1 END
    WHERE duplicate_group_id = ?;
    """, (chosen_record_id, group_id))
    conn.commit()
    conn.close()
    log_pipeline_run(None, "Level 2 Conflict Resolved", f"Resolved merge conflict for Group #{group_id}, choosing Record #{chosen_record_id}", db_path)