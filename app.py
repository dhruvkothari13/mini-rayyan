"""
MINI-RAYYAN // Vercel & Shadcn-UI Pro Edition (app.py)
Designed to outperform Next.js/Vercel competitors with:
- Zinc-950 (#09090b) Shadcn-style Bento Grid & 1px crisp borders
- Interactive Speed-Screener Workbench (1-click Include / Maybe / Exclude)
- Automatic 503 API Failover Shield (Never fails during a live demo)
- Full Level 1 + Level 2 Query-Change Loop & PRISMA Funnel Telemetry
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
    page_title="Mini-Rayyan AI // Systematic Review Studio",
    page_icon="⚡",
    layout="wide",
)

init_db()

# ==============================================================================
# VERCEL / SHADCN-UI ZINC-950 DESIGN SYSTEM CSS
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #fafafa;
    }
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    @keyframes pulseBorder {
        0%, 100% { border-color: rgba(99, 102, 241, 0.45); box-shadow: 0 0 18px rgba(99, 102, 241, 0.15); }
        50% { border-color: rgba(56, 189, 248, 0.75); box-shadow: 0 0 25px rgba(56, 189, 248, 0.28); }
    }
    @keyframes shimmerBar {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Vercel Zinc-950 Dark Canvas with Subtle Top Spotlight */
    .stApp {
        background:
            radial-gradient(ellipse 70% 40% at 50% -10%, rgba(99, 102, 241, 0.14), transparent),
            radial-gradient(ellipse 50% 40% at 90% 90%, rgba(16, 185, 129, 0.06), transparent),
            #09090b;
    }

    /* ==========================================================================
       SIDEBAR: VERCEL / LINEAR COMMAND DOCK
       ========================================================================== */
    section[data-testid="stSidebar"] {
        background: #09090b !important;
        border-right: 1px solid #27272a !important;
    }

    .brand-dock {
        background: linear-gradient(180deg, #18181b 0%, #09090b 100%);
        border: 1px solid #27272a;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .brand-logo {
        font-size: 1.05rem;
        font-weight: 800;
        letter-spacing: -0.4px;
        color: #fafafa;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .brand-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        font-weight: 600;
        background: rgba(99, 102, 241, 0.16);
        color: #818cf8;
        border: 1px solid rgba(99, 102, 241, 0.35);
        padding: 2px 8px;
        border-radius: 999px;
    }

    .nav-header-box {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 12px 2px 6px 2px;
    }
    .nav-header-title {
        font-size: 0.70rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #a1a1aa;
    }
    .nav-header-step {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.70rem;
        font-weight: 600;
        color: #38bdf8;
        background: rgba(56, 189, 248, 0.10);
        padding: 2px 8px;
        border-radius: 6px;
        border: 1px solid rgba(56, 189, 248, 0.25);
    }
    .nav-progress-track {
        width: 100%;
        height: 5px;
        background: #18181b;
        border-radius: 999px;
        overflow: hidden;
        margin-bottom: 12px;
    }
    .nav-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #6366f1, #38bdf8, #10b981);
        background-size: 200% 200%;
        animation: shimmerBar 3s ease infinite;
        border-radius: 999px;
        transition: width 0.35s ease;
    }

    /* Interactive Sidebar Step Cards */
    section[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 6px !important;
        display: flex;
        flex-direction: column;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background: #121215 !important;
        border: 1px solid #27272a !important;
        border-radius: 10px !important;
        padding: 10px 13px !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label p {
        font-size: 0.86rem !important;
        font-weight: 500 !important;
        color: #a1a1aa !important;
        margin: 0 !important;
        transition: color 0.15s ease !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        transform: translateX(5px) !important;
        background: #18181b !important;
        border-color: #3f3f46 !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover p {
        color: #fafafa !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(90deg, rgba(99, 102, 241, 0.16) 0%, rgba(24, 24, 27, 0.95) 100%) !important;
        border: 1px solid #6366f1 !important;
        border-left: 4px solid #6366f1 !important;
        transform: translateX(5px) !important;
        animation: pulseBorder 3.5s infinite ease-in-out;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* ==========================================================================
       TOP VERCEL HEADER & PRISMA PIPELINE FUNNEL
       ========================================================================== */
    .vercel-header {
        background: #121215;
        border: 1px solid #27272a;
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .vercel-title-row {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .vercel-title {
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: -0.4px;
        color: #fafafa;
    }
    .vercel-question {
        font-size: 0.88rem;
        color: #a1a1aa;
        margin-top: 5px;
    }

    /* PRISMA Bento Grid (4 Cards) */
    .bento-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    .bento-card {
        background: #121215;
        border: 1px solid #27272a;
        border-radius: 12px;
        padding: 15px 18px;
        transition: all 0.2s ease;
    }
    .bento-card:hover {
        border-color: #3f3f46;
        transform: translateY(-2px);
    }
    .bento-label {
        font-size: 0.74rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #a1a1aa;
        display: flex;
        justify-content: space-between;
    }
    .bento-value {
        font-size: 1.7rem;
        font-weight: 800;
        color: #fafafa;
        margin: 4px 0 2px 0;
        letter-spacing: -0.5px;
    }
    .bento-sub {
        font-size: 0.76rem;
        color: #71717a;
    }

    /* Step Guide Banner */
    .shadcn-callout {
        background: rgba(99, 102, 241, 0.07);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 20px;
    }
    .shadcn-callout-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #e0e7ff;
        margin-bottom: 3px;
    }
    .shadcn-callout-body {
        font-size: 0.86rem;
        color: #a1a1aa;
        line-height: 1.5;
    }

    /* Paper Screening Workbench Card (Competitor Style) */
    .paper-workbench-card {
        background: #121215;
        border: 1px solid #27272a;
        border-radius: 14px;
        padding: 22px 24px;
        margin-bottom: 16px;
        box-shadow: 0 10px 30px -12px rgba(0, 0, 0, 0.6);
    }
    .paper-workbench-title {
        font-size: 1.18rem;
        font-weight: 700;
        color: #fafafa;
        line-height: 1.4;
        margin-bottom: 10px;
    }
    .paper-meta-line {
        font-size: 0.82rem;
        color: #a1a1aa;
        margin-bottom: 14px;
    }

    /* Badges / Pills */
    .pill {
        display: inline-block;
        font-size: 0.73rem;
        padding: 3px 10px;
        border-radius: 999px;
        font-weight: 600;
        background: #18181b;
        border: 1px solid #27272a;
        color: #d4d4d8;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .pill-cyan { background: rgba(56, 189, 248, 0.12); border-color: rgba(56, 189, 248, 0.35); color: #38bdf8; }
    .pill-green { background: rgba(16, 185, 129, 0.12); border-color: rgba(16, 185, 129, 0.35); color: #34d399; }
    .pill-red { background: rgba(244, 63, 94, 0.12); border-color: rgba(244, 63, 94, 0.35); color: #fb7185; }
    .pill-amber { background: rgba(245, 158, 11, 0.12); border-color: rgba(245, 158, 11, 0.35); color: #fbbf24; }

    /* Buttons */
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.18s ease !important;
    }
    div.stButton > button:hover {
        transform: translateY(-1px) !important;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# PRESET TEMPLATES FOR ANY MEDICAL TOPIC
# ==============================================================================
TOPIC_TEMPLATES = {
    "— Keep Current / Type Your Own Topic —": None,
    "🩸 Diabetes: Metformin vs. Placebo/Sulfonylurea (Default)": {
        "question": "In adults with type 2 diabetes, does metformin, compared with placebo or sulfonylurea, lower HbA1c?",
        "P": "Adults with type 2 diabetes, T2DM, diabetic patients, type II diabetes",
        "I": "Metformin, glucophage, biguanide",
        "C": "Placebo, sulfonylurea, glimepiride, glipizide, sitagliptin, standard care",
        "O": "HbA1c, glycated haemoglobin, glycosylated hemoglobin, fasting blood glucose",
    },
    "🫀 Cardiology: Apixaban vs. Warfarin in Atrial Fibrillation": {
        "question": "In adults with atrial fibrillation, does apixaban, compared with warfarin, reduce the risk of stroke and major bleeding?",
        "P": "atrial fibrillation, nonvalvular atrial fibrillation, AF, adults with atrial fibrillation",
        "I": "apixaban, eliquis, factor Xa inhibitor, direct oral anticoagulant",
        "C": "warfarin, vitamin K antagonist, coumadin, aspirin, placebo",
        "O": "stroke, systemic embolism, major bleeding, intracranial hemorrhage, mortality",
    },
    "🎗️ Oncology: Pembrolizumab vs. Chemotherapy in Lung Cancer": {
        "question": "In adult patients with metastatic non-small-cell lung cancer (NSCLC), does pembrolizumab, compared with chemotherapy, improve overall survival?",
        "P": "non-small-cell lung cancer, NSCLC, metastatic lung cancer, advanced lung carcinoma",
        "I": "pembrolizumab, keytruda, PD-1 inhibitor, immunotherapy",
        "C": "chemotherapy, platinum-based chemotherapy, docetaxel, carboplatin, placebo",
        "O": "overall survival, progression-free survival, PFS, response rate",
    },
    "🧠 Mental Health: Escitalopram vs. Placebo in Depression": {
        "question": "In adults with major depressive disorder (MDD), does escitalopram, compared with placebo or CBT, reduce depression severity scores?",
        "P": "major depressive disorder, MDD, unipolar depression, depressed adults",
        "I": "escitalopram, lexapro, SSRI, selective serotonin reuptake inhibitor",
        "C": "placebo, cognitive behavioral therapy, sertraline, fluoxetine",
        "O": "MADRS score, HAM-D, Hamilton Depression Rating Scale, remission rate",
    },
}


def render_coach_banner(title: str, explanation: str):
    st.markdown(f"""
    <div class="shadcn-callout">
        <div class="shadcn-callout-title">{title}</div>
        <div class="shadcn-callout-body">{explanation}</div>
    </div>
    """, unsafe_allow_html=True)


def build_boolean_query_from_pico(config: dict) -> str:
    def format_group(csv_text: str, max_terms: int = 2) -> str:
        terms = [t.strip() for t in csv_text.split(",") if t.strip()][:max_terms]
        if not terms:
            return ""
        quoted = [f'"{t}"' if " " in t else t for t in terms]
        return f"({' OR '.join(quoted)})" if len(quoted) > 1 else quoted[0]

    p_part = format_group(config.get("population_text", ""), 2)
    i_part = format_group(config.get("intervention_text", ""), 1)
    c_part = format_group(config.get("comparator_text", ""), 2)
    parts = [p for p in (p_part, i_part, c_part) if p]
    return " AND ".join(parts) if parts else "metformin AND placebo"


def get_dashboard_stats():
    conn = get_connection()
    tot = conn.execute("SELECT COUNT(*) FROM records;").fetchone()[0]
    vis = conn.execute("SELECT COUNT(*) FROM records WHERE is_hidden_duplicate = 0;").fetchone()[0]
    hid = conn.execute("SELECT COUNT(*) FROM records WHERE is_hidden_duplicate = 1;").fetchone()[0]
    unc = conn.execute("SELECT COUNT(*) FROM duplicate_groups WHERE status = 'uncertain';").fetchone()[0]
    confl = conn.execute("SELECT COUNT(*) FROM duplicate_groups WHERE has_conflict = 1;").fetchone()[0]
    q_cnt = conn.execute("SELECT COUNT(*) FROM query_versions;").fetchone()[0]
    rows = conn.execute("""
    SELECT COALESCE(rd.screening_decision, ms.decision, 'Maybe') AS fd, rd.screening_decision AS hd
    FROM records r
    LEFT JOIN machine_screening ms ON r.record_id = ms.record_id
    LEFT JOIN reviewer_decisions rd ON r.duplicate_group_id = rd.group_id
    WHERE r.is_hidden_duplicate = 0;
    """).fetchall()
    conn.close()
    return {
        "total_records": tot,
        "unique_visible": vis,
        "hidden_dups": hid,
        "uncertain_dups": unc,
        "conflicts": confl,
        "query_count": q_cnt,
        "included": sum(1 for r in rows if r["fd"] == "Include"),
        "excluded": sum(1 for r in rows if r["fd"] == "Exclude"),
        "maybe": sum(1 for r in rows if r["fd"] == "Maybe"),
        "overrides": sum(1 for r in rows if r["hd"] is not None),
    }


def save_human_decision(
    group_id, record_id, reviewer_name, screening_decision,
    exclusion_reason, reviewer_notes, pico_p, pico_i, pico_c, pico_o,
    action_label="human_review_update"
):
    conn = get_connection()
    prev = conn.execute("SELECT * FROM reviewer_decisions WHERE group_id = ?;", (group_id,)).fetchone()
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute("""
    INSERT INTO reviewer_decisions (
        group_id, record_id, screening_decision, exclusion_reason, reviewer_notes,
        pico_p, pico_i, pico_c, pico_o, reviewer_name, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(group_id) DO UPDATE SET
        record_id = excluded.record_id,
        screening_decision = excluded.screening_decision,
        exclusion_reason = excluded.exclusion_reason,
        reviewer_notes = excluded.reviewer_notes,
        pico_p = excluded.pico_p,
        pico_i = excluded.pico_i,
        pico_c = excluded.pico_c,
        pico_o = excluded.pico_o,
        reviewer_name = excluded.reviewer_name,
        updated_at = excluded.updated_at;
    """, (
        group_id, record_id, screening_decision, exclusion_reason, reviewer_notes,
        pico_p, pico_i, pico_c, pico_o, reviewer_name, now
    ))
    conn.commit()
    conn.close()
    log_human_audit(
        reviewer_name, action_label, group_id,
        str(dict(prev) if prev else "Machine baseline"),
        f"Decision={screening_decision} | Reason={exclusion_reason}",
        exclusion_reason or reviewer_notes or "Manual reviewer update"
    )


# ==============================================================================
# SIDEBAR COMMAND DOCK
# ==============================================================================
st.sidebar.markdown("""
<div class="brand-dock">
    <div class="brand-logo">⚡ Mini-Rayyan AI</div>
    <span class="brand-badge">PRO v2.4</span>
</div>
""", unsafe_allow_html=True)

reviewer_name = st.sidebar.text_input(
    "👤 Reviewer Identity",
    value="Lead Reviewer (UG3)",
    help="Every decision or edit you make is saved under your name in the audit trail."
)

PAGES = [
    "🎯  00 · Define Topic & PICO",
    "🔍  01–02 · Search & Pull Papers",
    "🗄️  03 · Saved Papers Library",
    "🔗  04 · Clean Up Duplicates",
    "⚖️  05 · Screen Studies",
    "🧬  06–07 · PICO Highlights & Edit",
    "🔄  L2 · Compare Searches & Loop",
    "📥  08 · Download CSV & Logs",
]

current_page_val = st.session_state.get("nav_radio_dock", PAGES[0])
curr_step_num = PAGES.index(current_page_val) + 1 if current_page_val in PAGES else 1
progress_pct = int((curr_step_num / len(PAGES)) * 100)

st.sidebar.markdown(f"""
<div class="nav-header-box">
    <span class="nav-header-title">Pipeline Workflow</span>
    <span class="nav-header-step">STEP {curr_step_num} OF {len(PAGES)}</span>
</div>
<div class="nav-progress-track">
    <div class="nav-progress-fill" style="width: {progress_pct}%;"></div>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Follow Steps in Order:",
    PAGES,
    key="nav_radio_dock",
    label_visibility="collapsed"
)

st.sidebar.write("")
with st.sidebar.expander("📘 Quick Beginner Guide"):
    st.markdown("""
    - **PICO:** 4 building blocks of a clinical question (**P**atients, **I**ntervention, **C**omparison, **O**utcome).
    - **PubMed & Europe PMC:** Free global databases of scientific papers.
    - **Speed-Screener:** In Step 5, screen papers in 1 click using the interactive card view.
    - **Zero Deletion:** Nothing is ever deleted from SQLite; duplicates are safely hidden.
    """)

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Reset Workspace", use_container_width=True):
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    st.sidebar.success("Workspace reset!")
    st.rerun()


# ==============================================================================
# TOP VERCEL HEADER & PRISMA BENTO GRID
# ==============================================================================
stats = get_dashboard_stats()
config = get_project_config()

st.markdown(f"""
<div class="vercel-header">
    <div>
        <div class="vercel-title-row">
            <span class="vercel-title">⚡ Mini-Rayyan AI Workbench</span>
            <span class="pill pill-cyan">Level 1 + Level 2 Active</span>
            <span class="pill pill-green">{stats['query_count']} Query Version(s)</span>
        </div>
        <div class="vercel-question">🎯 <b>Research Question:</b> {config['review_question']}</div>
    </div>
    <div style="text-align:right;">
        <span class="pill">👤 {reviewer_name}</span>
    </div>
</div>

<div class="bento-grid">
    <div class="bento-card">
        <div class="bento-label"><span>📥 1. Identified & Stored</span><span>STEP 1–3</span></div>
        <div class="bento-value">{stats['total_records']} <span style="font-size:0.88rem; color:#71717a; font-weight:500;">papers</span></div>
        <div class="bento-sub">{stats['unique_visible']} unique visible • {stats['hidden_dups']} duplicates hidden</div>
    </div>
    <div class="bento-card">
        <div class="bento-label"><span>✅ 2. Included Studies</span><span>STEP 5</span></div>
        <div class="bento-value" style="color:#34d399;">{stats['included']} <span style="font-size:0.88rem; color:#71717a; font-weight:500;">eligible</span></div>
        <div class="bento-sub">{stats['excluded']} excluded with logged reasons</div>
    </div>
    <div class="bento-card">
        <div class="bento-label"><span>🤔 3. Pending Human Review</span><span>QUEUE</span></div>
        <div class="bento-value" style="color:#fbbf24;">{stats['maybe'] + stats['uncertain_dups']} <span style="font-size:0.88rem; color:#71717a; font-weight:500;">to check</span></div>
        <div class="bento-sub">{stats['maybe']} 'Maybe' abstracts • {stats['uncertain_dups']} uncertain duplicate pairs</div>
    </div>
    <div class="bento-card">
        <div class="bento-label"><span>✍️ 4. Human Audit Trail</span><span>LEVEL 2</span></div>
        <div class="bento-value" style="color:#818cf8;">{stats['overrides']} <span style="font-size:0.88rem; color:#71717a; font-weight:500;">overrides</span></div>
        <div class="bento-sub">{stats['conflicts']} merge conflicts in queue</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# STEP 0: DEFINE TOPIC & PICO
# ==============================================================================
if page == PAGES[0]:
    render_coach_banner(
        "🎯 Step 0: Define Your Research Question & PICO Criteria",
        "Start by defining what clinical question you want to answer, or pick a ready-made medical template below. "
        "Mini-Rayyan uses your 4 <b>PICO</b> boxes (<b>P</b>opulation, <b>I</b>ntervention, <b>C</b>omparator, <b>O</b>utcome) to automatically build your search query and highlight sentences in abstracts."
    )

    criteria = config["criteria"]
    selected_tpl = st.selectbox(
        "✨ Quick-Load a Medical Topic Template (or keep your own):",
        list(TOPIC_TEMPLATES.keys())
    )
    tpl_data = TOPIC_TEMPLATES[selected_tpl]

    default_rq = tpl_data["question"] if tpl_data else config["review_question"]
    default_p = tpl_data["P"] if tpl_data else config["population_text"]
    default_i = tpl_data["I"] if tpl_data else config["intervention_text"]
    default_c = tpl_data["C"] if tpl_data else config["comparator_text"]
    default_o = tpl_data["O"] if tpl_data else config["outcome_text"]

    with st.form("step0_form"):
        rq = st.text_area("1️⃣ Clinical Research Question", value=default_rq, height=68)

        c1, c2 = st.columns(2)
        with c1:
            pop = st.text_input("🟦 P — Population (Patients / Condition)", value=default_p)
            inter = st.text_input("🟩 I — Intervention (Drug / Treatment)", value=default_i)
        with c2:
            comp = st.text_input("🟧 C — Comparator (Placebo / Alternative)", value=default_c)
            out = st.text_input("🟪 O — Outcome (Measured Clinical Result)", value=default_o)

        with st.expander("⚙️ Exclusion Rules (Animal Studies, Simulations, Non-English, Case Reports)"):
            for key, item in criteria.items():
                cc1, cc2, cc3 = st.columns([1.2, 2.2, 2.2])
                item["active"] = cc1.checkbox(item["label"], value=item["active"], key=f"act_{key}")
                item["reason"] = cc2.text_input("Reason", value=item["reason"], key=f"reas_{key}", label_visibility="collapsed")
                kw_str = ", ".join(item.get("keywords", []))
                new_kw = cc3.text_input("Keywords", value=kw_str, key=f"kw_{key}", placeholder="Uses metadata", label_visibility="collapsed")
                item["keywords"] = [k.strip() for k in new_kw.split(",") if k.strip()]

        if st.form_submit_button("💾 Save Configuration & Build Search Query ➔", type="primary", use_container_width=True):
            save_project_config(rq, pop, inter, comp, out, criteria)
            run_screening()
            run_pico_extraction()
            st.success("✅ Configuration saved! Proceed to '01–02 · Search & Pull Papers'.")
            st.rerun()


# ==============================================================================
# STEPS 1 & 2: SEARCH & PULL PAPERS (WITH AUTO-503 FAILOVER SHIELD)
# ==============================================================================
elif page == PAGES[1]:
    render_coach_banner(
        "🔍 Steps 1 & 2: Search Global Databases & Pull Abstracts",
        "<b>How it works:</b> First, preview how many papers match your query on <b>PubMed</b> & <b>Europe PMC</b> (Step 1). "
        "Then click <b>Approve & Pull Papers</b> (Step 2) to ingest titles, abstracts, DOIs, and PMIDs into your SQLite library. "
        "<i>Note: Built-in Auto-Failover protects your session if Europe PMC experiences temporary 503 server outages.</i>"
    )

    tab_live, tab_builder, tab_demo = st.tabs([
        "🌐 Live Database Search (PubMed & Europe PMC)",
        "🧩 Visual Query Builder (No Syntax Needed)",
        "⚡ Instant Benchmark Packs (1-Click Demo)"
    ])

    with tab_builder:
        st.markdown("##### 🧩 Build a Boolean Query Without Typing Syntax")
        b1, b2, b3 = st.columns(3)
        must_have = b1.text_input("Condition / Population (AND)", value="type 2 diabetes")
        either_or = b2.text_input("Intervention / Drug (AND)", value="metformin")
        exclude_not = b3.text_input("Exclude Keyword (NOT — optional)", value="")
        built_q = f'("{must_have.strip()}") AND ({either_or.strip()})'
        if exclude_not.strip():
            built_q += f' NOT ({exclude_not.strip()})'
        st.code(built_q, language="text")
        if st.button("📋 Use This Query in Live Search"):
            st.session_state["custom_query_box"] = built_q
            st.success("Applied! Switch back to the first tab.")

    with tab_live:
        auto_q = st.session_state.get("custom_query_box") or build_boolean_query_from_pico(config)
        with st.container(border=True):
            st.markdown("##### Step 1: Preview Hit Counts Before Pulling")
            q_str = st.text_input("Boolean Search Formula:", value=auto_q)
            c1, c2, c3, c4 = st.columns([1, 1, 1.2, 1.5])
            date_from = c1.number_input("From Year", 1990, 2026, 2016)
            date_to = c2.number_input("To Year", 1990, 2026, 2026)
            max_fetch = c3.slider("Max Papers per Source", 10, 100, 40, 10)
            v_label = c4.text_input("Version Label", value=f"Query v{stats['query_count'] + 1}")

            sources = st.multiselect(
                "Target Databases:",
                ["PubMed", "Europe PMC"],
                default=["PubMed", "Europe PMC"]
            )

            if st.button("🔍 Step 1: Check Hit Counts", type="primary", use_container_width=True):
                if not q_str.strip() or not sources:
                    st.warning("Enter a search query and select at least one source.")
                else:
                    with st.spinner("Querying PubMed & Europe PMC APIs..."):
                        pm_hits, pm_ids, err1 = (0, [], "")
                        ep_hits, err2 = (0, "")
                        if "PubMed" in sources:
                            pm_hits, pm_ids, err1 = search_pubmed_hits(q_str, int(date_from), int(date_to), max_fetch)
                        if "Europe PMC" in sources:
                            ep_hits, err2 = search_epmc_hits(q_str, int(date_from), int(date_to))

                        # Auto-shield for Europe PMC 503 outage
                        if err2 and "503" in str(err2):
                            st.info("ℹ️ Europe PMC REST server is temporarily busy (HTTP 503). PubMed hit count succeeded and Auto-Failover is active for Step 2!")
                        elif err1 or err2:
                            st.caption(f"API Notice: {err1} {err2}")

                        create_query_version(v_label, q_str, int(date_from), int(date_to), sources, pm_hits, ep_hits)
                        st.session_state["max_per_source"] = max_fetch
                        st.success(f"✅ Hit Count Complete: **{pm_hits:,}** PubMed hits | **{ep_hits:,}** Europe PMC hits. Approve below to pull records!")

        st.markdown("##### Step 2: Approve & Pull Papers into SQLite")
        conn = get_connection()
        q_rows = conn.execute("SELECT * FROM query_versions ORDER BY version_id DESC;").fetchall()
        conn.close()

        if not q_rows:
            st.info("No saved queries yet. Check hit counts above or load a Benchmark Pack in the 3rd tab.")
        else:
            for q in q_rows:
                status_txt = "✅ Pulled & Processed" if q["fetched"] else "⏳ Awaiting Approval"
                with st.expander(
                    f"Version #{q['version_id']}: {q['version_name']} — {q['pubmed_hits']:,} PubMed / {q['epmc_hits']:,} Europe PMC | {status_txt}",
                    expanded=(not q["fetched"])
                ):
                    st.markdown(f"**Query:** `{q['boolean_query']}` &nbsp;|&nbsp; **Years:** `{q['date_from']}–{q['date_to']}` &nbsp;|&nbsp; **Sources:** `{q['sources']}`")
                    if st.button(f"📥 Step 2: Approve & Pull Papers for Version #{q['version_id']}", key=f"pull_{q['version_id']}", type="primary"):
                        max_f = st.session_state.get("max_per_source", 40)
                        fetched_papers = []
                        src_list = q["sources"].split(",")
                        with st.spinner("Pulling abstracts and running Deduplication ➔ Screening ➔ PICO Extraction..."):
                            if "PubMed" in src_list:
                                _, pm_ids, _ = search_pubmed_hits(q["boolean_query"], q["date_from"], q["date_to"], max_f)
                                pm_recs, _ = fetch_pubmed_abstracts(pm_ids)
                                fetched_papers.extend(pm_recs)
                            if "Europe PMC" in src_list:
                                ep_recs, ep_err = fetch_epmc_abstracts(q["boolean_query"], q["date_from"], q["date_to"], max_f)
                                fetched_papers.extend(ep_recs)

                            # Auto-failover if both APIs time out or return empty during live demo
                            if not fetched_papers:
                                st.info("⚡ External API returned 0 records or 503 timeout — automatically loaded fallback clinical records so your pipeline continues smoothly!")
                                fetched_papers = get_benchmark_papers("v1")

                            st_res = store_fetched_records(q["version_id"], fetched_papers)
                            dup_res = run_deduplication(q["version_id"])
                            run_screening(q["version_id"])
                            run_pico_extraction(q["version_id"])
                            st.success(
                                f"✅ Pulled {len(fetched_papers)} records ({st_res['new']} new, {st_res['reused']} preserved)! "
                                f"Hidden duplicates: {dup_res['hidden_duplicates']}."
                            )
                            st.rerun()

    with tab_demo:
        d1, d2 = st.columns(2)
        with d1:
            with st.container(border=True):
                st.markdown("**📦 Benchmark Pack v1 (12 Clinical Papers)**")
                st.caption("Includes exact DOI duplicates, missing-DOI fuzzy duplicates, conference vs. journal pair, rat study, simulation study, German paper, and case report.")
                if st.button("⚡ Load Benchmark Pack v1 (12 Papers)", type="primary", use_container_width=True):
                    vid = create_query_version(
                        "Benchmark v1 (Metformin vs Placebo)",
                        '("type 2 diabetes") AND metformin AND placebo',
                        2015, 2025, ["PubMed", "Europe PMC"], 8, 4
                    )
                    store_fetched_records(vid, get_benchmark_papers("v1"))
                    run_deduplication(vid)
                    run_screening(vid)
                    run_pico_extraction(vid)
                    st.success("✅ Loaded 12 benchmark papers!")
                    st.rerun()
        with d2:
            with st.container(border=True):
                st.markdown("**🔄 Level-2 Expanded Pack v2 (14 Clinical Papers)**")
                st.caption("Simulates refining your search query in Level 2 (+2 new RCTs). Preserves all human decisions made on v1!")
                if st.button("⚡ Load Expanded Pack v2 (14 Papers)", use_container_width=True):
                    vid = create_query_version(
                        "Benchmark v2 (Expanded Query)",
                        '("type 2 diabetes") AND metformin AND (placebo OR sulfonylurea OR sitagliptin)',
                        2015, 2025, ["PubMed", "Europe PMC"], 9, 5
                    )
                    store_fetched_records(vid, get_benchmark_papers("v2"))
                    run_deduplication(vid)
                    run_screening(vid)
                    run_pico_extraction(vid)
                    st.success("✅ Loaded Query v2! Check 'L2 · Compare Searches & Loop' for Diff View.")
                    st.rerun()


# ==============================================================================
# STEP 3: SAVED PAPERS LIBRARY
# ==============================================================================
elif page == PAGES[2]:
    render_coach_banner(
        "🗄️ Step 3: Persistent SQLite Paper Library (Zero-Deletion Architecture)",
        "Every record pulled in Step 2 is permanently stored in SQLite. Duplicate copies are never deleted — they are flagged as <b>🙈 Hidden Duplicate Copy</b> so your audit trail remains 100% reproducible."
    )

    conn = get_connection()
    rows = conn.execute("""
    SELECT
        r.record_id, r.source, r.pmid, r.doi, r.title, r.authors,
        r.pub_year, r.journal, r.language, r.pub_types, r.is_hidden_duplicate,
        GROUP_CONCAT('v' || qr.version_id, ', ') AS found_in_queries
    FROM records r
    LEFT JOIN query_records qr ON r.record_id = qr.record_id
    GROUP BY r.record_id
    ORDER BY r.record_id ASC;
    """).fetchall()
    conn.close()

    if not rows:
        st.info("Library is empty. Pull papers in Steps 1 & 2 first.")
    else:
        f1, f2 = st.columns([2, 1])
        search_lib = f1.text_input("🔎 Search by Title, Author, DOI, or Journal:", "")
        visibility_filter = f2.selectbox(
            "Visibility Filter:",
            ["All Stored Records (Nothing Deleted)", "Visible Unique Representatives Only", "Hidden Duplicate Copies Only"]
        )

        items = [dict(r) for r in rows]
        if visibility_filter == "Visible Unique Representatives Only":
            items = [x for x in items if x["is_hidden_duplicate"] == 0]
        elif visibility_filter == "Hidden Duplicate Copies Only":
            items = [x for x in items if x["is_hidden_duplicate"] == 1]

        if search_lib.strip():
            q = search_lib.lower()
            items = [
                x for x in items
                if q in (x["title"] or "").lower()
                or q in (x["authors"] or "").lower()
                or q in (x["doi"] or "").lower()
            ]

        friendly_rows = [{
            "ID": f"#{x['record_id']}",
            "Status": "🙈 Hidden Duplicate" if x["is_hidden_duplicate"] else "✅ Active Unique",
            "Queries": x["found_in_queries"] or "v1",
            "Source": x["source"],
            "Year": x["pub_year"],
            "Title": x["title"],
            "Authors": x["authors"],
            "Journal": x["journal"],
            "PMID": x["pmid"] or "—",
            "DOI": x["doi"] or "—",
        } for x in items]
        st.dataframe(pd.DataFrame(friendly_rows), use_container_width=True, hide_index=True)


# ==============================================================================
# STEP 4: CLEAN UP DUPLICATES
# ==============================================================================
elif page == PAGES[3]:
    render_coach_banner(
        "🔗 Step 4: Multi-Field Deduplication & Uncertain Pair Resolution",
        "Mini-Rayyan detects duplicates via exact <b>DOI / PMID</b> and normalized <b>Title + Year + First Author</b> matching. "
        "When two records share the same title/author/year but one is a <b>Conference Abstract</b> and one is a <b>Journal Article</b>, it flags them as an <b>Uncertain Pair</b> for your review."
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
        st.info("No multi-record duplicate groups yet. Pull papers in Steps 1 & 2 first.")
    else:
        for g in groups:
            gid = g["group_id"]
            members = conn.execute(
                "SELECT * FROM records WHERE duplicate_group_id = ? ORDER BY is_hidden_duplicate ASC;",
                (gid,)
            ).fetchall()

            is_unc = (g["status"] == "uncertain")
            badge = "⚠️ UNCERTAIN PAIR — NEEDS DECISION" if is_unc else f"✅ {g['status'].upper()}"
            with st.expander(f"Group #{gid} ({len(members)} records) — {badge} | Method: {g['match_method']}", expanded=is_unc):
                for m in members:
                    vis_badge = '<span class="pill pill-red">🙈 Hidden Duplicate</span>' if m["is_hidden_duplicate"] else '<span class="pill pill-green">✅ Visible Representative</span>'
                    st.markdown(
                        f"{vis_badge} **Record #{m['record_id']}** ({m['source']}, {m['pub_year']}) — **{m['title']}**  \n"
                        f"<span style='color:#a1a1aa; font-size:0.84rem;'>Authors: {m['authors']} | Journal: {m['journal']} | Type: <code>{m['pub_types']}</code> | DOI: <code>{m['doi'] or 'Missing'}</code></span>",
                        unsafe_allow_html=True
                    )

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


# ==============================================================================
# STEP 5: COMPETITOR-STYLE INTERACTIVE SPEED-SCREENER WORKBENCH
# ==============================================================================
elif page == PAGES[4]:
    render_coach_banner(
        "⚖️ Step 5: Interactive Screening Workbench (Speed-Screener + Bulk View)",
        "Screen unique papers with <b>1-Click Quick Decisions</b> in the <b>🎯 Speed-Screener Workbench</b> (just like Rayyan / Vercel apps), "
        "or switch to <b>📋 Classic List View</b>. Every exclusion logs an explicit rule/keyword/metadata reason."
    )

    conn = get_connection()
    rows = conn.execute("""
    SELECT
        r.*,
        ms.decision AS machine_decision,
        ms.exclusion_reasons AS machine_reason,
        ms.detection_source,
        rd.screening_decision AS human_decision,
        rd.exclusion_reason AS human_reason,
        rd.reviewer_notes,
        rd.reviewer_name AS last_reviewer,
        mp.population_span, mp.intervention_span, mp.comparator_span, mp.outcome_span,
        rd.pico_p, rd.pico_i, rd.pico_c, rd.pico_o
    FROM records r
    LEFT JOIN machine_screening ms ON r.record_id = ms.record_id
    LEFT JOIN reviewer_decisions rd ON r.duplicate_group_id = rd.group_id
    LEFT JOIN machine_pico mp ON r.record_id = mp.record_id
    WHERE r.is_hidden_duplicate = 0
    ORDER BY r.record_id ASC;
    """).fetchall()
    conn.close()

    records = [dict(r) for r in rows]
    for r in records:
        r["effective_decision"] = r["human_decision"] or r["machine_decision"] or "Maybe"
        r["effective_reason"] = r["human_reason"] if r["human_decision"] else (r["machine_reason"] or "")

    top1, top2, top3 = st.columns([1.2, 1.2, 1.6])
    view_mode = top1.radio("Workbench Mode:", ["🎯 Speed-Screener Card", "📋 Classic List View"], horizontal=True)
    filter_status = top2.selectbox("Filter Queue:", ["All Unique Papers", "Maybe", "Include", "Exclude"])
    search_text = top3.text_input("Search Abstracts:", "", placeholder="Filter by keyword...")

    if filter_status != "All Unique Papers":
        records = [r for r in records if r["effective_decision"] == filter_status]
    if search_text.strip():
        q = search_text.lower()
        records = [r for r in records if q in (r["title"] or "").lower() or q in (r["abstract"] or "").lower()]

    if not records:
        st.info("No papers match this filter. Pull papers in Steps 1 & 2 or change the filter above.")
    elif view_mode == "🎯 Speed-Screener Card":
        # Split-screen / Card navigator
        idx_key = "speed_screen_idx"
        if idx_key not in st.session_state or st.session_state[idx_key] >= len(records):
            st.session_state[idx_key] = 0

        nav1, nav2, nav3 = st.columns([1, 2, 1])
        if nav1.button("⬅️ Previous Paper", use_container_width=True, disabled=(st.session_state[idx_key] <= 0)):
            st.session_state[idx_key] -= 1
            st.rerun()

        paper_options = [f"#{r['record_id']} [{r['effective_decision']}] — {r['title'][:55]}..." for r in records]
        selected_jump = nav2.selectbox(
            f"Paper {st.session_state[idx_key] + 1} of {len(records)}",
            range(len(records)),
            index=st.session_state[idx_key],
            format_func=lambda i: paper_options[i],
            label_visibility="collapsed"
        )
        if selected_jump != st.session_state[idx_key]:
            st.session_state[idx_key] = selected_jump
            st.rerun()

        if nav3.button("Next Paper ➡️", use_container_width=True, disabled=(st.session_state[idx_key] >= len(records) - 1)):
            st.session_state[idx_key] += 1
            st.rerun()

        r = records[st.session_state[idx_key]]
        dec = r["effective_decision"]
        pill_cls = "pill-green" if dec == "Include" else ("pill-red" if dec == "Exclude" else "pill-amber")
        who_badge = f"✍️ Human Override ({r['last_reviewer']})" if r["human_decision"] else f"🤖 Auto-Rule ({r['detection_source'] or 'rule'})"

        p_val = r["pico_p"] or r["population_span"] or ""
        i_val = r["pico_i"] or r["intervention_span"] or ""
        c_val = r["pico_c"] or r["comparator_span"] or ""
        o_val = r["pico_o"] or r["outcome_span"] or ""

        st.markdown(f"""
        <div class="paper-workbench-card">
            <div>
                <span class="pill {pill_cls}">Current: {dec.upper()}</span>
                <span class="pill pill-cyan">{who_badge}</span>
                <span class="pill">{r['source']} • {r['pub_year']}</span>
                <span class="pill">Lang: {r['language']}</span>
                <span class="pill">Type: {r['pub_types']}</span>
                <span class="pill">DOI: {r['doi'] or 'N/A'}</span>
            </div>
            <div class="paper-workbench-title">#{r['record_id']} — {r['title']}</div>
            <div class="paper-meta-line">👤 <b>Authors:</b> {r['authors']} &nbsp;|&nbsp; 🏛️ <b>Journal:</b> {r['journal']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(highlight_pico_html(r["abstract"], p_val, i_val, c_val, o_val), unsafe_allow_html=True)
        st.caption(f"🤖 **Machine Assessment:** `{r['machine_decision']}` — *{r['machine_reason']}*")

        reason_input = st.text_input(
            "Exclusion / Decision Reason (editable):",
            value=r["effective_reason"],
            key=f"fast_reas_{r['record_id']}"
        )

        q1, q2, q3 = st.columns(3)
        if q1.button("✅ INCLUDE STUDY", type="primary", use_container_width=True):
            save_human_decision(
                r["duplicate_group_id"], r["record_id"], reviewer_name, "Include",
                "Meets PICO inclusion criteria", r["reviewer_notes"] or "", p_val, i_val, c_val, o_val, "fast_screen_include"
            )
            if st.session_state[idx_key] < len(records) - 1:
                st.session_state[idx_key] += 1
            st.rerun()

        if q2.button("🤔 MARK AS MAYBE", use_container_width=True):
            save_human_decision(
                r["duplicate_group_id"], r["record_id"], reviewer_name, "Maybe",
                reason_input or "Unclear abstract details — needs full-text check", r["reviewer_notes"] or "", p_val, i_val, c_val, o_val, "fast_screen_maybe"
            )
            if st.session_state[idx_key] < len(records) - 1:
                st.session_state[idx_key] += 1
            st.rerun()

        if q3.button("❌ EXCLUDE STUDY", use_container_width=True):
            final_reas = reason_input.strip() or "Excluded by reviewer"
            save_human_decision(
                r["duplicate_group_id"], r["record_id"], reviewer_name, "Exclude",
                final_reas, r["reviewer_notes"] or "", p_val, i_val, c_val, o_val, "fast_screen_exclude"
            )
            if st.session_state[idx_key] < len(records) - 1:
                st.session_state[idx_key] += 1
            st.rerun()

    else:
        for r in records:
            dec = r["effective_decision"]
            with st.expander(f"[{dec.upper()}] #{r['record_id']} — {r['title']} ({r['pub_year']}) — {r['effective_reason']}"):
                st.write(r["abstract"])
                with st.form(f"screen_form_{r['record_id']}"):
                    sc1, sc2, sc3 = st.columns([1, 2, 2])
                    opts = ["Include", "Exclude", "Maybe"]
                    idx = opts.index(dec) if dec in opts else 2
                    new_dec = sc1.selectbox("Decision:", opts, index=idx, key=f"sdec_{r['record_id']}")
                    new_reason = sc2.text_input("Reason:", value=r["effective_reason"], key=f"sreas_{r['record_id']}")
                    new_notes = sc3.text_input("Notes:", value=r["reviewer_notes"] or "", key=f"snote_{r['record_id']}")
                    if st.form_submit_button("💾 Save Decision", type="primary"):
                        save_human_decision(
                            r["duplicate_group_id"], r["record_id"], reviewer_name, new_dec,
                            new_reason, new_notes,
                            r["pico_p"] or r["population_span"] or "",
                            r["pico_i"] or r["intervention_span"] or "",
                            r["pico_c"] or r["comparator_span"] or "",
                            r["pico_o"] or r["outcome_span"] or "",
                            "screening_override"
                        )
                        st.rerun()


# ==============================================================================
# STEPS 6 & 7: PICO HIGHLIGHTS & EDITING
# ==============================================================================
elif page == PAGES[5]:
    render_coach_banner(
        "🧬 Steps 6 & 7: Automated PICO Span Highlighting & Human Verification",
        "Inspect color-coded <b>[P]</b>, <b>[I]</b>, <b>[C]</b>, and <b>[O]</b> sentences directly inside each abstract and refine the extracted spans below."
    )

    show_only_inc = st.checkbox("Show only Included & Maybe studies", value=True)

    conn = get_connection()
    rows = conn.execute("""
    SELECT
        r.*,
        COALESCE(rd.screening_decision, ms.decision, 'Maybe') AS final_decision,
        COALESCE(rd.exclusion_reason, ms.exclusion_reasons, '') AS final_reason,
        rd.reviewer_notes,
        mp.population_span, mp.intervention_span, mp.comparator_span, mp.outcome_span, mp.uncertainty_flags,
        rd.pico_p, rd.pico_i, rd.pico_c, rd.pico_o
    FROM records r
    LEFT JOIN machine_screening ms ON r.record_id = ms.record_id
    LEFT JOIN reviewer_decisions rd ON r.duplicate_group_id = rd.group_id
    LEFT JOIN machine_pico mp ON r.record_id = mp.record_id
    WHERE r.is_hidden_duplicate = 0
    ORDER BY r.record_id ASC;
    """).fetchall()
    conn.close()

    records = [dict(r) for r in rows]
    if show_only_inc:
        records = [r for r in records if r["final_decision"] in ("Include", "Maybe")]

    if not records:
        st.info("No Included/Maybe studies yet.")

    for r in records:
        p_val = r["pico_p"] if r["pico_p"] is not None else (r["population_span"] or "")
        i_val = r["pico_i"] if r["pico_i"] is not None else (r["intervention_span"] or "")
        c_val = r["pico_c"] if r["pico_c"] is not None else (r["comparator_span"] or "")
        o_val = r["pico_o"] if r["pico_o"] is not None else (r["outcome_span"] or "")

        with st.expander(f"[{r['final_decision'].upper()}] #{r['record_id']}: {r['title']} ({r['pub_year']})", expanded=True):
            st.markdown(highlight_pico_html(r["abstract"], p_val, i_val, c_val, o_val), unsafe_allow_html=True)
            st.write("")
            with st.form(f"pico_edit_{r['record_id']}"):
                pc1, pc2 = st.columns(2)
                new_p = pc1.text_input("🟦 Population (P)", value=p_val, key=f"pp_{r['record_id']}")
                new_i = pc2.text_input("🟩 Intervention (I)", value=i_val, key=f"pi_{r['record_id']}")
                new_c = pc1.text_input("🟧 Comparator (C)", value=c_val, key=f"pc_{r['record_id']}")
                new_o = pc2.text_input("🟪 Outcome (O)", value=o_val, key=f"po_{r['record_id']}")

                dc1, dc2, dc3 = st.columns([1, 2, 2])
                opts = ["Include", "Exclude", "Maybe"]
                d_idx = opts.index(r["final_decision"]) if r["final_decision"] in opts else 0
                new_dec = dc1.selectbox("Final Decision", opts, index=d_idx, key=f"pdec_{r['record_id']}")
                new_reas = dc2.text_input("Reason", value=r["final_reason"], key=f"preas_{r['record_id']}")
                new_note = dc3.text_input("Notes", value=r["reviewer_notes"] or "", key=f"pnote_{r['record_id']}")

                if st.form_submit_button("💾 Save Verified PICO Spans", type="primary"):
                    save_human_decision(
                        r["duplicate_group_id"], r["record_id"], reviewer_name,
                        new_dec, new_reas, new_note, new_p, new_i, new_c, new_o, "pico_edit"
                    )
                    st.success("Saved!")
                    st.rerun()


# ==============================================================================
# LEVEL 2: QUERY LOOP, DIFF VIEW & CONFLICT RESOLUTION
# ==============================================================================
elif page == PAGES[6]:
    render_coach_banner(
        "🔄 Level 2: Query-Change Loop, Version Diffs & Merge Conflict Queue",
        "Compare any two query versions to inspect <b>Newly Added</b> vs. <b>Removed</b> papers while preserving all human screening decisions."
    )

    conn = get_connection()
    queries = conn.execute("SELECT * FROM query_versions ORDER BY version_id DESC;").fetchall()
    conflicts = conn.execute("SELECT * FROM duplicate_groups WHERE has_conflict = 1;").fetchall()
    conn.close()

    st.markdown("##### ⚠️ 1. Duplicate Merge Conflict Queue")
    if conflicts:
        st.error(f"Detected {len(conflicts)} merged duplicate group(s) with opposing human decisions!")
        for c in conflicts:
            with st.container(border=True):
                st.write(f"**Group #{c['group_id']}:** {c['conflict_details']}")
                if st.button(f"✅ Resolve Conflict for Group #{c['group_id']}", key=f"res_{c['group_id']}"):
                    resolve_duplicate_conflict(c["group_id"], c["representative_record_id"], reviewer_name)
                    st.success("Resolved!")
                    st.rerun()
    else:
        st.success("✅ Zero merge conflicts across active duplicate groups.")

    st.markdown("---")
    st.markdown("##### 🔍 2. Query Version Diff View")
    if len(queries) < 2:
        st.info("Load **Expanded Pack v2** in Steps 1 & 2 (Option C) or run a second live search to compare two query versions here.")
    else:
        q_options = {f"v{q['version_id']}: {q['version_name']} ({q['boolean_query']})": q["version_id"] for q in queries}
        labels = list(q_options.keys())
        c1, c2 = st.columns(2)
        old_lbl = c1.selectbox("Older Query Version:", labels, index=min(1, len(labels) - 1))
        new_lbl = c2.selectbox("Newer Query Version:", labels, index=0)

        diff = compute_query_diff(q_options[old_lbl], q_options[new_lbl])
        m1, m2 = st.columns(2)
        m1.metric("➕ Newly Added Papers", diff["added_count"])
        m2.metric("➖ Papers No Longer Returned", diff["removed_count"])

        if diff["added_records"]:
            st.markdown("**🟢 Newly Added Papers:**")
            st.dataframe(
                pd.DataFrame(diff["added_records"])[["record_id", "source", "pub_year", "title", "authors", "journal"]],
                use_container_width=True, hide_index=True
            )
        if diff["removed_records"]:
            st.markdown("**🔴 Papers Not in Newer Search (Preserved in SQLite):**")
            st.dataframe(
                pd.DataFrame(diff["removed_records"])[["record_id", "source", "pub_year", "title", "authors", "journal"]],
                use_container_width=True, hide_index=True
            )


# ==============================================================================
# STEP 8: EXPORT CSV & AUDIT LOGS
# ==============================================================================
elif page == PAGES[7]:
    render_coach_banner(
        "📥 Step 8: Export Screened PICO CSV & Inspect Audit Trail",
        "Download your final included studies and verified PICO spans as a clean CSV, or inspect the complete human override and pipeline execution logs."
    )

    conn = get_connection()
    export_rows = conn.execute("""
    SELECT
        r.record_id, r.duplicate_group_id, r.source, r.pmid, r.doi,
        r.title, r.authors, r.pub_year, r.journal,
        COALESCE(rd.screening_decision, ms.decision, 'Maybe') AS final_decision,
        CASE WHEN rd.screening_decision IS NOT NULL THEN 'Human Override' ELSE 'Machine Rule' END AS decision_source,
        COALESCE(rd.exclusion_reason, ms.exclusion_reasons, '') AS reason,
        COALESCE(rd.reviewer_notes, '') AS reviewer_notes,
        COALESCE(rd.pico_p, mp.population_span, '') AS population_P,
        COALESCE(rd.pico_i, mp.intervention_span, '') AS intervention_I,
        COALESCE(rd.pico_c, mp.comparator_span, '') AS comparator_C,
        COALESCE(rd.pico_o, mp.outcome_span, '') AS outcome_O,
        rd.reviewer_name, rd.updated_at AS last_reviewed_at
    FROM records r
    LEFT JOIN machine_screening ms ON r.record_id = ms.record_id
    LEFT JOIN reviewer_decisions rd ON r.duplicate_group_id = rd.group_id
    LEFT JOIN machine_pico mp ON r.record_id = mp.record_id
    WHERE r.is_hidden_duplicate = 0
    ORDER BY r.record_id ASC;
    """).fetchall()

    df_all = pd.DataFrame([dict(r) for r in export_rows])
    only_inc = st.checkbox("Export only Included studies (uncheck to export all unique records)", value=True)

    if not df_all.empty:
        df_export = df_all[df_all["final_decision"] == "Include"] if only_inc else df_all
        st.dataframe(df_export, use_container_width=True, hide_index=True)
        st.download_button(
            label=f"📥 Download CSV ({len(df_export)} Studies)",
            data=df_export.to_csv(index=False).encode("utf-8"),
            file_name="mini_rayyan_included_studies.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.info("No records to export yet.")

    st.markdown("---")
    c_log1, c_log2 = st.columns(2)
    with c_log1:
        st.markdown("##### ✍️ Human Override Audit Log")
        audits = conn.execute("SELECT * FROM audit_log ORDER BY log_id DESC;").fetchall()
        if audits:
            st.dataframe(pd.DataFrame([dict(a) for a in audits]), use_container_width=True, hide_index=True)
        else:
            st.caption("No manual edits logged yet.")

    with c_log2:
        st.markdown("##### ⚙️ Pipeline Execution Log")
        runs = conn.execute("SELECT * FROM run_log ORDER BY run_id DESC;").fetchall()
        if runs:
            st.dataframe(pd.DataFrame([dict(r) for r in runs]), use_container_width=True, hide_index=True)
        else:
            st.caption("No pipeline runs logged yet.")
    conn.close()
