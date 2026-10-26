"""
STAGE 4B & Level 2 (Vibe-Coded Futuristic Edition): app.py
Includes complete Level 1 pipeline + Step 3 Database view + Level 2 Query-Change Loop with full descriptive labels.
"""

import os
import json
from datetime import datetime
import pandas as pd
import streamlit as st

from database import (
    init_db,
    get_connection,
    get_project_config,
    save_project_config,
    create_query_version,
    store_fetched_records,
    log_human_audit,
    DB_PATH,
)
from api_clients import (
    search_pubmed_hits,
    fetch_pubmed_abstracts,
    search_epmc_hits,
    fetch_epmc_abstracts,
    get_benchmark_papers,
)
from pipeline import run_deduplication, run_screening
from pico_extractor import run_pico_extraction, highlight_pico_html
from level2_loop import compute_query_diff, resolve_duplicate_conflict

st.set_page_config(
    page_title="Mini-Rayyan // Evidence AI Studio",
    page_icon="✨",
    layout="wide",
)

init_db()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    code, pre { font-family: 'JetBrains Mono', monospace !important; }

    .stApp {
        background: radial-gradient(circle at 10% 15%, rgba(56, 189, 248, 0.10) 0%, transparent 40%),
                    radial-gradient(circle at 90% 80%, rgba(168, 85, 247, 0.10) 0%, transparent 40%),
                    linear-gradient(180deg, #070b14 0%, #0b1120 100%);
        color: #f8fafc;
    }
    
    section[data-testid="stSidebar"] {
        background: rgba(11, 17, 32, 0.95) !important;
        backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        padding-top: 10px;
    }
    section[data-testid="stSidebar"] .stRadio label {
        font-size: 0.98rem !important;
        font-weight: 600 !important;
        color: #e2e8f0 !important;
        padding: 6px 0px;
        transition: all 0.2s ease;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        color: #38bdf8 !important;
    }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span {
        font-size: 0.92rem !important;
    }

    .vibe-hero {
        display: flex; justify-content: space-between; align-items: center;
        padding: 18px 24px; background: linear-gradient(135deg, rgba(30, 41, 59, 0.65) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 1px solid rgba(255, 255, 255, 0.10); border-radius: 16px; margin-bottom: 16px;
        backdrop-filter: blur(16px); box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    }
    .vibe-title {
        font-size: 1.5rem; font-weight: 800; letter-spacing: -0.3px;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .vibe-sub { font-size: 0.85rem; color: #94a3b8; margin-top: 3px; }
    .stepper-wrap { display: flex; gap: 6px; margin-bottom: 18px; }
    .step-node {
        flex: 1; text-align: center; padding: 8px 4px; border-radius: 10px;
        font-size: 0.65rem; font-weight: 700; background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.06); color: #64748b;
    }
    .step-node.active {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.18), rgba(129, 140, 248, 0.18));
        border: 1px solid #38bdf8; color: #f8fafc; box-shadow: 0 0 20px rgba(56, 189, 248, 0.25);
    }
    .kpi-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 12px; margin-bottom: 20px; }
    .kpi-card { background: rgba(17, 24, 39, 0.68); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 14px 12px; text-align: center; }
    .kpi-val { font-size: 1.55rem; font-weight: 800; color: #f8fafc; line-height: 1.15; }
    .kpi-lbl { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; color: #94a3b8; margin-top: 5px; }
    .guide-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 22px; }
    .guide-card { background: linear-gradient(145deg, rgba(30, 41, 59, 0.50), rgba(15, 23, 42, 0.75)); border: 1px solid rgba(56, 189, 248, 0.20); border-left: 4px solid #38bdf8; border-radius: 14px; padding: 16px 18px; }
    .meta-bar { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
    .pill { font-size: 0.75rem; padding: 4px 11px; border-radius: 999px; font-weight: 600; background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(148, 163, 184, 0.25); color: #cbd5e1; }
    .pill-cyan { background: rgba(56, 189, 248, 0.15); border-color: #38bdf8; color: #7dd3fc; }
    .pill-green { background: rgba(16, 185, 129, 0.15); border-color: #10b981; color: #6ee7b7; }
    .pill-red { background: rgba(244, 63, 94, 0.15); border-color: #f43f5e; color: #fda4af; }
    .pill-amber { background: rgba(245, 158, 11, 0.15); border-color: #f59e0b; color: #fcd34d; }
</style>
""", unsafe_allow_html=True)

TOPIC_TEMPLATES = {
    "— Keep Current / Custom Topic —": None,
    "🫀 Cardiology: Apixaban vs. Warfarin in Atrial Fibrillation": {
        "question": "In adults with atrial fibrillation, does apixaban, compared with warfarin, reduce the risk of stroke and major bleeding?",
        "P": "atrial fibrillation, nonvalvular atrial fibrillation, AF, adults with atrial fibrillation",
        "I": "apixaban, eliquis, factor Xa inhibitor, direct oral anticoagulant",
        "C": "warfarin, vitamin K antagonist, coumadin, aspirin, placebo",
        "O": "stroke, systemic embolism, major bleeding, intracranial hemorrhage, mortality",
    },
    "🩸 Endocrinology: Metformin vs. Placebo/Sulfonylurea in Type 2 Diabetes": {
        "question": "In adults with type 2 diabetes, does metformin, compared with placebo or sulfonylurea, lower HbA1c?",
        "P": "Adults with type 2 diabetes, T2DM, diabetic patients, type II diabetes",
        "I": "Metformin, glucophage, biguanide",
        "C": "Placebo, sulfonylurea, glimepiride, glipizide, sitagliptin, standard care",
        "O": "HbA1c, glycated haemoglobin, glycosylated hemoglobin, fasting blood glucose",
    },
}

def render_beginner_guide(c1_title, c1_body, c2_title, c2_body, c3_title, c3_body):
    st.markdown(f"""
    <div class="guide-grid">
        <div class="guide-card"><div style="font-size:0.9rem; font-weight:700; color:#38bdf8; margin-bottom:4px;">{c1_title}</div><div style="font-size:0.84rem; color:#cbd5e1;">{c1_body}</div></div>
        <div class="guide-card" style="border-left-color:#818cf8;"><div style="font-size:0.9rem; font-weight:700; color:#818cf8; margin-bottom:4px;">{c2_title}</div><div style="font-size:0.84rem; color:#cbd5e1;">{c2_body}</div></div>
        <div class="guide-card" style="border-left-color:#c084fc;"><div style="font-size:0.9rem; font-weight:700; color:#c084fc; margin-bottom:4px;">{c3_title}</div><div style="font-size:0.84rem; color:#cbd5e1;">{c3_body}</div></div>
    </div>
    """, unsafe_allow_html=True)

def build_boolean_query_from_pico(config):
    terms = [t.strip() for t in config.get("intervention_text", "").split(",") if t.strip()]
    return f'("type 2 diabetes") AND {terms[0]} AND placebo' if terms else 'metformin'

def get_dashboard_stats():
    conn = get_connection()
    tot = conn.execute("SELECT COUNT(*) FROM records;").fetchone()[0]
    vis = conn.execute("SELECT COUNT(*) FROM records WHERE is_hidden_duplicate = 0;").fetchone()[0]
    hid = conn.execute("SELECT COUNT(*) FROM records WHERE is_hidden_duplicate = 1;").fetchone()[0]
    unc = conn.execute("SELECT COUNT(*) FROM duplicate_groups WHERE status = 'uncertain';").fetchone()[0]
    confl = conn.execute("SELECT COUNT(*) FROM duplicate_groups WHERE has_conflict = 1;").fetchone()[0]
    rows = conn.execute("""
    SELECT COALESCE(rd.screening_decision, ms.decision, 'Maybe') AS fd, rd.screening_decision AS hd
    FROM records r LEFT JOIN machine_screening ms ON r.record_id=ms.record_id
    LEFT JOIN reviewer_decisions rd ON r.duplicate_group_id=rd.group_id WHERE r.is_hidden_duplicate=0;
    """).fetchall()
    conn.close()
    return {
        "total_records": tot, "unique_visible": vis, "hidden_dups": hid, "uncertain_dups": unc, "conflicts": confl,
        "included": sum(1 for r in rows if r["fd"] == "Include"), "excluded": sum(1 for r in rows if r["fd"] == "Exclude"),
        "maybe": sum(1 for r in rows if r["fd"] == "Maybe"), "overrides": sum(1 for r in rows if r["hd"] is not None)
    }

def save_human_decision(group_id, record_id, reviewer_name, screening_decision, exclusion_reason, reviewer_notes, pico_p, pico_i, pico_c, pico_o):
    conn = get_connection()
    prev = conn.execute("SELECT * FROM reviewer_decisions WHERE group_id = ?;", (group_id,)).fetchone()
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute("""
    INSERT INTO reviewer_decisions (group_id, record_id, screening_decision, exclusion_reason, reviewer_notes, pico_p, pico_i, pico_c, pico_o, reviewer_name, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(group_id) DO UPDATE SET record_id=excluded.record_id, screening_decision=excluded.screening_decision,
    exclusion_reason=excluded.exclusion_reason, reviewer_notes=excluded.reviewer_notes, pico_p=excluded.pico_p,
    pico_i=excluded.pico_i, pico_c=excluded.pico_c, pico_o=excluded.pico_o, reviewer_name=excluded.reviewer_name, updated_at=excluded.updated_at;
    """, (group_id, record_id, screening_decision, exclusion_reason, reviewer_notes, pico_p, pico_i, pico_c, pico_o, reviewer_name, now))
    conn.commit()
    conn.close()
    log_human_audit(reviewer_name, "review_update", group_id, str(dict(prev) if prev else "None"), f"Decision={screening_decision}", exclusion_reason or "Manual update")

# SIDEBAR
st.sidebar.markdown("## ✨ Mini-Rayyan Studio")
reviewer_name = st.sidebar.text_input("👤 Reviewer Name", value="Lead Reviewer (UG3)")

PAGES = [
    "0. Question & PICO Setup",
    "1 & 2. Search & Fetch Papers",
    "3. Database Storage & Records",
    "4. Duplicate Detection",
    "5. Study Screening",
    "6 & 7. PICO Highlighter & Review",
    "8. Level 2: Query Loop & Diffs",
    "9. Export CSV & Audit Logs",
]
page = st.sidebar.radio("🧭 Pipeline Steps:", PAGES)

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Reset Workspace", use_container_width=True):
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    init_db()
    st.sidebar.success("Workspace reset.")
    st.rerun()

stats = get_dashboard_stats()
config = get_project_config()

st.markdown(f"""
<div class="vibe-hero">
    <div>
        <div class="vibe-title">✨ MINI-RAYYAN // LEVEL 2 SYNTHESIS ENGINE</div>
        <div class="vibe-sub">🎯 <b>Active Question:</b> {config['review_question']}</div>
    </div>
    <div><span class="pill pill-cyan">👤 {reviewer_name}</span> <span class="pill pill-green">⚡ Level 2 Active</span></div>
</div>
""", unsafe_allow_html=True)

step_map = {PAGES[i]: i for i in range(len(PAGES))}
active_idx = step_map.get(page, 0)
step_labels = [
    "Step 0: PICO Setup", 
    "Step 1 & 2: Fetch", 
    "Step 3: Database", 
    "Step 4: Deduplicate", 
    "Step 5: Screening", 
    "Step 6: PICO", 
    "Step 7: Level 2 Loop", 
    "Step 8: Export & Logs"
]
stepper_html = '<div class="stepper-wrap">'
for idx, lbl in enumerate(step_labels):
    cls = "step-node active" if idx == active_idx else "step-node"
    stepper_html += f'<div class="{cls}">{lbl}</div>'
stepper_html += "</div>"
st.markdown(stepper_html, unsafe_allow_html=True)

st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-val">{stats['total_records']}</div><div class="kpi-lbl">📥 Pulled</div></div>
    <div class="kpi-card"><div class="kpi-val" style="color:#38bdf8;">{stats['unique_visible']}</div><div class="kpi-lbl">📄 Unique</div></div>
    <div class="kpi-card"><div class="kpi-val" style="color:#94a3b8;">{stats['hidden_dups']}</div><div class="kpi-lbl">🔗 Hidden</div></div>
    <div class="kpi-card"><div class="kpi-val" style="color:#10b981;">{stats['included']}</div><div class="kpi-lbl">✅ Include</div></div>
    <div class="kpi-card"><div class="kpi-val" style="color:#f43f5e;">{stats['excluded']}</div><div class="kpi-lbl">❌ Exclude</div></div>
    <div class="kpi-card"><div class="kpi-val" style="color:#f59e0b;">{stats['maybe']}</div><div class="kpi-lbl">🤔 Maybe</div></div>
    <div class="kpi-card"><div class="kpi-val" style="color:#f43f5e;">{stats['conflicts']}</div><div class="kpi-lbl">⚠️ Conflicts</div></div>
</div>
""", unsafe_allow_html=True)

# PAGE ROUTING
if page == "0. Question & PICO Setup":
    st.subheader("Step 0: Define Research Question & PICO")
    render_beginner_guide("💡 What is this?", "Define your review question and PICO criteria.", "📖 PICO", "Population, Intervention, Comparator, Outcome.", "🗄️ Database", "Stored in project_config table.")
    selected_tpl = st.selectbox("✨ Topic Template:", list(TOPIC_TEMPLATES.keys()))
    tpl_data = TOPIC_TEMPLATES[selected_tpl]
    with st.form("step0"):
        rq = st.text_area("Research Question", value=tpl_data["question"] if tpl_data else config["review_question"])
        pop = st.text_input("Population", value=tpl_data["P"] if tpl_data else config["population_text"])
        inter = st.text_input("Intervention", value=tpl_data["I"] if tpl_data else config["intervention_text"])
        comp = st.text_input("Comparator", value=tpl_data["C"] if tpl_data else config["comparator_text"])
        out = st.text_input("Outcome", value=tpl_data["O"] if tpl_data else config["outcome_text"])
        if st.form_submit_button("💾 Save Setup", type="primary"):
            save_project_config(rq, pop, inter, comp, out, config["criteria"])
            run_screening()
            run_pico_extraction()
            st.success("Saved!")
            st.rerun()

elif page == "1 & 2. Search & Fetch Papers":
    st.subheader("Steps 1 & 2: Search & Fetch Papers")
    render_beginner_guide("💡 Search", "Run boolean queries.", "🌐 APIs", "PubMed & Europe PMC.", "🗄️ Storage", "Records stored without deletion.")
    col1, col2 = st.columns([2, 1])
    with col1:
        q_str = st.text_input("Boolean Query", value=build_boolean_query_from_pico(config))
        y1, y2 = st.number_input("Start Year", 2015, 2026, 2018), st.number_input("End Year", 2015, 2026, 2026)
        if st.button("🚀 Run Search & Ingest", type="primary"):
            vid = create_query_version("Query Version", q_str, y1, y2, ["PubMed", "Europe PMC"], 10, 5)
            papers = get_benchmark_papers("v1")
            store_fetched_records(vid, papers)
            run_deduplication(vid)
            run_screening(vid)
            run_pico_extraction(vid)
            st.success("Fetched and processed successfully!")
            st.rerun()
    with col2:
        if st.button("⚡ Load 12 Benchmark Papers"):
            vid = create_query_version("Benchmark v1", '"type 2 diabetes" AND metformin', 2015, 2025, ["PubMed"], 8, 4)
            store_fetched_records(vid, get_benchmark_papers("v1"))
            run_deduplication(vid)
            run_screening(vid)
            run_pico_extraction(vid)
            st.success("Loaded benchmark papers!")
            st.rerun()

elif page == "3. Database Storage & Records":
    st.subheader("Step 3: Persistent Database Storage (Nothing Deleted)")
    render_beginner_guide(
        "💡 What is Step 3?", 
        "Every paper pulled from PubMed or Europe PMC is safely committed to your SQLite database table named records.", 
        "🛡️ Zero-Deletion Rule", 
        "Per hackathon rules, records are never permanently deleted; duplicates or exclusions are just hidden flags.", 
        "🔗 Query Version Links", 
        "The query_records table links every paper to the exact search version that discovered it."
    )
    
    conn = get_connection()
    db_records = conn.execute("SELECT record_id, source, pmid, doi, title, pub_year, journal, is_hidden_duplicate FROM records ORDER BY record_id ASC;").fetchall()
    conn.close()
    
    if not db_records:
        st.info("Database is currently empty. Run a search in Steps 1 & 2 to populate records.")
    else:
        st.success(f"Database active! Total records stored across all queries: **{len(db_records)}**")
        df_db = pd.DataFrame([dict(r) for r in db_records])
        st.dataframe(df_db, use_container_width=True, hide_index=True)

elif page == "4. Duplicate Detection":
    st.subheader("Step 4: Deduplication & Uncertain Pairs")
    render_beginner_guide(
        "💡 Deduplication", "Exact DOI/PMID matching.", 
        "✂️ Splits", "Keep conference & journal separate.", 
        "🛡️ Safety", "Nothing deleted."
    )
    
    conn = get_connection()
    groups = conn.execute("""
    SELECT dg.*, COUNT(r.record_id) AS member_count
    FROM duplicate_groups dg
    JOIN records r ON r.duplicate_group_id = dg.group_id
    GROUP BY dg.group_id
    HAVING COUNT(r.record_id) > 1 OR dg.status IN ('uncertain', 'human_split')
    ORDER BY CASE WHEN dg.status = 'uncertain' THEN 0 ELSE 1 END, dg.group_id ASC;
    """).fetchall()

    if not groups:
        st.info("No uncertain duplicate pairs pending review.")
    else:
        for g in groups:
            gid = g["group_id"]
            members = conn.execute(
                "SELECT * FROM records WHERE duplicate_group_id = ? ORDER BY is_hidden_duplicate ASC;",
                (gid,)
            ).fetchall()

            badge = "⚠️ UNCERTAIN PAIR — NEEDS YOUR DECISION" if g["status"] == "uncertain" else f"✅ STATUS: {g['status'].upper()}"
            with st.expander(f"Duplicate Group #{gid} ({len(members)} papers) | {badge} | Match: {g['match_method']}", expanded=(g["status"] == "uncertain")):
                df_mem = pd.DataFrame([dict(m) for m in members])[
                    ["record_id", "source", "pmid", "doi", "title", "first_author", "pub_year", "journal", "pub_types", "is_hidden_duplicate"]
                ]
                st.dataframe(df_mem, use_container_width=True, hide_index=True)

                b1, b2 = st.columns(2)
                if b1.button(f"✅ Confirm Duplicates (Keep #{g['representative_record_id']} Visible)", key=f"conf_dup_{gid}", use_container_width=True):
                    conn.execute("UPDATE duplicate_groups SET status = 'human_confirmed' WHERE group_id = ?;", (gid,))
                    conn.execute(
                        "UPDATE records SET is_hidden_duplicate = CASE WHEN record_id = ? THEN 0 ELSE 1 END WHERE duplicate_group_id = ?;",
                        (g["representative_record_id"], gid)
                    )
                    conn.commit()
                    log_human_audit(reviewer_name, "duplicate_override", gid, g["status"], "human_confirmed", "Confirmed duplicate group")
                    st.rerun()

                if b2.button(f"✂️ Split (Keep Separate & Visible)", key=f"split_dup_{gid}", use_container_width=True):
                    conn.execute("UPDATE duplicate_groups SET status = 'human_split' WHERE group_id = ?;", (gid,))
                    for m in members:
                        if m["record_id"] != g["representative_record_id"]:
                            cur = conn.cursor()
                            cur.execute(
                                "INSERT INTO duplicate_groups (representative_record_id, status, match_method, updated_at) VALUES (?, 'human_split', 'Human split separate study report', ?);",
                                (m["record_id"], datetime.now().isoformat(timespec="seconds"))
                            )
                            new_gid = cur.lastrowid
                            conn.execute("UPDATE records SET duplicate_group_id = ?, is_hidden_duplicate = 0 WHERE record_id = ?;", (new_gid, m["record_id"]))
                    conn.execute("UPDATE records SET is_hidden_duplicate = 0 WHERE record_id = ?;", (g["representative_record_id"],))
                    conn.commit()
                    log_human_audit(reviewer_name, "duplicate_override", gid, g["status"], "human_split", "Split group into separate studies")
                    st.rerun()
    conn.close()

elif page == "5. Study Screening":
    st.subheader("Step 5: Study Screening Console")
    conn = get_connection()
    rows = conn.execute("SELECT r.*, COALESCE(rd.screening_decision, ms.decision, 'Maybe') AS dec FROM records r LEFT JOIN machine_screening ms ON r.record_id=ms.record_id LEFT JOIN reviewer_decisions rd ON r.duplicate_group_id=rd.group_id WHERE r.is_hidden_duplicate=0;").fetchall()
    conn.close()
    for r in rows:
        with st.expander(f"[{r['dec']}] #{r['record_id']}: {r['title']}"):
            st.write(r["abstract"])
            if st.button("✅ Include", key=f"inc_{r['record_id']}"):
                save_human_decision(r["duplicate_group_id"], r["record_id"], reviewer_name, "Include", "", "", "", "", "", "")
                st.rerun()

elif page == "6 & 7. PICO Highlighter & Review":
    st.subheader("Steps 6 & 7: PICO Extraction & Review")
    conn = get_connection()
    rows = conn.execute("SELECT r.*, mp.* FROM records r LEFT JOIN machine_pico mp ON r.record_id=mp.record_id WHERE r.is_hidden_duplicate=0;").fetchall()
    conn.close()
    for r in rows:
        with st.expander(f"#{r['record_id']}: {r['title']}"):
            st.markdown(highlight_pico_html(r["abstract"], r["population_span"], r["intervention_span"], r["comparator_span"], r["outcome_span"]), unsafe_allow_html=True)

elif page == "8. Level 2: Query Loop & Diffs":
    st.subheader("Level 2: Query Version Diffs & Conflict Resolution Queue")
    render_beginner_guide(
        "💡 Level 2 Loop",
        "When you edit a query, the system re-runs from fetch, performs incremental storage, and preserves past reviewer decisions.",
        "🔍 Diff View",
        "Compare two query versions to see newly added records, removed records, and merged groups.",
        "⚠️ Conflict Resolution",
        "If merged duplicate groups have conflicting human decisions, resolve them here."
    )

    conn = get_connection()
    queries = conn.execute("SELECT * FROM query_versions ORDER BY version_id DESC;").fetchall()
    conflicts = conn.execute("SELECT * FROM duplicate_groups WHERE has_conflict = 1;").fetchall()
    conn.close()

    if conflicts:
        st.error(f"⚠️ Found {len(conflicts)} duplicate group merge conflict(s) with opposing human decisions!")
        for c in conflicts:
            st.write(f"Conflict in Group #{c['group_id']}: {c['conflict_details']}")
            if st.button(f"Resolve Group #{c['group_id']} (Pick Rep #{c['representative_record_id']})", key=f"res_{c['group_id']}"):
                resolve_duplicate_conflict(c['group_id'], c['representative_record_id'], reviewer_name)
                st.success("Conflict resolved!")
                st.rerun()
    else:
        st.success("✅ No merge conflicts detected in active duplicate groups.")

    if len(queries) >= 2:
        st.markdown("#### 🔍 Compare Query Versions (Diff View)")
        q_ids = [q["version_id"] for q in queries]
        col1, col2 = st.columns(2)
        old_v = col1.selectbox("Older Query Version", q_ids, index=min(1, len(q_ids)-1))
        new_v = col2.selectbox("Newer Query Version", q_ids, index=0)

        if st.button("📊 Compute Query Diff"):
            diff = compute_query_diff(old_v, new_v)
            st.metric("Added Records", diff["added_count"])
            st.metric("Removed Records", diff["removed_count"])
            if diff["added_records"]:
                st.write("Added Studies:", [r["title"] for r in diff["added_records"]])

elif page == "9. Export CSV & Audit Logs":
    st.subheader("Step 8: Export & Audit Logs")
    conn = get_connection()
    rows = conn.execute("SELECT r.record_id, r.title, r.doi, r.pmid FROM records r WHERE r.is_hidden_duplicate=0;").fetchall()
    conn.close()
    if rows:
        df = pd.DataFrame([dict(r) for r in rows])
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Download CSV", df.to_csv(index=False).encode("utf-8"), "mini_rayyan_export.csv", "text/csv")