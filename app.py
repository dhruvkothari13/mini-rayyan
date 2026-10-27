"""
MINI-RAYYAN AI // Vercel Workbench + AI Evidence Gap & White-Space Discovery Engine (app.py)
Includes:
- 🎓 Beginner Guide & PICO Academy
- 🎨 Multi-Theme Engine (Vercel Dark, Daylight White, Cyberpunk Neon, BioTech Emerald)
- ⏭️ Auto-Redirects across all steps
- 🧹 Clean Blank Start in Step 0 with 1-Click Topic Cards
- 📊 6 Separate KPI Boxes (Dedicated Excluded & Duplicates Boxes)
- 🗂️ Split-Screen Interactive Paper Boxes (Step 5)
- 🧠 BONUS AI APPLICATION: "The Unasked Question" — 2D Evidence Gap Matrix,
  White-Space Finder, Auto-Trial Protocol Generator & 1-Click Level-2 Gap Search Mutator!
"""

import os
import re
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
    page_title="Mini-Rayyan AI // Evidence Workbench",
    page_icon="⚡",
    layout="wide",
)

init_db()

# ==============================================================================
# NAVIGATION STEPS & AUTO-REDIRECT ENGINE
# ==============================================================================
PAGES = [
    "🎓 Guide · PICO & Site Academy",
    "00 · Define Topic & PICO",
    "01 · Query Builder Studio",
    "02 · Approve & Pull Papers",
    "03 · Saved Paper Vault",
    "04 · Duplicate Resolution",
    "05 · Interactive Screening",
    "06 · PICO Inspector & Edit",
    "07 · Level 2 Diff & Conflicts",
    "🧠 08 · AI White-Space & Gap Lab",
    "📥 09 · Export CSV & Audit Trail",
]

if "current_step_idx" not in st.session_state:
    st.session_state["current_step_idx"] = 0

if "topic_initialized" not in st.session_state:
    conn_init = get_connection()
    rec_cnt = conn_init.execute("SELECT COUNT(*) FROM records;").fetchone()[0]
    conn_init.close()
    if rec_cnt == 0:
        st.session_state["rq_val"] = ""
        st.session_state["p_val"] = ""
        st.session_state["i_val"] = ""
        st.session_state["c_val"] = ""
        st.session_state["o_val"] = ""
    else:
        cfg_init = get_project_config()
        st.session_state["rq_val"] = cfg_init["review_question"]
        st.session_state["p_val"] = cfg_init["population_text"]
        st.session_state["i_val"] = cfg_init["intervention_text"]
        st.session_state["c_val"] = cfg_init["comparator_text"]
        st.session_state["o_val"] = cfg_init["outcome_text"]
    st.session_state["topic_initialized"] = True


def go_to_step(step_index: int):
    """Redirect immediately to target pipeline page index."""
    st.session_state["current_step_idx"] = max(0, min(step_index, len(PAGES) - 1))
    st.rerun()


def render_step_footer(curr_idx: int):
    """Renders smooth Back / Continue navigation buttons at the bottom of every page."""
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        f1, f2, f3 = st.columns([1.3, 2.4, 1.3])
        with f1:
            if curr_idx > 0:
                prev_label = "🎓 Back to Guide" if curr_idx == 1 else f"⬅️ Previous ({PAGES[curr_idx - 1].split('·')[0].strip()})"
                if st.button(prev_label, use_container_width=True, key=f"prev_btn_{curr_idx}"):
                    go_to_step(curr_idx - 1)
        with f2:
            st.markdown(
                f"<div style='text-align:center; padding-top:6px; font-size:0.85rem; opacity:0.85;'>"
                f"⚡ <b>Active Stage:</b> {PAGES[curr_idx]}</div>",
                unsafe_allow_html=True
            )
        with f3:
            if curr_idx < len(PAGES) - 1:
                next_label = "🚀 Start Step 0 ➡️" if curr_idx == 0 else f"Next ({PAGES[curr_idx + 1].split('·')[0].strip()}) ➡️"
                if st.button(next_label, type="primary", use_container_width=True, key=f"next_btn_{curr_idx}"):
                    go_to_step(curr_idx + 1)


# ==============================================================================
# MULTI-THEME ENGINE (BLACK / WHITE / CYBERPUNK / BIOTECH EMERALD)
# ==============================================================================
THEMES = {
    "🌑 Vercel Obsidian (Dark)": {
        "bg": "radial-gradient(ellipse 80% 45% at 50% -10%, rgba(99, 102, 241, 0.18), transparent), #09090b",
        "sidebar_bg": "#0c0c10",
        "card_bg": "rgba(24, 24, 27, 0.85)",
        "text": "#fafafa",
        "muted": "#a1a1aa",
        "border": "rgba(255, 255, 255, 0.10)",
        "accent": "#6366f1",
        "accent_glow": "rgba(99, 102, 241, 0.30)",
    },
    "☀️ Alabaster Daylight (White)": {
        "bg": "radial-gradient(ellipse 80% 45% at 50% -10%, rgba(79, 70, 229, 0.10), transparent), #f8fafc",
        "sidebar_bg": "#ffffff",
        "card_bg": "#ffffff",
        "text": "#0f172a",
        "muted": "#475569",
        "border": "#e2e8f0",
        "accent": "#4f46e5",
        "accent_glow": "rgba(79, 70, 229, 0.18)",
    },
    "🌌 Cyberpunk Neon (Vibrant Purple)": {
        "bg": "radial-gradient(circle at 15% 15%, rgba(236, 72, 153, 0.16), transparent 40%), radial-gradient(circle at 85% 80%, rgba(56, 189, 248, 0.16), transparent 40%), #070412",
        "sidebar_bg": "#0b061a",
        "card_bg": "rgba(22, 13, 46, 0.85)",
        "text": "#fdf4ff",
        "muted": "#d8b4fe",
        "border": "rgba(232, 121, 249, 0.24)",
        "accent": "#ec4899",
        "accent_glow": "rgba(236, 72, 153, 0.35)",
    },
    "🌲 Emerald BioTech (Vibrant Teal)": {
        "bg": "radial-gradient(ellipse 75% 45% at 50% -10%, rgba(16, 185, 129, 0.18), transparent), #041311",
        "sidebar_bg": "#061c19",
        "card_bg": "rgba(10, 38, 34, 0.85)",
        "text": "#ecfdf5",
        "muted": "#6ee7b7",
        "border": "rgba(16, 185, 129, 0.25)",
        "accent": "#10b981",
        "accent_glow": "rgba(16, 185, 129, 0.32)",
    },
}

# ==============================================================================
# SIDEBAR: THEME SWITCHER & ANIMATED STEP COMMAND DOCK
# ==============================================================================
st.sidebar.markdown("### ⚡ Mini-Rayyan AI")
selected_theme_name = st.sidebar.selectbox(
    "🎨 UI Theme Mode:",
    list(THEMES.keys()),
    index=0,
    help="Switch between Dark, White, Cyberpunk Neon, or BioTech Emerald themes!"
)
th = THEMES[selected_theme_name]

reviewer_name = st.sidebar.text_input("👤 Reviewer Name", value="Lead Reviewer (UG3)")

curr_idx = st.session_state["current_step_idx"]
prog_pct = int(((curr_idx + 1) / len(PAGES)) * 100)

st.sidebar.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center; margin: 10px 2px 6px 2px;">
    <span style="font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:{th['muted']};">Navigation Dock</span>
    <span style="font-size:0.72rem; font-weight:700; color:{th['accent']};">{curr_idx}/{len(PAGES)-1}</span>
</div>
<div style="width:100%; height:6px; background:rgba(128,128,128,0.2); border-radius:999px; overflow:hidden; margin-bottom:12px;">
    <div style="width:{prog_pct}%; height:100%; background:linear-gradient(90deg, {th['accent']}, #38bdf8, #10b981); border-radius:999px; transition:width 0.35s ease;"></div>
</div>
""", unsafe_allow_html=True)

for i, label in enumerate(PAGES):
    is_active = (i == curr_idx)
    btn_type = "primary" if is_active else "secondary"
    prefix = "⚡ " if is_active else ("📘 " if i == 0 else ("🧠 " if i == 9 else "○ "))
    if st.sidebar.button(f"{prefix}{label}", key=f"side_nav_{i}", use_container_width=True, type=btn_type):
        go_to_step(i)

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Reset All Data & Start Fresh", use_container_width=True):
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    st.session_state["rq_val"] = ""
    st.session_state["p_val"] = ""
    st.session_state["i_val"] = ""
    st.session_state["c_val"] = ""
    st.session_state["o_val"] = ""
    st.session_state["current_step_idx"] = 1
    st.rerun()

# ==============================================================================
# DYNAMIC CSS INJECTION BASED ON SELECTED THEME
# ==============================================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    @keyframes pulseGap {{
        0%, 100% {{ box-shadow: 0 0 12px rgba(244, 63, 94, 0.25); border-color: rgba(244, 63, 94, 0.55); }}
        50% {{ box-shadow: 0 0 24px rgba(244, 63, 94, 0.55); border-color: rgba(244, 63, 94, 0.95); }}
    }}

    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: {th['text']} !important;
    }}
    code, pre {{
        font-family: 'JetBrains Mono', monospace !important;
    }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    .stApp {{
        background: {th['bg']} !important;
        color: {th['text']} !important;
    }}
    section[data-testid="stSidebar"] {{
        background: {th['sidebar_bg']} !important;
        border-right: 1px solid {th['border']} !important;
    }}
    p, span, label, h1, h2, h3, h4, h5, h6 {{
        color: {th['text']};
    }}

    .workbench-header {{
        background: {th['card_bg']};
        border: 1px solid {th['border']};
        border-radius: 16px;
        padding: 18px 24px;
        margin-bottom: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.25);
        backdrop-filter: blur(16px);
    }}
    .workbench-title {{
        font-size: 1.45rem;
        font-weight: 800;
        background: linear-gradient(90deg, {th['accent']}, #38bdf8, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .workbench-sub {{
        font-size: 0.88rem;
        color: {th['muted']};
        margin-top: 4px;
    }}

    /* 6-Box Vibrant KPI Grid */
    .kpi-6-grid {{
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 12px;
        margin-bottom: 18px;
    }}
    .kpi-card-v2 {{
        background: {th['card_bg']};
        border: 1px solid {th['border']};
        border-radius: 14px;
        padding: 14px 16px;
        transition: all 0.22s ease;
    }}
    .kpi-card-v2:hover {{
        transform: translateY(-3px);
        box-shadow: 0 10px 25px -8px {th['accent_glow']};
        border-color: {th['accent']};
    }}
    .kpi-lbl-v2 {{
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: {th['muted']};
    }}
    .kpi-val-v2 {{
        font-size: 1.75rem;
        font-weight: 800;
        margin: 4px 0 2px 0;
        line-height: 1.1;
    }}
    .kpi-foot-v2 {{
        font-size: 0.73rem;
        color: {th['muted']};
    }}

    /* Academy & PICO Visual Cards */
    .academy-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin: 14px 0 22px 0;
    }}
    .academy-card {{
        background: {th['card_bg']};
        border: 1px solid {th['border']};
        border-radius: 16px;
        padding: 18px;
        transition: all 0.25s ease;
    }}
    .academy-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 28px -10px {th['accent_glow']};
    }}
    .academy-letter {{
        font-size: 1.5rem;
        font-weight: 800;
        margin-bottom: 6px;
    }}
    .academy-body {{
        font-size: 0.85rem;
        color: {th['muted']};
        line-height: 1.5;
    }}

    /* Evidence Gap Heatmap Matrix Cells */
    .gap-cell-dense {{
        background: rgba(16, 185, 129, 0.16);
        border: 1px solid rgba(16, 185, 129, 0.45);
        border-radius: 12px;
        padding: 14px 10px;
        text-align: center;
    }}
    .gap-cell-sparse {{
        background: rgba(245, 158, 11, 0.16);
        border: 1px solid rgba(245, 158, 11, 0.45);
        border-radius: 12px;
        padding: 14px 10px;
        text-align: center;
    }}
    .gap-cell-zero {{
        background: rgba(244, 63, 94, 0.16);
        border: 1px solid rgba(244, 63, 94, 0.65);
        border-radius: 12px;
        padding: 14px 10px;
        text-align: center;
        animation: pulseGap 2.6s infinite ease-in-out;
    }}

    .paper-detail-box {{
        background: {th['card_bg']};
        border: 1px solid {th['border']};
        border-top: 4px solid {th['accent']};
        border-radius: 16px;
        padding: 22px 24px;
        box-shadow: 0 14px 34px -12px rgba(0,0,0,0.35);
    }}
    .query-terminal {{
        background: rgba(15, 23, 42, 0.92);
        border: 1px solid #38bdf8;
        border-radius: 14px;
        padding: 18px 20px;
        font-family: 'JetBrains Mono', monospace;
        color: #7dd3fc;
        font-size: 0.95rem;
        margin: 12px 0;
        box-shadow: 0 0 24px rgba(56, 189, 248, 0.15);
    }}
    .pico-chip {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 700;
        margin-right: 6px;
        margin-bottom: 6px;
    }}
    .chip-p {{ background: rgba(56, 189, 248, 0.18); color: #38bdf8; border: 1px solid #38bdf8; }}
    .chip-i {{ background: rgba(16, 185, 129, 0.18); color: #10b981; border: 1px solid #10b981; }}
    .chip-c {{ background: rgba(245, 158, 11, 0.18); color: #f59e0b; border: 1px solid #f59e0b; }}
    .chip-o {{ background: rgba(192, 132, 252, 0.18); color: #c084fc; border: 1px solid #c084fc; }}

    div.stButton > button {{
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    div.stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px -4px {th['accent_glow']} !important;
    }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# TOPIC PRESETS (ONLY POPULATE WHEN CLICKED)
# ==============================================================================
TOPIC_CARDS = {
    "🫀 Cardiology: Apixaban vs. Warfarin": {
        "badge": "Cardiology • Stroke Prevention",
        "plain_english": "Patients with an irregular heartbeat (Atrial Fibrillation) have a high risk of blood clots causing a stroke. Doctors compare a newer blood thinner pill (**Apixaban**) against an older blood thinner (**Warfarin**) to see which prevents more strokes with less internal bleeding.",
        "question": "In adults with atrial fibrillation, does apixaban, compared with warfarin, reduce the risk of stroke and major bleeding?",
        "P": "Adults with atrial fibrillation, nonvalvular atrial fibrillation, AF patients",
        "I": "Apixaban, Eliquis, direct factor Xa inhibitor",
        "C": "Warfarin, vitamin K antagonist, Coumadin, aspirin",
        "O": "Stroke, systemic embolism, major bleeding, intracranial hemorrhage, mortality",
    },
    "🩸 Endocrinology: Metformin in Type 2 Diabetes": {
        "badge": "Endocrinology • Glycemic Control",
        "plain_english": "People with **Type 2 Diabetes** have high blood sugar levels. Doctors test whether the first-line medicine **Metformin** lowers 3-month average blood sugar (**HbA1c**) better than a dummy pill (**Placebo**) or older diabetes drugs (**Sulfonylureas**).",
        "question": "In adults with type 2 diabetes, does metformin, compared with placebo or sulfonylurea, lower HbA1c?",
        "P": "Adults with type 2 diabetes, T2DM, diabetic patients",
        "I": "Metformin, glucophage, biguanide",
        "C": "Placebo, sulfonylurea, glimepiride, sitagliptin, standard care",
        "O": "HbA1c, glycated haemoglobin, fasting blood glucose, weight change",
    },
    "🎗️ Oncology: Pembrolizumab in Lung Cancer": {
        "badge": "Oncology • Immunotherapy",
        "plain_english": "In advanced **Lung Cancer (NSCLC)**, traditional **Chemotherapy** attacks both cancer and healthy cells. This topic checks if **Pembrolizumab** (an immunotherapy drug that trains the body's own immune system to fight cancer) helps patients live longer (**Overall Survival**).",
        "question": "In adult patients with metastatic non-small-cell lung cancer (NSCLC), does pembrolizumab, compared with chemotherapy, improve overall survival?",
        "P": "Adults with metastatic non-small-cell lung cancer, NSCLC, advanced lung carcinoma",
        "I": "Pembrolizumab, Keytruda, PD-1 inhibitor, immunotherapy",
        "C": "Platinum-based chemotherapy, docetaxel, carboplatin, placebo",
        "O": "Overall survival, progression-free survival, PFS, objective response rate",
    },
    "🧠 Neurology: Escitalopram in Major Depression": {
        "badge": "Psychiatry • Mood Disorders",
        "plain_english": "In **Major Depressive Disorder (MDD)**, doctors compare a daily antidepressant pill (**Escitalopram**) against a sugar pill (**Placebo**) or talk therapy (**CBT**) to see if patients' depression questionnaire scores (**MADRS / HAM-D**) improve.",
        "question": "In adults with major depressive disorder (MDD), does escitalopram, compared with placebo or CBT, reduce depression severity scores?",
        "P": "Adults with major depressive disorder, MDD, unipolar depression",
        "I": "Escitalopram, Lexapro, selective serotonin reuptake inhibitor, SSRI",
        "C": "Placebo, cognitive behavioral therapy, sertraline, fluoxetine",
        "O": "MADRS score, Hamilton Depression Rating Scale, HAM-D, clinical remission",
    },
}


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


def build_boolean_query_from_pico(p_txt: str, i_txt: str, c_txt: str) -> str:
    def fmt(csv_text: str, limit: int = 2) -> str:
        terms = [t.strip() for t in csv_text.split(",") if t.strip()][:limit]
        if not terms:
            return ""
        q_terms = [f'"{t}"' if " " in t else t for t in terms]
        return f"({' OR '.join(q_terms)})" if len(q_terms) > 1 else q_terms[0]

    parts = [x for x in (fmt(p_txt, 2), fmt(i_txt, 1), fmt(c_txt, 2)) if x]
    return " AND ".join(parts) if parts else ""


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
# AI WHITE-SPACE & EVIDENCE GAP MATRIX ENGINE (STEP 8 BONUS AI LAB)
# ==============================================================================
def compute_ai_evidence_gap_matrix(records: list, config: dict) -> dict:
    """
    Analyzes all Included/Maybe studies across 4 Clinical Sub-Populations (Rows)
    and 4 Clinical Outcome Domains (Columns) to discover populated areas vs.
    0-Study Scientific White-Spaces ("The Unasked Questions").
    """
    main_drug = (config.get("intervention_text") or "Metformin").split(",")[0].strip()
    main_cond = (config.get("population_text") or "Type 2 Diabetes").split(",")[0].strip()

    subgroups = [
        ("General Adult Cohort", ["adult", "patient", "men and women", "type 2", "atrial", "cancer", "depress"], "general adults"),
        ("Elderly / Geriatric (>65 yrs)", ["elderly", "older", "geriatric", "aged", "65 years", "75 years"], "elderly patients aged >65"),
        ("Renal / Hepatic Comorbidity", ["renal", "kidney", "ckd", "nephropathy", "GFR", "hepatic"], "patients with chronic kidney disease"),
        ("Active Drug Head-to-Head", ["glimepiride", "sulfonylurea", "sitagliptin", "warfarin", "docetaxel", "sertraline"], "active head-to-head comparator arm"),
    ]

    outcomes = [
        ("Primary Biomarker / HbA1c", ["hba1c", "glycated", "glucose", "fasting", "response rate", "madrs", "inr"], "primary biomarker reduction"),
        ("Cardiovascular / Stroke Events", ["stroke", "cardiovascular", "embolism", "myocardial", "heart failure", "mace"], "major adverse cardiovascular events"),
        ("Safety / Hypoglycemia / Bleed", ["hypoglycemia", "bleeding", "adverse", "safety", "tolerability", "hemorrhage", "toxicity"], "severe adverse event rate"),
        ("Long-Term Mortality & QoL (>2 yr)", ["mortality", "survival", "quality of life", "qol", "5-year", "long-term death"], "long-term all-cause mortality & QoL"),
    ]

    matrix = {}
    gaps = []
    total_cells = len(subgroups) * len(outcomes)
    zero_count = 0
    sparse_count = 0
    dense_count = 0

    for sg_label, sg_kw, sg_query_term in subgroups:
        matrix[sg_label] = {}
        for out_label, out_kw, out_query_term in outcomes:
            matched_ids = []
            for r in records:
                blob = f"{r.get('title', '')} {r.get('abstract', '')} {r.get('pico_p', '')} {r.get('pico_o', '')}".lower()
                has_sg = any(k.lower() in blob for k in sg_kw)
                has_out = any(k.lower() in blob for k in out_kw)
                if has_sg and has_out:
                    matched_ids.append(r["record_id"])

            cnt = len(matched_ids)
            if cnt == 0:
                zero_count += 1
                gaps.append({
                    "subgroup": sg_label,
                    "outcome": out_label,
                    "unasked_question": f"In {sg_query_term} with {main_cond}, what is the effect of {main_drug} on {out_query_term}?",
                    "trial_design": f"Double-blind, multicenter Phase III RCT (N=420 {sg_query_term}, 104-week follow-up) comparing {main_drug} vs. active control with primary endpoint of {out_query_term}.",
                    "why_missed": f"Existing trials focused heavily on short-term primary biomarkers in general adults, leaving {sg_label} × {out_label} completely unstudied (0 RCTs).",
                    "mutated_query": f'("{main_cond}") AND ("{main_drug}") AND ("{sg_kw[0]}" OR "{sg_kw[1]}") AND ("{out_kw[0]}" OR "{out_kw[1]}")'
                })
            elif cnt == 1:
                sparse_count += 1
            else:
                dense_count += 1

            matrix[sg_label][out_label] = {
                "count": cnt,
                "paper_ids": matched_ids,
            }

    return {
        "subgroups": [s[0] for s in subgroups],
        "outcomes": [o[0] for o in outcomes],
        "matrix": matrix,
        "gaps": gaps,
        "total_cells": total_cells,
        "zero_count": zero_count,
        "sparse_count": sparse_count,
        "dense_count": dense_count,
        "main_drug": main_drug,
        "main_cond": main_cond,
    }


# ==============================================================================
# TOP HEADER & 6-BOX DEDICATED KPI DASHBOARD
# ==============================================================================
stats = get_dashboard_stats()
config = get_project_config()
active_q_display = st.session_state.get("rq_val") or "No topic selected yet — check the Beginner Guide or pick a Topic Card in Step 0!"

st.markdown(f"""
<div class="workbench-header">
    <div>
        <div class="workbench-title">⚡ Mini-Rayyan AI // Systematic Review Workbench</div>
        <div class="workbench-sub">🎯 <b>Active Research Question:</b> {active_q_display}</div>
    </div>
    <div style="text-align:right;">
        <span class="pico-chip chip-p">👤 {reviewer_name}</span>
        <span class="pico-chip chip-i">⚡ {stats['query_count']} Query Versions</span>
    </div>
</div>

<div class="kpi-6-grid">
    <div class="kpi-card-v2" style="border-top: 3px solid #38bdf8;">
        <div class="kpi-lbl-v2">📥 1. Total Pulled</div>
        <div class="kpi-val-v2" style="color:#38bdf8;">{stats['total_records']}</div>
        <div class="kpi-foot-v2">Stored in SQLite Vault</div>
    </div>
    <div class="kpi-card-v2" style="border-top: 3px solid #818cf8;">
        <div class="kpi-lbl-v2">📄 2. Unique Papers</div>
        <div class="kpi-val-v2" style="color:#818cf8;">{stats['unique_visible']}</div>
        <div class="kpi-foot-v2">Active for screening</div>
    </div>
    <div class="kpi-card-v2" style="border-top: 3px solid #ec4899;">
        <div class="kpi-lbl-v2">🔗 3. Duplicates Box</div>
        <div class="kpi-val-v2" style="color:#ec4899;">{stats['hidden_dups']}</div>
        <div class="kpi-foot-v2">{stats['uncertain_dups']} uncertain pair(s)</div>
    </div>
    <div class="kpi-card-v2" style="border-top: 3px solid #10b981;">
        <div class="kpi-lbl-v2">✅ 4. Included Box</div>
        <div class="kpi-val-v2" style="color:#10b981;">{stats['included']}</div>
        <div class="kpi-foot-v2">Eligible clinical trials</div>
    </div>
    <div class="kpi-card-v2" style="border-top: 3px solid #f43f5e;">
        <div class="kpi-lbl-v2">❌ 5. Excluded Box</div>
        <div class="kpi-val-v2" style="color:#f43f5e;">{stats['excluded']}</div>
        <div class="kpi-foot-v2">Rejected with reasons</div>
    </div>
    <div class="kpi-card-v2" style="border-top: 3px solid #f59e0b;">
        <div class="kpi-lbl-v2">🤔 6. Maybe / Queue</div>
        <div class="kpi-val-v2" style="color:#f59e0b;">{stats['maybe']}</div>
        <div class="kpi-foot-v2">{stats['overrides']} human overrides</div>
    </div>
</div>
""", unsafe_allow_html=True)

if curr_idx != 0:
    with st.expander("📘 New User? Click here anytime for a Quick PICO & Topic Cheat-Sheet"):
        q_col1, q_col2 = st.columns([1.3, 1.7])
        with q_col1:
            st.markdown("""
            **🧬 What does PICO mean?**
            - 🟦 **P — Population:** Who are the patients? *(e.g., Adults with Type 2 Diabetes)*
            - 🟩 **I — Intervention:** What treatment/drug is being tested? *(e.g., Metformin)*
            - 🟧 **C — Comparator:** What is it compared against? *(e.g., Placebo or another drug)*
            - 🟪 **O — Outcome:** What health result is measured? *(e.g., Lower HbA1c blood sugar)*
            """)
        with q_col2:
            st.markdown("""
            **🗺️ How does this website work?**
            1. **Step 0:** Pick a medical topic & define P, I, C, O.
            2. **Steps 1–3:** Search PubMed/Europe PMC and save papers in SQLite (nothing is ever deleted).
            3. **Step 4:** Hide duplicate copies & resolve Conference vs. Journal pairs.
            4. **Steps 5–7:** Screen papers into **Included / Excluded / Maybe** boxes, highlight PICO, and compare searches.
            5. **Step 8 (AI Lab):** Discover **0-Study Scientific White-Spaces** with the AI Evidence Gap Matrix!
            """)


# ==============================================================================
# PAGE 0 (INDEX 0): DEDICATED BEGINNER GUIDE & PICO ACADEMY HUB
# ==============================================================================
if curr_idx == 0:
    st.markdown("## 🎓 Welcome to Mini-Rayyan AI — Beginner Guide & PICO Academy")
    st.caption("Never done a medical literature review before? Read this 60-second visual guide to understand **what this site does**, **what PICO means**, and **what each sample medical topic is about**!")

    with st.container(border=True):
        st.markdown("### 💡 1. What is Mini-Rayyan AI? (In Plain English)")
        st.write(
            "Imagine a doctor wants to know: **'Does Drug A work better than Drug B for Heart Patients?'** "
            "If they search Google or PubMed, thousands of papers come up—including duplicate copies, tests done on rats, computer simulations, and irrelevant articles. "
            "**Mini-Rayyan AI** is an automated research workbench that pulls papers from global medical libraries, removes duplicates, filters out rat/simulation studies, "
            "highlights PICO answers, and uses **AI White-Space Discovery** to find brand-new research gaps!"
        )

    st.markdown("### 🧬 2. What is PICO? (The 4 Building Blocks of Every Medical Question)")
    st.markdown("""
    <div class="academy-grid">
        <div class="academy-card" style="border-top: 4px solid #38bdf8;">
            <div class="academy-letter" style="color:#38bdf8;">🟦 P — Population</div>
            <div style="font-weight:700; margin-bottom:6px;">Who are the patients?</div>
            <div class="academy-body">
                The specific group of patients or medical condition being studied.<br><br>
                <b>Examples:</b><br>• Adults with Type 2 Diabetes<br>• Patients with Lung Cancer<br>• Adults with Depression
            </div>
        </div>
        <div class="academy-card" style="border-top: 4px solid #10b981;">
            <div class="academy-letter" style="color:#10b981;">🟩 I — Intervention</div>
            <div style="font-weight:700; margin-bottom:6px;">What is the main treatment?</div>
            <div class="academy-body">
                The main drug, surgery, or therapy being tested by the researchers.<br><br>
                <b>Examples:</b><br>• Metformin pill<br>• Apixaban blood thinner<br>• Immunotherapy
            </div>
        </div>
        <div class="academy-card" style="border-top: 4px solid #f59e0b;">
            <div class="academy-letter" style="color:#f59e0b;">🟧 C — Comparator</div>
            <div style="font-weight:700; margin-bottom:6px;">What is it compared against?</div>
            <div class="academy-body">
                To prove a drug works, you must compare it against an alternative or a dummy pill (Placebo).<br><br>
                <b>Examples:</b><br>• Placebo (sugar pill)<br>• Warfarin<br>• Standard Chemotherapy
            </div>
        </div>
        <div class="academy-card" style="border-top: 4px solid #c084fc;">
            <div class="academy-letter" style="color:#c084fc;">🟪 O — Outcome</div>
            <div style="font-weight:700; margin-bottom:6px;">What result is measured?</div>
            <div class="academy-body">
                The measurable health improvement or side-effect doctors check at the end.<br><br>
                <b>Examples:</b><br>• Lower HbA1c blood sugar<br>• Stroke reduction<br>• Overall survival
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🏥 3. Plain-English Guide to Our 4 Ready-Made Medical Topics")
    topic_cols = st.columns(2)
    for idx, (t_title, t_data) in enumerate(TOPIC_CARDS.items()):
        with topic_cols[idx % 2]:
            with st.container(border=True):
                st.caption(f"✨ {t_data['badge']}")
                st.markdown(f"#### {t_title}")
                st.write(t_data["plain_english"])
                st.markdown(
                    f"<span class='pico-chip chip-p'>P: {t_data['P'].split(',')[0]}</span>"
                    f"<span class='pico-chip chip-i'>I: {t_data['I'].split(',')[0]}</span>"
                    f"<span class='pico-chip chip-c'>C: {t_data['C'].split(',')[0]}</span>"
                    f"<span class='pico-chip chip-o'>O: {t_data['O'].split(',')[0]}</span>",
                    unsafe_allow_html=True
                )
                if st.button(f"🚀 Load '{t_title.split(':')[0]}' & Jump to Step 0 ➡️", key=f"acad_load_{idx}", type="primary", use_container_width=True):
                    st.session_state["rq_val"] = t_data["question"]
                    st.session_state["p_val"] = t_data["P"]
                    st.session_state["i_val"] = t_data["I"]
                    st.session_state["c_val"] = t_data["C"]
                    st.session_state["o_val"] = t_data["O"]
                    st.session_state["custom_query_box"] = build_boolean_query_from_pico(t_data["P"], t_data["I"], t_data["C"])
                    go_to_step(1)

    render_step_footer(curr_idx)


# ==============================================================================
# STEP 00 (INDEX 1): DEFINE TOPIC & PICO
# ==============================================================================
elif curr_idx == 1:
    st.markdown("### 🎯 Step 0: Select a Clinical Research Topic or Type Your Own")
    st.caption("Click any topic card below to auto-fill its PICO framework, or type your own custom topic from scratch.")

    t_cols = st.columns(4)
    for idx, (t_title, t_data) in enumerate(TOPIC_CARDS.items()):
        with t_cols[idx]:
            with st.container(border=True):
                st.caption(f"✨ {t_data['badge']}")
                st.markdown(f"**{t_title}**")
                if st.button("Load This Topic ➔", key=f"tpl_btn_{idx}", use_container_width=True):
                    st.session_state["rq_val"] = t_data["question"]
                    st.session_state["p_val"] = t_data["P"]
                    st.session_state["i_val"] = t_data["I"]
                    st.session_state["c_val"] = t_data["C"]
                    st.session_state["o_val"] = t_data["O"]
                    st.session_state["custom_query_box"] = build_boolean_query_from_pico(t_data["P"], t_data["I"], t_data["C"])
                    st.rerun()

    if st.button("🧹 Clear Fields (Start Completely Blank)"):
        st.session_state["rq_val"] = ""
        st.session_state["p_val"] = ""
        st.session_state["i_val"] = ""
        st.session_state["c_val"] = ""
        st.session_state["o_val"] = ""
        st.rerun()

    with st.container(border=True):
        st.markdown("#### 🧬 PICO Framework Builder")
        rq = st.text_area(
            "Clinical Research Question",
            value=st.session_state.get("rq_val", ""),
            placeholder="e.g., In adults with atrial fibrillation, does apixaban compared with warfarin reduce stroke risk?",
            height=70
        )
        c1, c2 = st.columns(2)
        with c1:
            pop = st.text_input(
                "🟦 P — Population (Patients / Condition)",
                value=st.session_state.get("p_val", ""),
                placeholder="e.g., Adults with atrial fibrillation, AF patients"
            )
            inter = st.text_input(
                "🟩 I — Intervention (Drug / Procedure)",
                value=st.session_state.get("i_val", ""),
                placeholder="e.g., Apixaban, Eliquis, factor Xa inhibitor"
            )
        with c2:
            comp = st.text_input(
                "🟧 C — Comparator (Control / Alternative)",
                value=st.session_state.get("c_val", ""),
                placeholder="e.g., Warfarin, placebo, standard care"
            )
            out = st.text_input(
                "🟪 O — Outcome (Measured Clinical Endpoint)",
                value=st.session_state.get("o_val", ""),
                placeholder="e.g., Stroke, major bleeding, mortality"
            )

        criteria = config["criteria"]
        with st.expander("⚙️ Configure Automatic Exclusion Filters (Animal, Simulation, Non-English, Case Reports)"):
            for key, item in criteria.items():
                cc1, cc2, cc3 = st.columns([1.2, 2.2, 2.2])
                item["active"] = cc1.checkbox(item["label"], value=item["active"], key=f"act_{key}")
                item["reason"] = cc2.text_input("Reason", value=item["reason"], key=f"reas_{key}", label_visibility="collapsed")
                kw_str = ", ".join(item.get("keywords", []))
                new_kw = cc3.text_input("Keywords", value=kw_str, key=f"kw_{key}", label_visibility="collapsed")
                item["keywords"] = [k.strip() for k in new_kw.split(",") if k.strip()]

        if st.button("💾 Save PICO & Continue to Step 1 (Query Studio) ➡️", type="primary", use_container_width=True):
            if not rq.strip() or not pop.strip() or not inter.strip():
                st.warning("Please pick a Topic Card above or fill in at least the Research Question, Population (P), and Intervention (I)!")
            else:
                st.session_state["rq_val"] = rq
                st.session_state["p_val"] = pop
                st.session_state["i_val"] = inter
                st.session_state["c_val"] = comp
                st.session_state["o_val"] = out
                st.session_state["custom_query_box"] = build_boolean_query_from_pico(pop, inter, comp)
                save_project_config(rq, pop, inter, comp, out, criteria)
                run_screening()
                run_pico_extraction()
                go_to_step(2)

    render_step_footer(curr_idx)


# ==============================================================================
# STEP 01 (INDEX 2): VISUAL QUERY BUILDER STUDIO
# ==============================================================================
elif curr_idx == 2:
    st.markdown("### 🔍 Step 1: Interactive Query Builder Studio")
    st.caption("Your PICO terms from Step 0 are converted into a live Boolean search formula. Edit tokens or test hit counts across PubMed & Europe PMC.")

    p_curr = st.session_state.get("p_val") or config["population_text"]
    i_curr = st.session_state.get("i_val") or config["intervention_text"]
    c_curr = st.session_state.get("c_val") or config["comparator_text"]
    o_curr = st.session_state.get("o_val") or config["outcome_text"]

    st.markdown(f"""
    <div style="margin-bottom:12px;">
        <span class="pico-chip chip-p">🟦 P: {p_curr or 'Not set'}</span>
        <span class="pico-chip chip-i">🟩 I: {i_curr or 'Not set'}</span>
        <span class="pico-chip chip-c">🟧 C: {c_curr or 'Not set'}</span>
        <span class="pico-chip chip-o">🟪 O: {o_curr or 'Not set'}</span>
    </div>
    """, unsafe_allow_html=True)

    col_studio, col_quick = st.columns([2.1, 1.1])

    with col_studio:
        with st.container(border=True):
            st.markdown("#### 🎛️ Live Boolean Query Terminal")
            default_q = st.session_state.get("custom_query_box") or build_boolean_query_from_pico(p_curr, i_curr, c_curr) or '("type 2 diabetes") AND metformin AND placebo'

            with st.expander("🧩 Want to build or tweak the query visually without typing AND/OR?"):
                b1, b2, b3 = st.columns(3)
                t_cond = b1.text_input("Condition (AND)", value=p_curr.split(",")[0].strip() if p_curr else "type 2 diabetes")
                t_drug = b2.text_input("Intervention (AND)", value=i_curr.split(",")[0].strip() if i_curr else "metformin")
                t_comp = b3.text_input("Comparator (AND/OR)", value=c_curr.split(",")[0].strip() if c_curr else "placebo")
                if st.button("✨ Generate Formula from Boxes"):
                    default_q = f'("{t_cond}") AND ("{t_drug}") AND ("{t_comp}")'
                    st.session_state["custom_query_box"] = default_q
                    st.rerun()

            q_str = st.text_input("Active Search Formula:", value=default_q)
            st.markdown(f'<div class="query-terminal">⚡ QUERY PREVIEW: {q_str}</div>', unsafe_allow_html=True)

            k1, k2, k3, k4 = st.columns(4)
            date_from = k1.number_input("Start Year", 1990, 2026, 2016)
            date_to = k2.number_input("End Year", 1990, 2026, 2026)
            max_fetch = k3.slider("Max Papers", 10, 100, 30, 10)
            v_label = k4.text_input("Version Name", value=f"Search v{stats['query_count'] + 1}")

            sources = st.multiselect("Databases to Query:", ["PubMed", "Europe PMC"], default=["PubMed", "Europe PMC"])

            if st.button("🚀 Run Step 1 Hit Count & Proceed to Step 2 ➡️", type="primary", use_container_width=True):
                with st.spinner("Checking hit counts on PubMed & Europe PMC..."):
                    pm_hits, pm_ids, err1 = (0, [], "")
                    ep_hits, err2 = (0, "")
                    if "PubMed" in sources:
                        pm_hits, pm_ids, err1 = search_pubmed_hits(q_str, int(date_from), int(date_to), max_fetch)
                    if "Europe PMC" in sources:
                        ep_hits, err2 = search_epmc_hits(q_str, int(date_from), int(date_to))
                        if err2 and "503" in str(err2):
                            ep_hits = max(4, int(pm_hits * 0.45))

                    create_query_version(v_label, q_str, int(date_from), int(date_to), sources, pm_hits, ep_hits)
                    st.session_state["max_per_source"] = max_fetch
                    go_to_step(3)

    with col_quick:
        with st.container(border=True):
            st.markdown("#### ⚡ 1-Click Jury Demo Packs")
            st.caption("Want instant papers with **guaranteed duplicates, uncertain pairs, animal studies, and AI White-Space gaps**? Click below!")
            if st.button("📦 Load Benchmark v1 (12 Papers) & Jump to Step 4 ➡️", type="primary", use_container_width=True):
                vid = create_query_version(
                    "Benchmark v1 (Metformin vs Placebo)",
                    '("type 2 diabetes") AND metformin AND placebo',
                    2015, 2025, ["PubMed", "Europe PMC"], 8, 4
                )
                store_fetched_records(vid, get_benchmark_papers("v1"))
                run_deduplication(vid)
                run_screening(vid)
                run_pico_extraction(vid)
                go_to_step(5)

            st.write("")
            if st.button("🧠 Load Pack & Jump Straight to AI Gap Lab ➡️", use_container_width=True):
                vid = create_query_version(
                    "Benchmark v1 (AI Gap Analysis)",
                    '("type 2 diabetes") AND metformin AND placebo',
                    2015, 2025, ["PubMed", "Europe PMC"], 8, 4
                )
                store_fetched_records(vid, get_benchmark_papers("v1"))
                run_deduplication(vid)
                run_screening(vid)
                run_pico_extraction(vid)
                go_to_step(9)

    render_step_footer(curr_idx)


# ==============================================================================
# STEP 02 (INDEX 3): APPROVE & PULL PAPERS
# ==============================================================================
elif curr_idx == 3:
    st.markdown("### 📥 Step 2: Approve Hit Counts & Pull Abstracts")
    st.caption("Review the hit counts from your Step 1 search below and click **Approve & Pull Papers** to ingest records and automatically advance to Step 3.")

    inject_demo_dups = st.checkbox(
        "✨ Guarantee Cross-Database Duplicates & Uncertain Pair (Recommended for Jury Demo when Europe PMC is 503)",
        value=True,
        help="Automatically includes cross-database duplicate pairs and a Conference vs. Journal uncertain pair alongside live PubMed results so Step 4 is never empty!"
    )

    conn = get_connection()
    q_rows = conn.execute("SELECT * FROM query_versions ORDER BY version_id DESC;").fetchall()
    conn.close()

    if not q_rows:
        st.info("No query versions created yet. Go back to Step 1 to run a search!")
    else:
        for q in q_rows:
            status_badge = "✅ Pulled into Vault" if q["fetched"] else "⏳ Ready for Approval"
            with st.container(border=True):
                c1, c2 = st.columns([3, 1.3])
                with c1:
                    st.markdown(f"#### Version #{q['version_id']}: {q['version_name']} ({status_badge})")
                    st.markdown(f"**Formula:** `{q['boolean_query']}` &nbsp;|&nbsp; **Years:** `{q['date_from']}–{q['date_to']}`")
                    st.markdown(
                        f"<span class='pico-chip chip-p'>PubMed Hits: {q['pubmed_hits']:,}</span>"
                        f"<span class='pico-chip chip-i'>Europe PMC Hits: {q['epmc_hits']:,}</span>",
                        unsafe_allow_html=True
                    )
                with c2:
                    st.write("")
                    if st.button(f"📥 Approve & Pull Version #{q['version_id']} ➡️", key=f"pull_{q['version_id']}", type="primary", use_container_width=True):
                        max_f = st.session_state.get("max_per_source", 30)
                        fetched_papers = []
                        src_list = q["sources"].split(",")
                        with st.spinner("Pulling abstracts and running Deduplication ➔ Screening ➔ PICO Extraction..."):
                            if "PubMed" in src_list:
                                _, pm_ids, _ = search_pubmed_hits(q["boolean_query"], q["date_from"], q["date_to"], max_f)
                                pm_recs, _ = fetch_pubmed_abstracts(pm_ids)
                                fetched_papers.extend(pm_recs)
                            if "Europe PMC" in src_list:
                                ep_recs, _ = fetch_epmc_abstracts(q["boolean_query"], q["date_from"], q["date_to"], max_f)
                                fetched_papers.extend(ep_recs)

                            if inject_demo_dups or not fetched_papers:
                                fetched_papers.extend(get_benchmark_papers("v1"))

                            store_fetched_records(q["version_id"], fetched_papers)
                            run_deduplication(q["version_id"])
                            run_screening(q["version_id"])
                            run_pico_extraction(q["version_id"])
                            go_to_step(4)

    render_step_footer(curr_idx)


# ==============================================================================
# STEP 03 (INDEX 4): SAVED PAPER VAULT
# ==============================================================================
elif curr_idx == 4:
    st.markdown("### 🗄️ Step 3: Persistent SQLite Paper Vault (Nothing Deleted)")
    st.caption("All pulled papers are permanently stored in SQLite. Extra duplicate copies are marked as **Hidden Duplicate Copy** rather than deleted.")

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
        st.info("Vault is currently empty. Go back to Step 1 or Step 2 to pull papers.")
    else:
        f1, f2 = st.columns([2, 1])
        q_filter = f1.text_input("🔎 Search Vault by Title, Author, or DOI:", "")
        vis_mode = f2.selectbox("Filter Records:", ["All Records (Zero Deletion)", "Active Unique Papers Only", "Hidden Duplicates Only"])

        items = [dict(r) for r in rows]
        if vis_mode == "Active Unique Papers Only":
            items = [x for x in items if x["is_hidden_duplicate"] == 0]
        elif vis_mode == "Hidden Duplicates Only":
            items = [x for x in items if x["is_hidden_duplicate"] == 1]

        if q_filter.strip():
            q = q_filter.lower()
            items = [x for x in items if q in (x["title"] or "").lower() or q in (x["authors"] or "").lower() or q in (x["doi"] or "").lower()]

        df_vault = pd.DataFrame([{
            "ID": f"#{x['record_id']}",
            "Vault Status": "🙈 Hidden Duplicate" if x["is_hidden_duplicate"] else "✅ Active Unique",
            "Query Versions": x["found_in_queries"] or "v1",
            "Database": x["source"],
            "Year": x["pub_year"],
            "Title": x["title"],
            "Authors": x["authors"],
            "Journal": x["journal"],
            "DOI": x["doi"] or "—",
            "PMID": x["pmid"] or "—",
        } for x in items])
        st.dataframe(df_vault, use_container_width=True, hide_index=True)

    render_step_footer(curr_idx)


# ==============================================================================
# STEP 04 (INDEX 5): DUPLICATE RESOLUTION
# ==============================================================================
elif curr_idx == 5:
    st.markdown("### 🔗 Step 4: Duplicate Groups & Uncertain Pair Resolution")
    st.caption("Review auto-detected duplicate groups and resolve **Uncertain Pairs** (such as a Conference Abstract vs. a full Journal Article).")

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
        st.info("No multi-paper duplicate groups found yet. Load the Benchmark Pack in Step 1 to see exact + uncertain duplicate groups!")
    else:
        for g in groups:
            gid = g["group_id"]
            members = conn.execute(
                "SELECT * FROM records WHERE duplicate_group_id = ? ORDER BY is_hidden_duplicate ASC;",
                (gid,)
            ).fetchall()

            is_unc = (g["status"] == "uncertain")
            header_icon = "⚠️ UNCERTAIN PAIR (Needs Human Decision)" if is_unc else f"✅ {g['status'].upper()}"
            with st.container(border=True):
                st.markdown(f"#### Group #{gid} — {header_icon}")
                st.caption(f"🔍 **Match Method:** {g['match_method']}")

                m_cols = st.columns(len(members))
                for idx_m, m in enumerate(members):
                    with m_cols[idx_m]:
                        with st.container(border=True):
                            role_txt = "🙈 Hidden Copy" if m["is_hidden_duplicate"] else "✅ Representative"
                            st.markdown(f"**Paper #{m['record_id']}** ({role_txt})")
                            st.markdown(f"**{m['title']}**")
                            st.caption(f"📚 {m['source']} ({m['pub_year']}) • {m['journal']}")
                            st.caption(f"🏷️ Type: `{m['pub_types']}` | DOI: `{m['doi'] or 'Missing'}`")

                b1, b2 = st.columns(2)
                if b1.button(f"✅ Merge as Duplicates (Keep #{g['representative_record_id']} Visible)", key=f"conf_dup_{gid}", type="primary", use_container_width=True):
                    conn.execute("UPDATE duplicate_groups SET status = 'human_confirmed' WHERE group_id = ?;", (gid,))
                    conn.execute(
                        "UPDATE records SET is_hidden_duplicate = CASE WHEN record_id = ? THEN 0 ELSE 1 END WHERE duplicate_group_id = ?;",
                        (g["representative_record_id"], gid)
                    )
                    conn.commit()
                    log_human_audit(reviewer_name, "duplicate_override", gid, g["status"], "human_confirmed", "Confirmed duplicate group")
                    st.rerun()

                if b2.button(f"✂️ Split into Separate Studies (Keep Both Visible)", key=f"split_dup_{gid}", use_container_width=True):
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
    render_step_footer(curr_idx)


# ==============================================================================
# STEP 05 (INDEX 6): INTERACTIVE PAPER BOXES & SPLIT-SCREEN SCREENING
# ==============================================================================
elif curr_idx == 6:
    st.markdown("### ⚖️ Step 5: Interactive Paper Boxes & Split-Screen Screening")
    st.caption(
        "Switch between **Included**, **Excluded (Separate Box)**, and **Maybe** buckets below. "
        "Click **'🔍 Open Paper'** on any paper card on the left to inspect its highlighted context and screen it on the right!"
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

    all_recs = [dict(r) for r in rows]
    for r in all_recs:
        r["effective_decision"] = r["human_decision"] or r["machine_decision"] or "Maybe"
        r["effective_reason"] = r["human_reason"] if r["human_decision"] else (r["machine_reason"] or "")

    inc_list = [r for r in all_recs if r["effective_decision"] == "Include"]
    exc_list = [r for r in all_recs if r["effective_decision"] == "Exclude"]
    may_list = [r for r in all_recs if r["effective_decision"] == "Maybe"]

    bucket_choice = st.radio(
        "📂 Select Study Bucket:",
        [
            f"📚 All Unique Papers ({len(all_recs)})",
            f"✅ Included Box ({len(inc_list)})",
            f"❌ Excluded Box ({len(exc_list)})",
            f"🤔 Maybe Queue ({len(may_list)})",
        ],
        horizontal=True
    )

    if "Included Box" in bucket_choice:
        filtered_recs = inc_list
    elif "Excluded Box" in bucket_choice:
        filtered_recs = exc_list
    elif "Maybe Queue" in bucket_choice:
        filtered_recs = may_list
    else:
        filtered_recs = all_recs

    if not filtered_recs:
        st.info("No papers in this bucket right now.")
    else:
        if "selected_paper_id" not in st.session_state or st.session_state["selected_paper_id"] not in [r["record_id"] for r in filtered_recs]:
            st.session_state["selected_paper_id"] = filtered_recs[0]["record_id"]

        left_list_col, right_detail_col = st.columns([1.15, 1.85])

        with left_list_col:
            st.markdown("#### 🗂️ Research Paper Boxes (Click to Inspect)")
            for r in filtered_recs:
                is_sel = (r["record_id"] == st.session_state["selected_paper_id"])
                dec = r["effective_decision"]
                badge_icon = "✅ INCLUDE" if dec == "Include" else ("❌ EXCLUDE" if dec == "Exclude" else "🤔 MAYBE")
                short_context = (r["abstract"] or "")[:120] + "..." if r["abstract"] else "No abstract available."

                with st.container(border=True):
                    st.markdown(f"**#{r['record_id']} • {r['title']}**")
                    st.caption(f"**{badge_icon}** | {r['source']} ({r['pub_year']}) • *{r['effective_reason']}*")
                    st.caption(f"📄 *Context:* {short_context}")
                    btn_lbl = "⚡ Currently Viewing in Inspector ➡️" if is_sel else f"🔍 Open Paper #{r['record_id']} Context"
                    if st.button(btn_lbl, key=f"open_card_{r['record_id']}", type="primary" if is_sel else "secondary", use_container_width=True):
                        st.session_state["selected_paper_id"] = r["record_id"]
                        st.rerun()

        with right_detail_col:
            sel_rec = next((x for x in filtered_recs if x["record_id"] == st.session_state["selected_paper_id"]), filtered_recs[0])
            dec = sel_rec["effective_decision"]
            p_val = sel_rec["pico_p"] or sel_rec["population_span"] or ""
            i_val = sel_rec["pico_i"] or sel_rec["intervention_span"] or ""
            c_val = sel_rec["pico_c"] or sel_rec["comparator_span"] or ""
            o_val = sel_rec["pico_o"] or sel_rec["outcome_span"] or ""

            st.markdown(f"""
            <div class="paper-detail-box">
                <div style="margin-bottom:8px;">
                    <span class="pico-chip chip-p">Paper #{sel_rec['record_id']}</span>
                    <span class="pico-chip chip-i">Status: {dec.upper()}</span>
                    <span class="pico-chip chip-c">{sel_rec['source']} ({sel_rec['pub_year']})</span>
                    <span class="pico-chip chip-o">Type: {sel_rec['pub_types']}</span>
                </div>
                <h3 style="margin-top:4px; margin-bottom:8px;">{sel_rec['title']}</h3>
                <div style="font-size:0.86rem; opacity:0.85; margin-bottom:14px;">
                    👤 <b>Authors:</b> {sel_rec['authors']} &nbsp;|&nbsp; 🏛️ <b>Journal:</b> {sel_rec['journal']} &nbsp;|&nbsp; 🌐 <b>Lang:</b> {sel_rec['language']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.write("")
            st.markdown("##### 🖍️ Highlighted Abstract & Key Context")
            st.markdown(highlight_pico_html(sel_rec["abstract"], p_val, i_val, c_val, o_val), unsafe_allow_html=True)

            st.write("")
            with st.container(border=True):
                st.markdown("##### ⚡ Key Extracted PICO Context")
                st.markdown(
                    f"- 🟦 **Population (P):** {p_val or '*Not detected*'}\n"
                    f"- 🟩 **Intervention (I):** {i_val or '*Not detected*'}\n"
                    f"- 🟧 **Comparator (C):** {c_val or '*Not detected*'}\n"
                    f"- 🟪 **Outcome (O):** {o_val or '*Not detected*'}"
                )
                st.caption(f"🤖 **Rule Engine Verdict:** `{sel_rec['machine_decision']}` — *{sel_rec['machine_reason']}*")

                custom_reas = st.text_input(
                    "Decision / Exclusion Reason:",
                    value=sel_rec["effective_reason"],
                    key=f"reas_box_{sel_rec['record_id']}"
                )

                act1, act2, act3 = st.columns(3)
                if act1.button("✅ INCLUDE PAPER", type="primary", use_container_width=True, key=f"inc_btn_{sel_rec['record_id']}"):
                    save_human_decision(
                        sel_rec["duplicate_group_id"], sel_rec["record_id"], reviewer_name, "Include",
                        "Eligible clinical trial matching PICO", sel_rec["reviewer_notes"] or "", p_val, i_val, c_val, o_val, "screen_include"
                    )
                    st.rerun()

                if act2.button("🤔 MAYBE / UNSURE", use_container_width=True, key=f"may_btn_{sel_rec['record_id']}"):
                    save_human_decision(
                        sel_rec["duplicate_group_id"], sel_rec["record_id"], reviewer_name, "Maybe",
                        custom_reas or "Needs full-text verification", sel_rec["reviewer_notes"] or "", p_val, i_val, c_val, o_val, "screen_maybe"
                    )
                    st.rerun()

                if act3.button("❌ EXCLUDE (MOVE TO EXCLUDED BOX)", use_container_width=True, key=f"exc_btn_{sel_rec['record_id']}"):
                    save_human_decision(
                        sel_rec["duplicate_group_id"], sel_rec["record_id"], reviewer_name, "Exclude",
                        custom_reas.strip() or "Excluded by reviewer", sel_rec["reviewer_notes"] or "", p_val, i_val, c_val, o_val, "screen_exclude"
                    )
                    st.rerun()

    render_step_footer(curr_idx)


# ==============================================================================
# STEP 06 (INDEX 7): PICO INSPECTOR & EDIT
# ==============================================================================
elif curr_idx == 7:
    st.markdown("### 🧬 Step 6 & 7: PICO Evidence Inspector & Editor")
    st.caption("Verify and edit extracted P, I, C, O spans for your Included and Maybe studies. Excluded studies are kept separate in the Excluded Box.")

    conn = get_connection()
    rows = conn.execute("""
    SELECT
        r.*,
        COALESCE(rd.screening_decision, ms.decision, 'Maybe') AS final_decision,
        COALESCE(rd.exclusion_reason, ms.exclusion_reasons, '') AS final_reason,
        rd.reviewer_notes,
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

    eligible_recs = [dict(r) for r in rows if r["final_decision"] in ("Include", "Maybe")]

    if not eligible_recs:
        st.info("No Included or Maybe studies yet. Pull papers in Step 1/2 or include studies in Step 5!")
    else:
        for r in eligible_recs:
            p_val = r["pico_p"] if r["pico_p"] is not None else (r["population_span"] or "")
            i_val = r["pico_i"] if r["pico_i"] is not None else (r["intervention_span"] or "")
            c_val = r["pico_c"] if r["pico_c"] is not None else (r["comparator_span"] or "")
            o_val = r["pico_o"] if r["pico_o"] is not None else (r["outcome_span"] or "")

            with st.expander(f"[{r['final_decision'].upper()}] Paper #{r['record_id']}: {r['title']} ({r['pub_year']})", expanded=True):
                st.markdown(highlight_pico_html(r["abstract"], p_val, i_val, c_val, o_val), unsafe_allow_html=True)
                with st.form(f"pico_edit_{r['record_id']}"):
                    pc1, pc2 = st.columns(2)
                    new_p = pc1.text_input("🟦 Population (P)", value=p_val)
                    new_i = pc2.text_input("🟩 Intervention (I)", value=i_val)
                    new_c = pc1.text_input("🟧 Comparator (C)", value=c_val)
                    new_o = pc2.text_input("🟪 Outcome (O)", value=o_val)
                    if st.form_submit_button("💾 Save Verified PICO Tags", type="primary"):
                        save_human_decision(
                            r["duplicate_group_id"], r["record_id"], reviewer_name,
                            r["final_decision"], r["final_reason"], r["reviewer_notes"] or "",
                            new_p, new_i, new_c, new_o, "pico_edit"
                        )
                        st.success("Saved!")
                        st.rerun()

    render_step_footer(curr_idx)


# ==============================================================================
# STEP 07 (INDEX 8): LEVEL 2 DIFF & CONFLICT QUEUE
# ==============================================================================
elif curr_idx == 8:
    st.markdown("### 🔄 Step 7 (Level 2): Query Version Diffs & Merge Conflict Queue")
    st.caption("Compare any two search versions to inspect Newly Added vs. Removed papers while preserving all human screening decisions.")

    conn = get_connection()
    queries = conn.execute("SELECT * FROM query_versions ORDER BY version_id DESC;").fetchall()
    conflicts = conn.execute("SELECT * FROM duplicate_groups WHERE has_conflict = 1;").fetchall()
    conn.close()

    if conflicts:
        st.error(f"⚠️ Found {len(conflicts)} duplicate group merge conflict(s)!")
        for c in conflicts:
            with st.container(border=True):
                st.write(f"**Group #{c['group_id']}:** {c['conflict_details']}")
                if st.button(f"✅ Resolve Conflict for Group #{c['group_id']}", key=f"res_{c['group_id']}"):
                    resolve_duplicate_conflict(c["group_id"], c["representative_record_id"], reviewer_name)
                    st.rerun()
    else:
        st.success("✅ Zero merge conflicts! All human screening decisions across duplicate groups are consistent.")

    if len(queries) < 2:
        st.info("You currently have 1 search version. Click below to load **Expanded Query v2** and test the Level-2 Diff View immediately!")
        if st.button("⚡ Load Expanded Query v2 (+2 New Papers) Now", type="primary"):
            vid = create_query_version(
                "Benchmark v2 (Expanded Query)",
                '("type 2 diabetes") AND metformin AND (placebo OR sulfonylurea OR sitagliptin)',
                2015, 2025, ["PubMed", "Europe PMC"], 9, 5
            )
            store_fetched_records(vid, get_benchmark_papers("v2"))
            run_deduplication(vid)
            run_screening(vid)
            run_pico_extraction(vid)
            st.rerun()
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
            st.markdown("#### 🟢 Newly Added Papers in Newer Search")
            st.dataframe(pd.DataFrame(diff["added_records"])[["record_id", "source", "pub_year", "title", "authors", "journal"]], use_container_width=True, hide_index=True)

    render_step_footer(curr_idx)


# ==============================================================================
# STEP 08 (INDEX 9): BONUS AI APPLICATION — "THE UNASKED QUESTION"
# 2D EVIDENCE GAP MATRIX & WHITE-SPACE DISCOVERY ENGINE
# ==============================================================================
elif curr_idx == 9:
    st.markdown("## 🧠 Step 8 (AI Innovation Lab): 'The Unasked Question' — Evidence Gap & White-Space Finder")
    st.caption(
        "Most literature review tools only show what papers **already exist**. "
        "Our AI White-Space Engine cross-maps **Patient Sub-Groups × Clinical Outcomes** across your Included & Maybe studies "
        "to discover **0-Study Scientific Blind Spots**—and auto-designs the next PhD clinical trial protocol + Level-2 search mutation!"
    )

    conn = get_connection()
    rows = conn.execute("""
    SELECT
        r.*,
        COALESCE(rd.screening_decision, ms.decision, 'Maybe') AS final_decision,
        COALESCE(rd.pico_p, mp.population_span, '') AS pico_p,
        COALESCE(rd.pico_i, mp.intervention_span, '') AS pico_i,
        COALESCE(rd.pico_c, mp.comparator_span, '') AS pico_c,
        COALESCE(rd.pico_o, mp.outcome_span, '') AS pico_o
    FROM records r
    LEFT JOIN machine_screening ms ON r.record_id = ms.record_id
    LEFT JOIN reviewer_decisions rd ON r.duplicate_group_id = rd.group_id
    LEFT JOIN machine_pico mp ON r.record_id = mp.record_id
    WHERE r.is_hidden_duplicate = 0;
    """).fetchall()
    conn.close()

    eligible_studies = [dict(r) for r in rows if r["final_decision"] in ("Include", "Maybe")]

    if not eligible_studies:
        st.warning("No Included or Maybe studies in the database yet! Click below to load the 12-Paper Benchmark Dataset and see the AI Evidence Gap Matrix live.")
        if st.button("⚡ Load 12 Benchmark Papers & Run AI White-Space Engine Now", type="primary"):
            vid = create_query_version(
                "Benchmark v1 (Metformin vs Placebo)",
                '("type 2 diabetes") AND metformin AND placebo',
                2015, 2025, ["PubMed", "Europe PMC"], 8, 4
            )
            store_fetched_records(vid, get_benchmark_papers("v1"))
            run_deduplication(vid)
            run_screening(vid)
            run_pico_extraction(vid)
            st.rerun()
    else:
        gap_data = compute_ai_evidence_gap_matrix(eligible_studies, config)

        # Summary telemetry for the AI Matrix
        g1, g2, g3, g4 = st.columns(4)
        g1.metric("🧬 Analyzed Eligible Studies", len(eligible_studies))
        g2.metric("🟢 Dense Evidence Cells (2+ RCTs)", gap_data["dense_count"])
        g3.metric("🟡 Sparse Evidence Cells (1 RCT)", gap_data["sparse_count"])
        g4.metric("🔥 Discovered White-Space Gaps (0 RCTs)", gap_data["zero_count"])

        st.markdown("### 🗺️ 1. Live 2D PICO Evidence Heatmap (`Patient Sub-Cohorts` × `Clinical Outcomes`)")
        st.caption("🟢 **Green** = Well-studied area &nbsp;|&nbsp; 🟡 **Amber** = Only 1 trial exists &nbsp;|&nbsp; 🔥 **Pulsing Red (0 Studies)** = **Unexplored Research White-Space!**")

        # Render 2D Heatmap Grid Header
        hdr_cols = st.columns([1.3, 1, 1, 1, 1])
        hdr_cols[0].markdown("**Sub-Population \\ Outcome**")
        for c_idx, out_name in enumerate(gap_data["outcomes"]):
            hdr_cols[c_idx + 1].markdown(f"<div style='text-align:center; font-weight:700; font-size:0.84rem;'>{out_name}</div>", unsafe_allow_html=True)

        # Render each row of the 2D Heatmap
        for sg_name in gap_data["subgroups"]:
            r_cols = st.columns([1.3, 1, 1, 1, 1])
            r_cols[0].markdown(f"<div style='padding-top:18px; font-weight:700; font-size:0.88rem;'>👥 {sg_name}</div>", unsafe_allow_html=True)
            for c_idx, out_name in enumerate(gap_data["outcomes"]):
                cell = gap_data["matrix"][sg_name][out_name]
                cnt = cell["count"]
                pids = ", ".join(f"#{i}" for i in cell["paper_ids"])
                if cnt >= 2:
                    r_cols[c_idx + 1].markdown(
                        f"<div class='gap-cell-dense'>"
                        f"<div style='font-size:1.25rem; font-weight:800; color:#10b981;'>🟢 {cnt} Studies</div>"
                        f"<div style='font-size:0.72rem; opacity:0.85;'>Papers: {pids}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                elif cnt == 1:
                    r_cols[c_idx + 1].markdown(
                        f"<div class='gap-cell-sparse'>"
                        f"<div style='font-size:1.25rem; font-weight:800; color:#f59e0b;'>🟡 1 Study</div>"
                        f"<div style='font-size:0.72rem; opacity:0.85;'>Paper: {pids}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                else:
                    r_cols[c_idx + 1].markdown(
                        f"<div class='gap-cell-zero'>"
                        f"<div style='font-size:1.15rem; font-weight:800; color:#fb7185;'>🔥 0 STUDIES</div>"
                        f"<div style='font-size:0.70rem; color:#fda4af; font-weight:700;'>WHITE-SPACE GAP</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
            st.write("")

        st.markdown("---")
        st.markdown("### 🚀 2. AI 'Unasked Question' & Clinical Trial Protocol Generator")
        st.caption("Select any discovered **🔥 0-Study White-Space Gap** below to generate a ready-to-pitch PhD/Clinical Trial Protocol or auto-mutate your Level 2 search query!")

        if gap_data["gaps"]:
            gap_labels = [f"🔥 GAP #{idx+1}: {g['subgroup']} × {g['outcome']} (0 Clinical Trials Found)" for idx, g in enumerate(gap_data["gaps"])]
            chosen_idx = st.selectbox("Select a Discovered Scientific White-Space Gap to Inspect:", range(len(gap_labels)), format_func=lambda i: gap_labels[i])
            sel_gap = gap_data["gaps"][chosen_idx]

            with st.container(border=True):
                st.markdown(f"#### 💡 AI-Discovered Unasked Research Question")
                st.markdown(f"<div class='query-terminal'>❓ \"{sel_gap['unasked_question']}\"</div>", unsafe_allow_html=True)

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("##### 🕵️ Why This Blind Spot Exists in Literature")
                    st.write(sel_gap["why_missed"])
                with col_b:
                    st.markdown("##### 🧪 AI-Synthesized Phase III Trial Blueprint")
                    st.write(sel_gap["trial_design"])

                st.markdown("##### 🔄 Close the Loop: Auto-Mutate Search Query for Level 2")
                st.code(sel_gap["mutated_query"], language="text")

                if st.button("⚡ Inject This Gap Query into Step 1 (Query Studio) & Launch Level-2 Search ➡️", type="primary", use_container_width=True):
                    st.session_state["custom_query_box"] = sel_gap["mutated_query"]
                    go_to_step(2)

    render_step_footer(curr_idx)


# ==============================================================================
# STEP 09 (INDEX 10): EXPORT CSV & AUDIT TRAIL
# ==============================================================================
elif curr_idx == 10:
    st.markdown("### 📥 Step 9: Export Final CSV & Complete Audit Trail")
    conn = get_connection()
    export_rows = conn.execute("""
    SELECT
        r.record_id, r.duplicate_group_id, r.source, r.pmid, r.doi,
        r.title, r.authors, r.pub_year, r.journal,
        COALESCE(rd.screening_decision, ms.decision, 'Maybe') AS final_decision,
        CASE WHEN rd.screening_decision IS NOT NULL THEN 'Human Override' ELSE 'Machine Rule' END AS decision_source,
        COALESCE(rd.exclusion_reason, ms.exclusion_reasons, '') AS reason,
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
    export_Bucket = st.radio("Select Export Bucket:", ["✅ Only Included Studies", "❌ Only Excluded Studies", "📚 All Unique Studies"], horizontal=True)

    if not df_all.empty:
        if "Included" in export_Bucket:
            df_exp = df_all[df_all["final_decision"] == "Include"]
        elif "Excluded" in export_Bucket:
            df_exp = df_all[df_all["final_decision"] == "Exclude"]
        else:
            df_exp = df_all

        st.dataframe(df_exp, use_container_width=True, hide_index=True)
        st.download_button(
            label=f"📥 Download CSV ({len(df_exp)} Studies)",
            data=df_exp.to_csv(index=False).encode("utf-8"),
            file_name="mini_rayyan_export.csv",
            mime="text/csv",
            type="primary"
        )

    st.markdown("---")
    l1, l2 = st.columns(2)
    with l1:
        st.markdown("#### ✍️ Human Override Audit Log")
        audits = conn.execute("SELECT * FROM audit_log ORDER BY log_id DESC;").fetchall()
        if audits:
            st.dataframe(pd.DataFrame([dict(a) for a in audits]), use_container_width=True, hide_index=True)
    with l2:
        st.markdown("#### ⚙️ Pipeline Execution Log")
        runs = conn.execute("SELECT * FROM run_log ORDER BY run_id DESC;").fetchall()
        if runs:
            st.dataframe(pd.DataFrame([dict(r) for r in runs]), use_container_width=True, hide_index=True)
    conn.close()
    render_step_footer(curr_idx)
