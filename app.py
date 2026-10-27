"""
MINI-RAYYAN // Ultra-Clean Vibe-Coded Edition (app.py)
Features a Futuristic Interactive Sidebar Command Dock with smooth animations,
while keeping all beginner-friendly guides and Level 1 + Level 2 features intact.
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
    page_title="Mini-Rayyan // Research Studio",
    page_icon="✨",
    layout="wide",
)

init_db()

# ==============================================================================
# VIBE-CODED MODERN SaaS CSS + FUTURISTIC ANIMATED SIDEBAR COMMAND DOCK
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Hide default Streamlit clutter */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Keyframe Animations */
    @keyframes navPulseGlow {
        0%, 100% { box-shadow: 0 0 14px rgba(56, 189, 248, 0.22), inset 0 0 12px rgba(56, 189, 248, 0.08); }
        50% { box-shadow: 0 0 22px rgba(129, 140, 248, 0.40), inset 0 0 16px rgba(129, 140, 248, 0.14); }
    }
    @keyframes progressShimmer {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes fadeInSlide {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Smooth Ambient Dark Background */
    .stApp {
        background:
            radial-gradient(ellipse 80% 50% at 50% -15%, rgba(56, 189, 248, 0.14), transparent),
            radial-gradient(ellipse 60% 50% at 85% 90%, rgba(139, 92, 246, 0.10), transparent),
            #090d16;
        color: #f8fafc;
    }

    /* ==========================================================================
       FUTURISTIC INTERACTIVE SIDEBAR COMMAND DOCK
       ========================================================================== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 15, 28, 0.96) 0%, rgba(7, 11, 20, 0.98) 100%) !important;
        backdrop-filter: blur(24px);
        border-right: 1px solid rgba(56, 189, 248, 0.14);
    }

    /* Sidebar Brand Box */
    .sidebar-brand {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 1px solid rgba(56, 189, 248, 0.22);
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 14px;
        box-shadow: 0 8px 24px -8px rgba(0, 0, 0, 0.5);
    }
    .sidebar-brand-title {
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: -0.3px;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #e879f9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sidebar-brand-sub {
        font-size: 0.74rem;
        color: #94a3b8;
        margin-top: 2px;
        letter-spacing: 0.3px;
    }

    /* Pipeline Progress Tracker in Sidebar */
    .nav-header-box {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 14px 2px 6px 2px;
    }
    .nav-header-title {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.1px;
        color: #7dd3fc;
    }
    .nav-header-step {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        color: #c084fc;
        background: rgba(192, 132, 252, 0.12);
        padding: 2px 8px;
        border-radius: 999px;
        border: 1px solid rgba(192, 132, 252, 0.3);
    }
    .nav-progress-track {
        width: 100%;
        height: 6px;
        background: rgba(30, 41, 59, 0.8);
        border-radius: 999px;
        overflow: hidden;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .nav-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        background-size: 200% 200%;
        animation: progressShimmer 3s ease infinite;
        border-radius: 999px;
        transition: width 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* Transform Default Radio Group into Futuristic Interactive Cards */
    section[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 7px !important;
        display: flex;
        flex-direction: column;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background: rgba(17, 24, 39, 0.65) !important;
        border: 1px solid rgba(255, 255, 255, 0.07) !important;
        border-left: 3px solid rgba(100, 116, 139, 0.35) !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        position: relative;
        overflow: hidden;
    }
    /* Hide the boring default radio circle */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    /* Step Text Styling */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label p {
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        margin: 0 !important;
        transition: all 0.2s ease !important;
        letter-spacing: -0.1px;
    }
    /* Hover Micro-Interaction: Slide Right + Neon Border Glow */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        transform: translateX(6px) !important;
        background: linear-gradient(90deg, rgba(56, 189, 248, 0.12) 0%, rgba(30, 41, 59, 0.75) 100%) !important;
        border-color: rgba(56, 189, 248, 0.40) !important;
        border-left: 4px solid #38bdf8 !important;
        box-shadow: 0 6px 18px -6px rgba(56, 189, 248, 0.28) !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover p {
        color: #f8fafc !important;
    }
    /* Active / Selected Step Card (Glowing Neon Pill) */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.20) 0%, rgba(129, 140, 248, 0.16) 100%) !important;
        border: 1px solid rgba(56, 189, 248, 0.65) !important;
        border-left: 5px solid #38bdf8 !important;
        transform: translateX(6px) !important;
        animation: navPulseGlow 3s infinite ease-in-out;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
        color: #ffffff !important;
        font-weight: 700 !important;
        text-shadow: 0 0 12px rgba(56, 189, 248, 0.45);
    }

    /* ==========================================================================
       MAIN WORKSPACE STYLING (UNTOUCHED & CLEAN)
       ========================================================================== */
    .hero-glass {
        animation: fadeInSlide 0.35s ease-out;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.55) 0%, rgba(15, 23, 42, 0.75) 100%);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 18px;
        padding: 20px 26px;
        margin-bottom: 18px;
        backdrop-filter: blur(16px);
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 12px 32px -12px rgba(0, 0, 0, 0.6);
    }
    .hero-title {
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: -0.4px;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 55%, #e879f9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-question {
        font-size: 0.92rem;
        color: #cbd5e1;
        margin-top: 6px;
        line-height: 1.4;
    }

    /* Clean Horizontal Journey Bar */
    .journey-bar {
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        gap: 8px;
        margin-bottom: 20px;
    }
    .journey-pill {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 10px 8px;
        text-align: center;
        transition: all 0.25s ease;
    }
    .journey-pill.active {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.20), rgba(129, 140, 248, 0.20));
        border: 1px solid #38bdf8;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.22);
        transform: translateY(-2px);
    }
    .journey-num {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #64748b;
    }
    .journey-pill.active .journey-num {
        color: #38bdf8;
    }
    .journey-name {
        font-size: 0.80rem;
        font-weight: 700;
        color: #94a3b8;
        margin-top: 2px;
    }
    .journey-pill.active .journey-name {
        color: #ffffff;
    }

    /* 4 Clean Summary Metric Cards */
    .stat-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 24px;
    }
    .stat-box {
        background: rgba(17, 24, 39, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 16px 20px;
        backdrop-filter: blur(12px);
        transition: all 0.25s ease;
    }
    .stat-box:hover {
        transform: translateY(-3px);
        border-color: rgba(56, 189, 248, 0.35);
    }
    .stat-title {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #94a3b8;
    }
    .stat-big {
        font-size: 1.75rem;
        font-weight: 800;
        color: #f8fafc;
        margin: 4px 0 2px 0;
    }
    .stat-sub {
        font-size: 0.78rem;
        color: #64748b;
    }

    /* Friendly Coach Card at Top of Every Page */
    .coach-banner {
        animation: fadeInSlide 0.4s ease-out;
        background: linear-gradient(90deg, rgba(56, 189, 248, 0.10) 0%, rgba(129, 140, 248, 0.08) 100%);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-left: 4px solid #38bdf8;
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 22px;
    }
    .coach-heading {
        font-size: 1.02rem;
        font-weight: 700;
        color: #e0f2fe;
        margin-bottom: 4px;
    }
    .coach-text {
        font-size: 0.90rem;
        color: #cbd5e1;
        line-height: 1.55;
    }

    /* Sub-step Numbered Cards */
    .substep-badge {
        display: inline-block;
        background: rgba(56, 189, 248, 0.16);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.35);
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 999px;
        margin-bottom: 8px;
    }

    /* Pills */
    .pill {
        display: inline-block;
        font-size: 0.76rem;
        padding: 4px 12px;
        border-radius: 999px;
        font-weight: 600;
        background: rgba(30, 41, 59, 0.85);
        border: 1px solid rgba(148, 163, 184, 0.25);
        color: #cbd5e1;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .pill-cyan { background: rgba(56, 189, 248, 0.15); border-color: #38bdf8; color: #7dd3fc; }
    .pill-green { background: rgba(16, 185, 129, 0.15); border-color: #10b981; color: #6ee7b7; }
    .pill-red { background: rgba(244, 63, 94, 0.15); border-color: #f43f5e; color: #fda4af; }
    .pill-amber { background: rgba(245, 158, 11, 0.15); border-color: #f59e0b; color: #fcd34d; }

    /* Smooth Buttons */
    div.stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px -6px rgba(56, 189, 248, 0.45) !important;
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
    """Renders a clean, friendly explanation banner at the top of the current step."""
    st.markdown(f"""
    <div class="coach-banner">
        <div class="coach-heading">{title}</div>
        <div class="coach-text">{explanation}</div>
    </div>
    """, unsafe_allow_html=True)


def build_boolean_query_from_pico(config: dict) -> str:
    """Automatically build a clean search query from Step 0 P, I, C terms."""
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
# FUTURISTIC SIDEBAR COMMAND DOCK
# ==============================================================================
st.sidebar.markdown("""
<div class="sidebar-brand">
    <div class="sidebar-brand-title">✨ MINI-RAYYAN OS</div>
    <div class="sidebar-brand-sub">AI-Assisted Evidence Synthesis</div>
</div>
""", unsafe_allow_html=True)

reviewer_name = st.sidebar.text_input(
    "👤 Operator / Reviewer Name",
    value="Lead Reviewer (UG3)",
    help="Every decision or edit you make is saved under your name."
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

# Render Live Progress Header right above the interactive step cards
current_page_val = st.session_state.get("nav_radio_dock", PAGES[0])
curr_step_num = PAGES.index(current_page_val) + 1 if current_page_val in PAGES else 1
progress_pct = int((curr_step_num / len(PAGES)) * 100)

st.sidebar.markdown(f"""
<div class="nav-header-box">
    <span class="nav-header-title">⚡ Pipeline Command Dock</span>
    <span class="nav-header-step">STAGE {curr_step_num}/{len(PAGES)}</span>
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
with st.sidebar.expander("📘 Quick Beginner Glossary"):
    st.markdown("""
    - **PICO:** The 4 building blocks of a medical research question (**P**atients, **I**ntervention/Drug, **C**omparison, **O**utcome).
    - **PubMed & Europe PMC:** Free global search engines for scientific and medical research papers.
    - **Abstract:** The short 1-paragraph summary of a research paper.
    - **DOI / PMID:** Unique ID codes assigned to every published scientific paper.
    """)

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Reset & Start New Topic", use_container_width=True):
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    st.sidebar.success("Database cleared! Ready for a new topic.")
    st.rerun()

st.sidebar.caption("Powered by free PubMed & Europe PMC APIs.")


# ==============================================================================
# TOP HERO HEADER, JOURNEY BAR & 4 CLEAN SUMMARY CARDS
# ==============================================================================
stats = get_dashboard_stats()
config = get_project_config()

st.markdown(f"""
<div class="hero-glass">
    <div>
        <div class="hero-title">✨ Mini-Rayyan Research Studio</div>
        <div class="hero-question">🎯 <b>Current Research Question:</b> {config['review_question']}</div>
    </div>
    <div style="text-align:right; min-width: 190px;">
        <span class="pill pill-cyan">👤 {reviewer_name}</span><br>
        <span class="pill pill-green">⚡ {stats['query_count']} Search Versions Saved</span>
    </div>
</div>
""", unsafe_allow_html=True)

active_idx = PAGES.index(page)
short_steps = [
    ("Step 0", "Topic & PICO"),
    ("Steps 1–2", "Search & Pull"),
    ("Step 3", "Paper Library"),
    ("Step 4", "Duplicates"),
    ("Step 5", "Screen Papers"),
    ("Steps 6–7", "PICO Tags"),
    ("Level 2", "Diff & Loop"),
    ("Step 8", "Export CSV"),
]
journey_html = '<div class="journey-bar">'
for idx, (s_num, s_name) in enumerate(short_steps):
    cls = "journey-pill active" if idx == active_idx else "journey-pill"
    journey_html += f'<div class="{cls}"><div class="journey-num">{s_num}</div><div class="journey-name">{s_name}</div></div>'
journey_html += "</div>"
st.markdown(journey_html, unsafe_allow_html=True)

# 4 Clean Summary Metric Cards
st.markdown(f"""
<div class="stat-row">
    <div class="stat-box">
        <div class="stat-title">📚 1. Paper Library</div>
        <div class="stat-big" style="color:#38bdf8;">{stats['unique_visible']} <span style="font-size:0.95rem; color:#94a3b8; font-weight:500;">unique papers</span></div>
        <div class="stat-sub">{stats['total_records']} total pulled • {stats['hidden_dups']} duplicate copies hidden</div>
    </div>
    <div class="stat-box">
        <div class="stat-title">✅ 2. Included Studies</div>
        <div class="stat-big" style="color:#10b981;">{stats['included']} <span style="font-size:0.95rem; color:#94a3b8; font-weight:500;">accepted</span></div>
        <div class="stat-sub">{stats['excluded']} excluded by rules</div>
    </div>
    <div class="stat-box">
        <div class="stat-title">🤔 3. Needs Your Review</div>
        <div class="stat-big" style="color:#f59e0b;">{stats['maybe'] + stats['uncertain_dups']} <span style="font-size:0.95rem; color:#94a3b8; font-weight:500;">items pending</span></div>
        <div class="stat-sub">{stats['maybe']} 'Maybe' papers • {stats['uncertain_dups']} uncertain duplicate pairs</div>
    </div>
    <div class="stat-box">
        <div class="stat-title">✍️ 4. Human Control</div>
        <div class="stat-big" style="color:#c084fc;">{stats['overrides']} <span style="font-size:0.95rem; color:#94a3b8; font-weight:500;">manual edits</span></div>
        <div class="stat-sub">{stats['conflicts']} Level-2 merge conflicts</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# STEP 0: DEFINE TOPIC & PICO
# ==============================================================================
if page == PAGES[0]:
    render_coach_banner(
        "👋 Welcome to Step 0! Let's set up your research topic in plain English.",
        "Before searching for scientific papers, tell Mini-Rayyan <b>what medical question you want to answer</b>. "
        "We break your question into 4 simple boxes called <b>PICO</b> (<b>P</b>atients, <b>I</b>ntervention/Treatment, <b>C</b>omparison, <b>O</b>utcome). "
        "Once you save this, Mini-Rayyan will automatically write your search query for Step 1!"
    )

    criteria = config["criteria"]
    selected_tpl = st.selectbox(
        "✨ Want a quick start? Pick a sample medical topic (or keep your own):",
        list(TOPIC_TEMPLATES.keys())
    )
    tpl_data = TOPIC_TEMPLATES[selected_tpl]

    default_rq = tpl_data["question"] if tpl_data else config["review_question"]
    default_p = tpl_data["P"] if tpl_data else config["population_text"]
    default_i = tpl_data["I"] if tpl_data else config["intervention_text"]
    default_c = tpl_data["C"] if tpl_data else config["comparator_text"]
    default_o = tpl_data["O"] if tpl_data else config["outcome_text"]

    with st.form("step0_form"):
        st.markdown("##### 1️⃣ Your Main Research Question")
        rq = st.text_area(
            "Write your question in one sentence:",
            value=default_rq,
            height=68,
            help="Example: In adults with type 2 diabetes, does metformin compared with placebo lower HbA1c?"
        )

        st.markdown("##### 2️⃣ Break It Into 4 PICO Boxes (Comma-Separated Words)")
        col1, col2 = st.columns(2)
        with col1:
            pop = st.text_input(
                "🟦 P — Population (Who are the patients?)",
                value=default_p,
                help="Example: Adults with type 2 diabetes, diabetic patients"
            )
            inter = st.text_input(
                "🟩 I — Intervention (What drug or treatment is tested?)",
                value=default_i,
                help="Example: Metformin, glucophage"
            )
        with col2:
            comp = st.text_input(
                "🟧 C — Comparator (What is it compared against?)",
                value=default_c,
                help="Example: Placebo, sulfonylurea, standard care"
            )
            out = st.text_input(
                "🟪 O — Outcome (What health result is measured?)",
                value=default_o,
                help="Example: HbA1c, blood sugar, survival"
            )

        with st.expander("⚙️ Advanced: Customize Automatic Rejection Rules (Animal studies, Simulations, Non-English, Case Reports)"):
            st.caption("By default, Mini-Rayyan automatically flags animal studies, computer simulations, non-English papers, and single-patient case reports as 'Exclude'. You can toggle or edit them here:")
            for key, item in criteria.items():
                cc1, cc2, cc3 = st.columns([1.2, 2.2, 2.2])
                item["active"] = cc1.checkbox(item["label"], value=item["active"], key=f"act_{key}")
                item["reason"] = cc2.text_input("Reason", value=item["reason"], key=f"reas_{key}", label_visibility="collapsed")
                kw_str = ", ".join(item.get("keywords", []))
                new_kw = cc3.text_input("Keywords", value=kw_str, key=f"kw_{key}", placeholder="Uses official paper metadata", label_visibility="collapsed")
                item["keywords"] = [k.strip() for k in new_kw.split(",") if k.strip()]

        if st.form_submit_button("💾 Save Step 0 & Prepare My Search Query ➔", type="primary", use_container_width=True):
            save_project_config(rq, pop, inter, comp, out, criteria)
            run_screening()
            run_pico_extraction()
            st.success("✅ Saved! Now click '01–02 · Search & Pull Papers' in the left sidebar.")
            st.rerun()


# ==============================================================================
# STEPS 1 & 2: BEGINNER-FRIENDLY SEARCH & FETCH
# ==============================================================================
elif page == PAGES[1]:
    render_coach_banner(
        "🔍 How do Steps 1 & 2 work? (No coding or complex syntax needed!)",
        "Finding research papers happens in two easy steps:<br>"
        "<b>Step 1 (Preview Search):</b> We ask two free global medical libraries (<b>PubMed</b> & <b>Europe PMC</b>) how many papers match your topic.<br>"
        "<b>Step 2 (Approve & Download):</b> If you like the search results, you click <b>Approve & Download</b> to pull the paper summaries (abstracts) into your workspace."
    )

    tab_live, tab_builder, tab_demo = st.tabs([
        "🚀 Option A: Search Live Medical Databases (PubMed & Europe PMC)",
        "🧩 Optional: Visual Search Builder (No AND/OR needed)",
        "⚡ Option B: Instant Offline Demo Pack (Best for Quick Testing)"
    ])

    with tab_builder:
        st.markdown("##### 🧩 Build a Search Query Visually")
        st.caption("Don't know how to write `AND` / `OR` queries? Type simple words below and we will build the formula for you:")
        b1, b2, b3 = st.columns(3)
        must_have = b1.text_input("Must include condition (AND)", value="type 2 diabetes")
        either_or = b2.text_input("Must include treatment (AND)", value="metformin")
        exclude_not = b3.text_input("Exclude word (NOT — optional)", value="")
        built_q = f'("{must_have.strip()}") AND ({either_or.strip()})'
        if exclude_not.strip():
            built_q += f' NOT ({exclude_not.strip()})'
        st.code(built_q, language="text")
        if st.button("📋 Copy This Formula Into My Search Box"):
            st.session_state["custom_query_box"] = built_q
            st.success("Copied! Switch back to Option A tab to run it.")

    with tab_live:
        st.markdown('<span class="substep-badge">SUB-STEP 1A • CHECK HOW MANY PAPERS EXIST</span>', unsafe_allow_html=True)
        auto_q = st.session_state.get("custom_query_box") or build_boolean_query_from_pico(config)

        with st.container(border=True):
            q_str = st.text_input(
                "1. Your Search Formula (Automatically created from your Step 0 PICO — feel free to edit!)",
                value=auto_q,
                help="Tip: AND means the paper must mention both words. OR means it can mention either word."
            )
            c1, c2, c3, c4 = st.columns([1, 1, 1.2, 1.5])
            date_from = c1.number_input("From Year", 1990, 2026, 2016)
            date_to = c2.number_input("To Year", 1990, 2026, 2026)
            max_fetch = c3.slider("Max Papers to Pull", 10, 100, 40, 10, help="How many papers to download when you approve.")
            v_label = c4.text_input("Search Version Name", value=f"Search v{stats['query_count'] + 1}")

            sources = st.multiselect(
                "Which free medical libraries should we search?",
                ["PubMed", "Europe PMC"],
                default=["PubMed", "Europe PMC"]
            )

            if st.button("🔍 Step 1: Check Paper Count on PubMed & Europe PMC", type="primary", use_container_width=True):
                if not q_str.strip() or not sources:
                    st.warning("Please enter a search formula and select at least one library.")
                else:
                    with st.spinner("Asking PubMed & Europe PMC how many papers match..."):
                        pm_hits, pm_ids, err1 = (0, [], "")
                        ep_hits, err2 = (0, "")
                        if "PubMed" in sources:
                            pm_hits, pm_ids, err1 = search_pubmed_hits(q_str, int(date_from), int(date_to), max_fetch)
                        if "Europe PMC" in sources:
                            ep_hits, err2 = search_epmc_hits(q_str, int(date_from), int(date_to))

                        vid = create_query_version(v_label, q_str, int(date_from), int(date_to), sources, pm_hits, ep_hits)
                        st.session_state["max_per_source"] = max_fetch
                        if err1 or err2:
                            st.warning(f"{err1} {err2}")
                        st.success(f"🎉 Found **{pm_hits:,}** matching papers on PubMed and **{ep_hits:,}** on Europe PMC! Scroll down to **Sub-Step 1B** to approve and download them.")

        st.write("")
        st.markdown('<span class="substep-badge">SUB-STEP 1B • APPROVE & DOWNLOAD PAPER SUMMARIES</span>', unsafe_allow_html=True)
        conn = get_connection()
        q_rows = conn.execute("SELECT * FROM query_versions ORDER BY version_id DESC;").fetchall()
        conn.close()

        if not q_rows:
            st.info("👆 Click **'Step 1: Check Paper Count'** above (or use the **Instant Offline Demo Pack** tab) to see your searches here.")
        else:
            for q in q_rows:
                status_txt = "✅ Downloaded into Library" if q["fetched"] else "⏳ Waiting for Your Approval"
                with st.expander(
                    f"Version #{q['version_id']}: {q['version_name']} — Found {q['pubmed_hits']:,} PubMed & {q['epmc_hits']:,} Europe PMC papers | {status_txt}",
                    expanded=(not q["fetched"])
                ):
                    st.markdown(f"**Search Formula:** `{q['boolean_query']}` &nbsp;|&nbsp; **Years:** `{q['date_from']}–{q['date_to']}` &nbsp;|&nbsp; **Libraries:** `{q['sources']}`")
                    if st.button(f"📥 Step 2: Approve & Download Papers for Version #{q['version_id']}", key=f"pull_{q['version_id']}", type="primary"):
                        max_f = st.session_state.get("max_per_source", 40)
                        fetched_papers = []
                        src_list = q["sources"].split(",")
                        with st.spinner("Downloading paper summaries and running Auto-Deduplication ➔ Screening ➔ PICO Highlighter..."):
                            if "PubMed" in src_list:
                                _, pm_ids, _ = search_pubmed_hits(q["boolean_query"], q["date_from"], q["date_to"], max_f)
                                pm_recs, _ = fetch_pubmed_abstracts(pm_ids)
                                fetched_papers.extend(pm_recs)
                            if "Europe PMC" in src_list:
                                ep_recs, _ = fetch_epmc_abstracts(q["boolean_query"], q["date_from"], q["date_to"], max_f)
                                fetched_papers.extend(ep_recs)

                            if not fetched_papers:
                                st.error("No papers could be downloaded. Try broadening your search words or use the Instant Offline Demo Pack tab.")
                            else:
                                st_res = store_fetched_records(q["version_id"], fetched_papers)
                                dup_res = run_deduplication(q["version_id"])
                                scr_res = run_screening(q["version_id"])
                                run_pico_extraction(q["version_id"])
                                st.success(
                                    f"✅ Downloaded {len(fetched_papers)} papers ({st_res['new']} brand new, {st_res['reused']} already in library)! "
                                    f"Automatically hid {dup_res['hidden_duplicates']} duplicate copies and screened all papers."
                                )
                                st.rerun()

    with tab_demo:
        st.markdown("##### ⚡ One-Click Sample Paper Packs (Works Offline!)")
        st.write(
            "Want to test or demo the entire app in 2 seconds? These pre-built packs contain realistic clinical papers "
            "(exact DOI duplicates, missing-DOI duplicates, a conference abstract vs. journal paper, a rat study, a computer simulation, a German paper, and a case report)."
        )
        d1, d2 = st.columns(2)
        with d1:
            with st.container(border=True):
                st.markdown("**📦 Pack 1: Initial Search (12 Papers)**")
                st.caption("Simulates `Query Version 1` (Metformin vs. Placebo). Loads 12 papers with 2 auto-duplicates and 1 uncertain conference/journal pair.")
                if st.button("📥 Load Pack 1 (12 Sample Papers)", type="primary", use_container_width=True):
                    vid = create_query_version(
                        "Demo Search v1 (Metformin vs Placebo)",
                        '("type 2 diabetes") AND metformin AND placebo',
                        2015, 2025, ["PubMed", "Europe PMC"], 8, 4
                    )
                    store_fetched_records(vid, get_benchmark_papers("v1"))
                    run_deduplication(vid)
                    run_screening(vid)
                    run_pico_extraction(vid)
                    st.success("✅ Pack 1 (12 papers) loaded! Check Step 3, Step 4, or Step 5 in the sidebar.")
                    st.rerun()

        with d2:
            with st.container(border=True):
                st.markdown("**🔄 Pack 2: Expanded Level-2 Search (+2 New Papers)**")
                st.caption("Simulates editing your query in `Level 2` to add Sulfonylurea/Sitagliptin (`Query Version 2`). Keeps all your earlier decisions safe!")
                if st.button("📥 Load Pack 2 (Expanded Query v2 — 14 Papers)", use_container_width=True):
                    vid = create_query_version(
                        "Demo Search v2 (Expanded with Sulfonylurea)",
                        '("type 2 diabetes") AND metformin AND (placebo OR sulfonylurea OR sitagliptin)',
                        2015, 2025, ["PubMed", "Europe PMC"], 9, 5
                    )
                    store_fetched_records(vid, get_benchmark_papers("v2"))
                    run_deduplication(vid)
                    run_screening(vid)
                    run_pico_extraction(vid)
                    st.success("✅ Pack 2 loaded as a new Query Version! Go to 'L2 · Compare Searches & Loop' to see the Diff View!")
                    st.rerun()


# ==============================================================================
# STEP 3: SAVED PAPERS LIBRARY (FRIENDLY DATABASE VIEW)
# ==============================================================================
elif page == PAGES[2]:
    render_coach_banner(
        "🗄️ What is Step 3 (Your Paper Library)?",
        "Every paper you download in Step 2 is safely stored inside your permanent SQLite database. "
        "<b>Hackathon Golden Rule — Nothing is ever deleted:</b> When Mini-Rayyan finds two copies of the same paper (or when a paper is excluded), "
        "it never deletes it from the database. Instead, it marks extra copies as <b>🙈 Hidden Duplicate Copy</b> so you can trace or undo any decision at any time."
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
        st.info("Your library is empty right now. Go to **01–02 · Search & Pull Papers** to download papers first!")
    else:
        f1, f2 = st.columns([2, 1])
        search_lib = f1.text_input("🔎 Search inside your saved papers (by title, author, or journal):", "")
        visibility_filter = f2.selectbox(
            "Filter by Visibility:",
            ["Show All Saved Papers (Nothing Deleted)", "Only Visible Unique Papers", "Only Hidden Duplicate Copies"]
        )

        items = [dict(r) for r in rows]
        if visibility_filter == "Only Visible Unique Papers":
            items = [x for x in items if x["is_hidden_duplicate"] == 0]
        elif visibility_filter == "Only Hidden Duplicate Copies":
            items = [x for x in items if x["is_hidden_duplicate"] == 1]

        if search_lib.strip():
            q = search_lib.lower()
            items = [x for x in items if q in (x["title"] or "").lower() or q in (x["authors"] or "").lower() or q in (x["journal"] or "").lower()]

        st.caption(f"Showing **{len(items)}** of **{len(rows)}** total records stored in database.")

        friendly_rows = []
        for x in items:
            friendly_rows.append({
                "Paper #": f"#{x['record_id']}",
                "Library Status": "🙈 Hidden Duplicate Copy" if x["is_hidden_duplicate"] else "✅ Active Unique Paper",
                "Found in Searches": x["found_in_queries"] or "v1",
                "Source Library": x["source"],
                "Year": x["pub_year"],
                "Paper Title": x["title"],
                "Authors": x["authors"],
                "Journal": x["journal"],
                "PMID": x["pmid"] or "—",
                "DOI": x["doi"] or "—",
            })
        st.dataframe(pd.DataFrame(friendly_rows), use_container_width=True, hide_index=True)


# ==============================================================================
# STEP 4: CLEAN UP DUPLICATES
# ==============================================================================
elif page == PAGES[3]:
    render_coach_banner(
        "🔗 How does Duplicate Cleanup work?",
        "Because we search both PubMed and Europe PMC, the exact same paper often shows up twice. "
        "Mini-Rayyan groups identical papers using their <b>DOI / PMID numbers</b> (or by matching <b>Title + Year + First Author</b> if the DOI is missing).<br>"
        "• <b>Auto-Confirmed Duplicates:</b> 1 best copy is kept visible and the extra copy is automatically hidden.<br>"
        "• <b>⚠️ Uncertain Pairs (Needs Your Decision):</b> If two papers have the same title and author, but one is a short <b>Conference Abstract</b> and one is a full <b>Journal Article</b>, Mini-Rayyan asks <b>you</b> whether to merge them or keep both separate."
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
        st.info("No duplicate groups detected yet. Pull papers in Steps 1 & 2 first!")
    else:
        for g in groups:
            gid = g["group_id"]
            members = conn.execute(
                "SELECT * FROM records WHERE duplicate_group_id = ? ORDER BY is_hidden_duplicate ASC;",
                (gid,)
            ).fetchall()

            is_unc = (g["status"] == "uncertain")
            badge = "⚠️ NEEDS YOUR CONFIRMATION (Conference vs. Journal)" if is_unc else f"✅ {g['status'].upper()}"
            with st.expander(f"Group #{gid} ({len(members)} papers) — {badge} | How it matched: {g['match_method']}", expanded=is_unc):
                for m in members:
                    vis_badge = '<span class="pill pill-red">🙈 Hidden Copy</span>' if m["is_hidden_duplicate"] else '<span class="pill pill-green">✅ Visible Representative</span>'
                    st.markdown(
                        f"{vis_badge} **Paper #{m['record_id']}** ({m['source']}, {m['pub_year']}) — **{m['title']}**  \n"
                        f"<span style='color:#94a3b8; font-size:0.85rem;'>Authors: {m['authors']} | Journal: {m['journal']} | Type: <code>{m['pub_types']}</code> | DOI: <code>{m['doi'] or 'Missing'}</code> | PMID: <code>{m['pmid'] or 'Missing'}</code></span>",
                        unsafe_allow_html=True
                    )

                b1, b2 = st.columns(2)
                if b1.button(f"✅ Merge as Duplicates (Keep Paper #{g['representative_record_id']} Visible, Hide Extra Copy)", key=f"conf_dup_{gid}", use_container_width=True):
                    conn.execute("UPDATE duplicate_groups SET status = 'human_confirmed' WHERE group_id = ?;", (gid,))
                    conn.execute(
                        "UPDATE records SET is_hidden_duplicate = CASE WHEN record_id = ? THEN 0 ELSE 1 END WHERE duplicate_group_id = ?;",
                        (g["representative_record_id"], gid)
                    )
                    conn.commit()
                    log_human_audit(reviewer_name, "duplicate_override", gid, g["status"], "human_confirmed", "Confirmed duplicate group")
                    st.rerun()

                if b2.button(f"✂️ Not Duplicates — Keep Both Separate & Visible", key=f"split_dup_{gid}", use_container_width=True):
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
# STEP 5: SCREEN STUDIES (INCLUDE / EXCLUDE / MAYBE)
# ==============================================================================
elif page == PAGES[4]:
    render_coach_banner(
        "⚖️ What happens in Step 5 (Study Screening)?",
        "Here we decide which papers belong in our final review:<br>"
        "• <b>✅ Include:</b> Real human clinical studies that match your Step 0 PICO question.<br>"
        "• <b>❌ Exclude:</b> Papers that break your rules (like rat/animal tests, computer simulations, foreign-language papers, or single-patient case reports). Every exclusion has a clear reason.<br>"
        "• <b>🤔 Maybe:</b> Papers where the abstract is unclear — flagged so <b>you</b> can make the final call!"
    )

    f_col1, f_col2 = st.columns([1, 2.2])
    filter_status = f_col1.selectbox("Filter by Decision:", ["All Unique Papers", "Include", "Exclude", "Maybe"])
    search_text = f_col2.text_input("Search inside Titles or Abstracts:", "", placeholder="Type e.g. 'rat', 'simulation', 'placebo'...")

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

    if filter_status != "All Unique Papers":
        records = [r for r in records if r["effective_decision"] == filter_status]
    if search_text.strip():
        q = search_text.lower()
        records = [r for r in records if q in (r["title"] or "").lower() or q in (r["abstract"] or "").lower()]

    if not records:
        st.info("No papers match this filter yet.")

    for r in records:
        dec = r["effective_decision"]
        pill_cls = "pill-green" if dec == "Include" else ("pill-red" if dec == "Exclude" else "pill-amber")
        who_badge = f"✍️ Overridden by {r['last_reviewer']}" if r["human_decision"] else f"🤖 Auto-Screened ({r['detection_source'] or 'rule'})"

        with st.expander(f"[{dec.upper()}] Paper #{r['record_id']} — {r['title']} ({r['pub_year'] or 'N/A'}) — {r['effective_reason']}"):
            st.markdown(f"""
            <div>
                <span class="pill {pill_cls}">Decision: {dec}</span>
                <span class="pill pill-cyan">{who_badge}</span>
                <span class="pill">Source: {r['source']}</span>
                <span class="pill">Language: {r['language']}</span>
                <span class="pill">Type: {r['pub_types']}</span>
                <span class="pill">DOI: {r['doi'] or 'None'}</span>
            </div>
            """, unsafe_allow_html=True)

            st.write(r["abstract"] or "*No abstract text provided.*")
            st.caption(f"🤖 **Machine Suggestion:** `{r['machine_decision']}` — *Reason: {r['machine_reason']}*")

            with st.form(f"screen_form_{r['record_id']}"):
                sc1, sc2, sc3 = st.columns([1, 2, 2])
                opts = ["Include", "Exclude", "Maybe"]
                idx = opts.index(dec) if dec in opts else 2
                new_dec = sc1.selectbox("Change Decision:", opts, index=idx, key=f"sdec_{r['record_id']}")
                new_reason = sc2.text_input("Reason (Required if Excluding):", value=r["effective_reason"], key=f"sreas_{r['record_id']}")
                new_notes = sc3.text_input("Reviewer Notes (Optional):", value=r["reviewer_notes"] or "", key=f"snote_{r['record_id']}")

                if st.form_submit_button("💾 Save My Decision", type="primary"):
                    if new_dec == "Exclude" and not new_reason.strip():
                        st.error("Please enter a reason when excluding a study!")
                    else:
                        save_human_decision(
                            group_id=r["duplicate_group_id"],
                            record_id=r["record_id"],
                            reviewer_name=reviewer_name,
                            screening_decision=new_dec,
                            exclusion_reason=new_reason,
                            reviewer_notes=new_notes,
                            pico_p=r["pico_p"] or r["population_span"] or "",
                            pico_i=r["pico_i"] or r["intervention_span"] or "",
                            pico_c=r["pico_c"] or r["comparator_span"] or "",
                            pico_o=r["pico_o"] or r["outcome_span"] or "",
                            action_label="screening_override"
                        )
                        st.success(f"Saved '{new_dec}' for Paper #{r['record_id']}!")
                        st.rerun()


# ==============================================================================
# STEPS 6 & 7: PICO HIGHLIGHTS & EDITING
# ==============================================================================
elif page == PAGES[5]:
    render_coach_banner(
        "🎨 What is PICO Highlighting & Review?",
        "For every eligible study, Mini-Rayyan automatically finds and highlights the exact sentences describing:<br>"
        "🟦 <b>[P] Population</b> (Who was studied) &nbsp;|&nbsp; 🟩 <b>[I] Intervention</b> (Treatment given) &nbsp;|&nbsp; "
        "🟧 <b>[C] Comparator</b> (Comparison group) &nbsp;|&nbsp; 🟪 <b>[O] Outcome</b> (Measured result).<br>"
        "You can edit any of the 4 boxes below if you want to refine the extracted text!"
    )

    show_only_inc = st.checkbox("Show only Included & Maybe studies (hides Excluded studies)", value=True)

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
        st.info("No Included or Maybe studies yet. Pull papers in Steps 1 & 2 first!")

    for r in records:
        p_val = r["pico_p"] if r["pico_p"] is not None else (r["population_span"] or "")
        i_val = r["pico_i"] if r["pico_i"] is not None else (r["intervention_span"] or "")
        c_val = r["pico_c"] if r["pico_c"] is not None else (r["comparator_span"] or "")
        o_val = r["pico_o"] if r["pico_o"] is not None else (r["outcome_span"] or "")

        with st.expander(f"[{r['final_decision'].upper()}] Paper #{r['record_id']}: {r['title']} ({r['pub_year'] or 'N/A'}) — {r['uncertainty_flags'] or ''}", expanded=True):
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

                if st.form_submit_button("💾 Save PICO Tags & Review Status", type="primary"):
                    save_human_decision(
                        group_id=r["duplicate_group_id"],
                        record_id=r["record_id"],
                        reviewer_name=reviewer_name,
                        screening_decision=new_dec,
                        exclusion_reason=new_reas,
                        reviewer_notes=new_note,
                        pico_p=new_p,
                        pico_i=new_i,
                        pico_c=new_c,
                        pico_o=new_o,
                        action_label="pico_edit"
                    )
                    st.success("Saved verified PICO spans!")
                    st.rerun()


# ==============================================================================
# LEVEL 2: QUERY LOOP, DIFF VIEW & CONFLICT RESOLUTION
# ==============================================================================
elif page == PAGES[6]:
    render_coach_banner(
        "🔄 What is the Level 2 Query-Change Loop?",
        "In real research, you often edit your search query after you have already reviewed several papers. "
        "When you run a new search version in Mini-Rayyan:<br>"
        "1. <b>Your Earlier Work is Safe:</b> Any Include/Exclude decision or PICO edit you already made is automatically preserved.<br>"
        "2. <b>Diff View:</b> Below, you can compare any two search versions to see which papers were <b>Added</b> or <b>Removed</b>.<br>"
        "3. <b>Conflict Resolution:</b> If two papers you previously judged differently (one Included, one Excluded) turn out to be duplicates when a new search merges them, Mini-Rayyan alerts you below!"
    )

    conn = get_connection()
    queries = conn.execute("SELECT * FROM query_versions ORDER BY version_id DESC;").fetchall()
    conflicts = conn.execute("SELECT * FROM duplicate_groups WHERE has_conflict = 1;").fetchall()
    conn.close()

    st.markdown("##### ⚠️ 1. Duplicate Merge Conflict Queue")
    if conflicts:
        st.error(f"Found {len(conflicts)} duplicate group(s) where merged papers had opposing human decisions!")
        for c in conflicts:
            with st.container(border=True):
                st.write(f"**Group #{c['group_id']}:** {c['conflict_details']}")
                if st.button(f"✅ Resolve Conflict for Group #{c['group_id']} (Keep Representative #{c['representative_record_id']})", key=f"res_{c['group_id']}"):
                    resolve_duplicate_conflict(c["group_id"], c["representative_record_id"], reviewer_name)
                    st.success("Conflict resolved!")
                    st.rerun()
    else:
        st.success("✅ Zero conflicts! All human decisions across your duplicate groups are consistent.")

    st.markdown("---")
    st.markdown("##### 🔍 2. Compare Search Versions (Diff View)")
    if len(queries) < 2:
        st.info(
            "You currently have **1** search version. To see the **Diff View** in action, go to **01–02 · Search & Pull Papers ➔ Option B (Instant Offline Demo Pack)** "
            "and click **'Load Pack 2 (Expanded Query v2)'** (or run a second live search)!"
        )
    else:
        q_options = {f"v{q['version_id']}: {q['version_name']} ({q['boolean_query']})": q["version_id"] for q in queries}
        labels = list(q_options.keys())
        c1, c2 = st.columns(2)
        old_lbl = c1.selectbox("Baseline Search Version (Older):", labels, index=min(1, len(labels) - 1))
        new_lbl = c2.selectbox("Updated Search Version (Newer):", labels, index=0)

        diff = compute_query_diff(q_options[old_lbl], q_options[new_lbl])
        m1, m2 = st.columns(2)
        m1.metric("➕ Newly Added Papers in Newer Search", diff["added_count"])
        m2.metric("➖ Papers No Longer Returned", diff["removed_count"])

        if diff["added_records"]:
            st.markdown("**🟢 Newly Added Papers:**")
            st.dataframe(
                pd.DataFrame(diff["added_records"])[["record_id", "source", "pub_year", "title", "authors", "journal"]],
                use_container_width=True, hide_index=True
            )
        if diff["removed_records"]:
            st.markdown("**🔴 Papers From Older Search Not in Newer Search (Still Safely Stored in Database):**")
            st.dataframe(
                pd.DataFrame(diff["removed_records"])[["record_id", "source", "pub_year", "title", "authors", "journal"]],
                use_container_width=True, hide_index=True
            )


# ==============================================================================
# STEP 8: EXPORT CSV & AUDIT LOGS
# ==============================================================================
elif page == PAGES[7]:
    render_coach_banner(
        "📥 Download Your Final Results & Audit Trail",
        "Export your final screened studies and verified PICO tags as a clean <b>CSV spreadsheet</b> for Excel or Google Sheets. "
        "Below that, you can inspect the complete <b>Human Audit Log</b> (every manual override you made) and the <b>Pipeline Run Log</b>."
    )

    conn = get_connection()
    export_rows = conn.execute("""
    SELECT
        r.record_id,
        r.duplicate_group_id,
        r.source,
        r.pmid,
        r.doi,
        r.title,
        r.authors,
        r.pub_year,
        r.journal,
        COALESCE(rd.screening_decision, ms.decision, 'Maybe') AS final_decision,
        CASE WHEN rd.screening_decision IS NOT NULL THEN 'Human Override' ELSE 'Machine Rule' END AS decision_source,
        COALESCE(rd.exclusion_reason, ms.exclusion_reasons, '') AS reason,
        COALESCE(rd.reviewer_notes, '') AS reviewer_notes,
        COALESCE(rd.pico_p, mp.population_span, '') AS population_P,
        COALESCE(rd.pico_i, mp.intervention_span, '') AS intervention_I,
        COALESCE(rd.pico_c, mp.comparator_span, '') AS comparator_C,
        COALESCE(rd.pico_o, mp.outcome_span, '') AS outcome_O,
        rd.reviewer_name,
        rd.updated_at AS last_reviewed_at
    FROM records r
    LEFT JOIN machine_screening ms ON r.record_id = ms.record_id
    LEFT JOIN reviewer_decisions rd ON r.duplicate_group_id = rd.group_id
    LEFT JOIN machine_pico mp ON r.record_id = mp.record_id
    WHERE r.is_hidden_duplicate = 0
    ORDER BY r.record_id ASC;
    """).fetchall()

    df_all = pd.DataFrame([dict(r) for r in export_rows])
    only_inc = st.checkbox("Export only Included studies (uncheck to export all unique studies)", value=True)

    if not df_all.empty:
        df_export = df_all[df_all["final_decision"] == "Include"] if only_inc else df_all
        st.dataframe(df_export, use_container_width=True, hide_index=True)
        st.download_button(
            label=f"📥 Download CSV Spreadsheet ({len(df_export)} Studies)",
            data=df_export.to_csv(index=False).encode("utf-8"),
            file_name="mini_rayyan_included_studies.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.info("No papers available to export yet.")

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
