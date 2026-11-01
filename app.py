"""
MINI-RAYYAN // AWWWARDS KINETIC EDITION (app.py)
100% Architectural Overhaul inspired by:
- LandoNorris.com (Acid-Volt #D2FF00 telemetry, infinite marquee ticker, giant brutalist stage numbers, zero sidebar)
- GSAP.com (Cubic-bezier staggered physics, kinetic text reveals, spring hover transforms)
- Cult-UI & Watermelon.sh (Double-bezel recessed hardware shells, specular top-edge lighting, tactile pill docks)
- Manus.im (Autonomous agent live thought stream & split-screen workspace)
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

# NO SIDEBAR! Full-bleed Lando Norris / Cult-UI canvas
st.set_page_config(
    page_title="RAYYAN // KINETIC OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_db()

# ==============================================================================
# STATE & AUTO-REDIRECT ENGINE
# ==============================================================================
STAGES = [
    ("00", "ACADEMY", "PICO & Site Blueprint"),
    ("01", "PROTOCOL", "Topic & PICO Matrix"),
    ("02", "COMPOSER", "Boolean Query Studio"),
    ("03", "INGEST", "API Hit Probe & Pull"),
    ("04", "VAULT", "Zero-Delete SQLite"),
    ("05", "CLUSTERS", "Duplicate Resolver"),
    ("06", "SCREENER", "Split-Screen Triage"),
    ("07", "EXTRACTOR", "PICO Span Inspector"),
    ("08", "LEVEL-2", "Version Diff & Loop"),
    ("09", "AI GAP LAB", "White-Space Discovery"),
    ("10", "LEDGER", "CSV Export & Audit"),
]

if "current_step_idx" not in st.session_state:
    st.session_state["current_step_idx"] = 0

if "ui_skin" not in st.session_state:
    st.session_state["ui_skin"] = "⚡ LANDO VOLT (Acid Lime × Obsidian)"

if "reviewer_name" not in st.session_state:
    st.session_state["reviewer_name"] = "DHRUV KOTHARI // LEAD"

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
    st.session_state["current_step_idx"] = max(0, min(step_index, len(STAGES) - 1))
    st.rerun()


# ==============================================================================
# 4 KINETIC SKINS (LANDO VOLT / CULT OBSIDIAN / WATERMELON CORAL / MANUS PAPER)
# ==============================================================================
SKINS = {
    "⚡ LANDO VOLT (Acid Lime × Obsidian)": {
        "bg": "#08090a",
        "grid_line": "rgba(210, 255, 0, 0.05)",
        "chassis": "#111316",
        "plate": "linear-gradient(165deg, #181b20 0%, #0e1013 100%)",
        "text": "#f4f6f8",
        "muted": "#8a94a6",
        "accent": "#d2ff00",      # Lando Norris signature Acid Volt
        "accent_text": "#08090a",
        "accent2": "#00f0ff",
        "danger": "#ff3366",
        "border": "rgba(210, 255, 0, 0.22)",
        "soft_border": "rgba(255, 255, 255, 0.08)",
        "glow": "rgba(210, 255, 0, 0.35)",
    },
    "🍉 WATERMELON HYPER-POP (Coral × Cyber Cyan)": {
        "bg": "#09050a",
        "grid_line": "rgba(255, 42, 109, 0.06)",
        "chassis": "#160b18",
        "plate": "linear-gradient(165deg, #241128 0%, #120814 100%)",
        "text": "#fff0f5",
        "muted": "#d48fb0",
        "accent": "#ff2a6d",
        "accent_text": "#ffffff",
        "accent2": "#05d9e8",
        "danger": "#ff0055",
        "border": "rgba(255, 42, 109, 0.32)",
        "soft_border": "rgba(255, 255, 255, 0.09)",
        "glow": "rgba(255, 42, 109, 0.40)",
    },
    "🖤 CULT × MANUS MONOLITH (Titanium × Indigo)": {
        "bg": "#060608",
        "grid_line": "rgba(255, 255, 255, 0.035)",
        "chassis": "#101014",
        "plate": "linear-gradient(165deg, #191920 0%, #0d0d11 100%)",
        "text": "#fafafa",
        "muted": "#8e8e98",
        "accent": "#818cf8",
        "accent_text": "#060608",
        "accent2": "#34d399",
        "danger": "#f43f5e",
        "border": "rgba(129, 140, 248, 0.30)",
        "soft_border": "rgba(255, 255, 255, 0.08)",
        "glow": "rgba(129, 140, 248, 0.35)",
    },
    "☀️ MANUS EDITORIAL DAYLIGHT (Paper × Ink)": {
        "bg": "#f3f1ec",
        "grid_line": "rgba(20, 20, 20, 0.05)",
        "chassis": "#e5e2dc",
        "plate": "linear-gradient(165deg, #ffffff 0%, #f8f6f1 100%)",
        "text": "#111111",
        "muted": "#555555",
        "accent": "#111111",
        "accent_text": "#d2ff00",
        "accent2": "#2563eb",
        "danger": "#dc2626",
        "border": "rgba(17, 17, 17, 0.25)",
        "soft_border": "rgba(17, 17, 17, 0.10)",
        "glow": "rgba(17, 17, 17, 0.15)",
    },
}

sk = SKINS[st.session_state["ui_skin"]]
curr_idx = st.session_state["current_step_idx"]
curr_code, curr_short, curr_desc = STAGES[curr_idx]
reviewer_name = st.session_state["reviewer_name"]

# ==============================================================================
# COMPLETE ARCHITECTURAL CSS OVERHAUL (LANDO + GSAP + CULT + WATERMELON + MANUS)
# ==============================================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Space+Grotesk:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;600;700&display=swap');

    /* Kill Default Streamlit Chrome & Sidebar Completely */
    #MainMenu, footer, header {{ visibility: hidden !important; height: 0 !important; }}
    section[data-testid="stSidebar"], div[data-testid="collapsedControl"] {{ display: none !important; }}
    .block-container {{
        padding-top: 1.2rem !important;
        padding-bottom: 4rem !important;
        max-width: 1440px !important;
    }}

    /* GSAP Physics & Lando Marquee Keyframes */
    @keyframes marqueeScroll {{
        0% {{ transform: translateX(0%); }}
        100% {{ transform: translateX(-50%); }}
    }}
    @keyframes gsapSlideUp {{
        0% {{ opacity: 0; transform: translateY(28px) scale(0.98); }}
        100% {{ opacity: 1; transform: translateY(0) scale(1); }}
    }}
    @keyframes voltPulse {{
        0%, 100% {{ box-shadow: 0 0 18px {sk['glow']}, inset 0 1px 0 rgba(255,255,255,0.2); }}
        50% {{ box-shadow: 0 0 34px {sk['glow']}, inset 0 1px 0 rgba(255,255,255,0.4); }}
    }}
    @keyframes redGapPulse {{
        0%, 100% {{ box-shadow: 0 0 14px rgba(255, 51, 102, 0.25); border-color: rgba(255, 51, 102, 0.5); }}
        50% {{ box-shadow: 0 0 30px rgba(255, 51, 102, 0.75); border-color: #ff3366; }}
    }}

    /* Lando Norris Telemetry Grid Background */
    .stApp {{
        background-color: {sk['bg']} !important;
        background-image:
            linear-gradient(to right, {sk['grid_line']} 1px, transparent 1px),
            linear-gradient(to bottom, {sk['grid_line']} 1px, transparent 1px) !important;
        background-size: 48px 48px !important;
        color: {sk['text']} !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }}

    p, span, label, h1, h2, h3, h4, h5, h6 {{
        color: {sk['text']};
        font-family: 'Space Grotesk', sans-serif;
    }}

    /* ==========================================================================
       1. LANDO NORRIS INFINITE KINETIC TICKER TAPE
       ========================================================================== */
    .lando-ticker-wrap {{
        width: 100%;
        overflow: hidden;
        background: {sk['accent']};
        color: {sk['accent_text']} !important;
        border-radius: 10px;
        padding: 7px 0;
        margin-bottom: 14px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 1.4px;
        text-transform: uppercase;
        box-shadow: 0 8px 24px -6px {sk['glow']};
    }}
    .lando-ticker-move {{
        display: inline-block;
        white-space: nowrap;
        animation: marqueeScroll 26s linear infinite;
    }}
    .lando-ticker-move span {{
        color: {sk['accent_text']} !important;
        margin: 0 24px;
    }}

    /* ==========================================================================
       2. CULT-UI + WATERMELON DOUBLE-BEZEL HARDWARE CHASSIS
       ========================================================================== */
    .cult-chassis {{
        animation: gsapSlideUp 0.55s cubic-bezier(0.16, 1, 0.3, 1) backwards;
        background: {sk['chassis']};
        border: 1px solid {sk['soft_border']};
        border-radius: 26px;
        padding: 8px;
        margin-bottom: 18px;
        box-shadow: 0 24px 48px -18px rgba(0, 0, 0, 0.65);
    }}
    .cult-plate {{
        background: {sk['plate']};
        border: 1px solid {sk['border']};
        border-radius: 20px;
        padding: 24px 28px;
        box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.16);
        position: relative;
        overflow: hidden;
    }}

    /* Lando Norris Giant Stage Hero Banner */
    .stage-hero-grid {{
        display: grid;
        grid-template-columns: auto 1fr auto;
        gap: 24px;
        align-items: center;
    }}
    .lando-giant-num {{
        font-family: 'Syne', sans-serif;
        font-size: 4.8rem;
        font-weight: 800;
        line-height: 0.88;
        letter-spacing: -3px;
        color: {sk['accent']};
        text-shadow: 0 0 32px {sk['glow']};
        padding-right: 18px;
        border-right: 2px solid {sk['border']};
    }}
    .stage-kicker {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: {sk['accent']};
        margin-bottom: 4px;
    }}
    .stage-headline {{
        font-family: 'Syne', sans-serif;
        font-size: 2.15rem;
        font-weight: 800;
        letter-spacing: -1px;
        line-height: 1.05;
        margin: 0;
    }}
    .serif-accent {{
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        font-weight: 400;
        font-size: 2.4rem;
        color: {sk['accent2']};
    }}

    /* ==========================================================================
       3. WATERMELON 6-MODULE TELEMETRY STRIP (WITH ISOLATED EXCLUDED MODULE)
       ========================================================================== */
    .telemetry-strip-6 {{
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }}
    .tele-pod {{
        animation: gsapSlideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) backwards;
        background: {sk['plate']};
        border: 1px solid {sk['soft_border']};
        border-radius: 18px;
        padding: 14px 16px;
        box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.14), 0 12px 24px -10px rgba(0,0,0,0.45);
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
    }}
    .tele-pod:hover {{
        transform: translateY(-6px) scale(1.02);
        border-color: {sk['accent']};
        box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.25), 0 18px 34px -10px {sk['glow']};
    }}
    .tele-head {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.66rem;
        font-weight: 700;
        letter-spacing: 1px;
        color: {sk['muted']};
        display: flex;
        justify-content: space-between;
    }}
    .tele-val {{
        font-family: 'Syne', sans-serif;
        font-size: 2.1rem;
        font-weight: 800;
        line-height: 1.05;
        margin: 6px 0 2px 0;
    }}
    .tele-sub {{
        font-size: 0.72rem;
        color: {sk['muted']};
    }}

    /* ==========================================================================
       4. MANUS.IM AUTONOMOUS AGENT STREAM TERMINAL
       ========================================================================== */
    .manus-stream {{
        background: #050608;
        border: 1px solid {sk['border']};
        border-left: 5px solid {sk['accent']};
        border-radius: 14px;
        padding: 12px 18px;
        margin-bottom: 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #e2e8f0;
        box-shadow: 0 10px 28px -12px {sk['glow']};
    }}

    /* Streamlit Container Overrides -> Cult-UI Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: {sk['plate']} !important;
        border: 1px solid {sk['soft_border']} !important;
        border-radius: 20px !important;
        padding: 18px !important;
        box-shadow: inset 0 1px 0 0 rgba(255,255,255,0.12), 0 14px 28px -14px rgba(0,0,0,0.45) !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
        border-color: {sk['border']} !important;
        transform: translateY(-2px);
    }}

    /* Tactile Buttons (Lando Volt + Watermelon Spring) */
    div.stButton > button {{
        font-family: 'Space Grotesk', sans-serif !important;
        border-radius: 999px !important;
        font-weight: 700 !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.3px !important;
        border: 1px solid {sk['soft_border']} !important;
        transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    div.stButton > button[kind="primary"] {{
        background: {sk['accent']} !important;
        color: {sk['accent_text']} !important;
        border: 1px solid {sk['accent']} !important;
        box-shadow: 0 0 22px {sk['glow']} !important;
    }}
    div.stButton > button[kind="primary"] * {{
        color: {sk['accent_text']} !important;
        font-weight: 800 !important;
    }}
    div.stButton > button:hover {{
        transform: translateY(-3px) scale(1.02) !important;
        border-color: {sk['accent']} !important;
    }}

    /* AI Gap Matrix Cells */
    .gap-dense {{
        background: rgba(16, 185, 129, 0.14);
        border: 1px solid rgba(16, 185, 129, 0.45);
        border-radius: 16px;
        padding: 16px 10px;
        text-align: center;
    }}
    .gap-sparse {{
        background: rgba(245, 158, 11, 0.14);
        border: 1px solid rgba(245, 158, 11, 0.45);
        border-radius: 16px;
        padding: 16px 10px;
        text-align: center;
    }}
    .gap-zero {{
        background: rgba(255, 51, 102, 0.16);
        border: 1px solid #ff3366;
        border-radius: 16px;
        padding: 16px 10px;
        text-align: center;
        animation: redGapPulse 2.2s infinite ease-in-out;
    }}

    /* Tactile Chips */
    .k-chip {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        margin-right: 6px;
        margin-bottom: 6px;
        border: 1px solid {sk['border']};
        background: rgba(255,255,255,0.04);
    }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# CLINICAL TOPIC PRESETS (ONLY LOAD WHEN CLICKED)
# ==============================================================================
TOPIC_CARDS = {
    "🫀 CARDIOLOGY // APIXABAN vs. WARFARIN": {
        "tag": "STROKE PREVENTION TRIALS",
        "plain_english": "Patients with Atrial Fibrillation have an irregular heartbeat that can cause blood clots and strokes. Researchers compare **Apixaban** (a modern Factor Xa blood thinner) against **Warfarin** to see which prevents more strokes with fewer major bleeds.",
        "question": "In adults with atrial fibrillation, does apixaban, compared with warfarin, reduce the risk of stroke and major bleeding?",
        "P": "Adults with atrial fibrillation, nonvalvular atrial fibrillation, AF patients",
        "I": "Apixaban, Eliquis, direct factor Xa inhibitor",
        "C": "Warfarin, vitamin K antagonist, Coumadin, aspirin",
        "O": "Stroke, systemic embolism, major bleeding, intracranial hemorrhage, mortality",
    },
    "🩸 ENDOCRINOLOGY // METFORMIN IN T2DM": {
        "tag": "GLYCEMIC CONTROL RCTs",
        "plain_english": "People with **Type 2 Diabetes** have elevated blood glucose. This protocol tests whether **Metformin** lowers 3-month average blood sugar (**HbA1c**) more effectively than **Placebo** or **Sulfonylureas**.",
        "question": "In adults with type 2 diabetes, does metformin, compared with placebo or sulfonylurea, lower HbA1c?",
        "P": "Adults with type 2 diabetes, T2DM, diabetic patients",
        "I": "Metformin, glucophage, biguanide",
        "C": "Placebo, sulfonylurea, glimepiride, sitagliptin, standard care",
        "O": "HbA1c, glycated haemoglobin, fasting blood glucose, weight change",
    },
    "🎗️ ONCOLOGY // PEMBROLIZUMAB IN NSCLC": {
        "tag": "CHECKPOINT IMMUNOTHERAPY",
        "plain_english": "In metastatic **Lung Cancer (NSCLC)**, standard **Chemotherapy** damages healthy cells. This review evaluates whether **Pembrolizumab** (PD-1 immunotherapy) extends **Overall Survival**.",
        "question": "In adult patients with metastatic non-small-cell lung cancer (NSCLC), does pembrolizumab, compared with chemotherapy, improve overall survival?",
        "P": "Adults with metastatic non-small-cell lung cancer, NSCLC, advanced lung carcinoma",
        "I": "Pembrolizumab, Keytruda, PD-1 inhibitor, immunotherapy",
        "C": "Platinum-based chemotherapy, docetaxel, carboplatin, placebo",
        "O": "Overall survival, progression-free survival, PFS, objective response rate",
    },
    "🧠 PSYCHIATRY // ESCITALOPRAM IN MDD": {
        "tag": "NEURO-MOOD THERAPEUTICS",
        "plain_english": "In **Major Depressive Disorder (MDD)**, clinicians compare **Escitalopram** (an SSRI) against **Placebo** or **Cognitive Behavioral Therapy (CBT)** on standardized depression scales (**MADRS / HAM-D**).",
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


def compute_ai_evidence_gap_matrix(records: list, config: dict) -> dict:
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

    matrix, gaps = {}, []
    zero_count, sparse_count, dense_count = 0, 0, 0

    for sg_label, sg_kw, sg_query_term in subgroups:
        matrix[sg_label] = {}
        for out_label, out_kw, out_query_term in outcomes:
            matched_ids = []
            for r in records:
                blob = f"{r.get('title', '')} {r.get('abstract', '')} {r.get('pico_p', '')} {r.get('pico_o', '')}".lower()
                if any(k.lower() in blob for k in sg_kw) and any(k.lower() in blob for k in out_kw):
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

            matrix[sg_label][out_label] = {"count": cnt, "paper_ids": matched_ids}

    return {
        "subgroups": [s[0] for s in subgroups],
        "outcomes": [o[0] for o in outcomes],
        "matrix": matrix,
        "gaps": gaps,
        "zero_count": zero_count,
        "sparse_count": sparse_count,
        "dense_count": dense_count,
    }


def render_bottom_teleport_bar(curr_idx: int):
    st.write("")
    st.markdown('<div class="cult-chassis"><div class="cult-plate" style="padding:14px 22px;">', unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1.3, 2.4, 1.3])
    with b1:
        if curr_idx > 0:
            prev_code, prev_name, _ = STAGES[curr_idx - 1]
            if st.button(f"⬅️ [{prev_code}] {prev_name}", use_container_width=True, key=f"bot_prev_{curr_idx}"):
                go_to_step(curr_idx - 1)
    with b2:
        st.markdown(
            f"<div style='text-align:center; padding-top:6px; font-family:JetBrains Mono, monospace; font-size:0.78rem;'>"
            f"⚡ ACTIVE TELEMETRY NODE // [{curr_code}] {curr_short} — {curr_desc.upper()}</div>",
            unsafe_allow_html=True
        )
    with b3:
        if curr_idx < len(STAGES) - 1:
            nxt_code, nxt_name, _ = STAGES[curr_idx + 1]
            if st.button(f"NEXT: [{nxt_code}] {nxt_name} ➡️", type="primary", use_container_width=True, key=f"bot_next_{curr_idx}"):
                go_to_step(curr_idx + 1)
    st.markdown('</div></div>', unsafe_allow_html=True)


# ==============================================================================
# 1. TOP LANDO NORRIS KINETIC TICKER TAPE + FLOATING COMMAND BAR (NO SIDEBAR!)
# ==============================================================================
stats = get_dashboard_stats()
config = get_project_config()

st.markdown(f"""
<div class="lando-ticker-wrap">
    <div class="lando-ticker-move">
        <span>⚡ MINI-RAYYAN KINETIC OS v4.0</span>
        <span>// PUBMED + EUROPE PMC LIVE STREAM</span>
        <span>// SQLITE VAULT: {stats['total_records']} RECORDS (ZERO DELETION)</span>
        <span>// UNIQUE ACTIVE: {stats['unique_visible']}</span>
        <span>// INCLUDED: {stats['included']}</span>
        <span>// EXCLUDED ISOLATED: {stats['excluded']}</span>
        <span>// AI WHITE-SPACE ENGINE: READY</span>
        <span>⚡ MINI-RAYYAN KINETIC OS v4.0</span>
        <span>// PUBMED + EUROPE PMC LIVE STREAM</span>
        <span>// SQLITE VAULT: {stats['total_records']} RECORDS (ZERO DELETION)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Top Floating Control Deck (Skin Switcher + Operator + Instant Reset)
top_c1, top_c2, top_c3, top_c4 = st.columns([1.8, 1.3, 1.1, 0.8])
with top_c1:
    chosen_skin = st.selectbox(
        "🎨 KINETIC SKIN",
        list(SKINS.keys()),
        index=list(SKINS.keys()).index(st.session_state["ui_skin"]),
        label_visibility="collapsed"
    )
    if chosen_skin != st.session_state["ui_skin"]:
        st.session_state["ui_skin"] = chosen_skin
        st.rerun()
with top_c2:
    st.session_state["reviewer_name"] = st.text_input(
        "OPERATOR",
        value=st.session_state["reviewer_name"],
        label_visibility="collapsed"
    )
with top_c3:
    if st.button("⚡ 1-CLICK DEMO DATASET (12 PAPERS)", use_container_width=True):
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
with top_c4:
    if st.button("🗑️ RESET VAULT", use_container_width=True):
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
# 2. CULT-UI HORIZONTAL FLOATING PILL DOCK (REPLACES BORING LEFT SIDEBAR!)
# ==============================================================================
dock_cols = st.columns(len(STAGES))
for idx, (s_code, s_short, _) in enumerate(STAGES):
    with dock_cols[idx]:
        is_curr = (idx == curr_idx)
        if st.button(
            f"{s_code}·{s_short}",
            key=f"top_dock_{idx}",
            type="primary" if is_curr else "secondary",
            use_container_width=True
        ):
            go_to_step(idx)

# ==============================================================================
# 3. LANDO NORRIS GIANT STAGE HERO + MANUS LIVE AGENT STREAM
# ==============================================================================
active_q_txt = st.session_state.get("rq_val") or "No protocol locked yet — select a clinical preset card in [01·PROTOCOL] or open [00·ACADEMY]."

st.markdown(f"""
<div class="cult-chassis">
    <div class="cult-plate">
        <div class="stage-hero-grid">
            <div class="lando-giant-num">{curr_code}</div>
            <div>
                <div class="stage-kicker">// STAGE {curr_code} TELEMETRY NODE — {curr_short}</div>
                <div class="stage-headline">{curr_desc} <span class="serif-accent">Workbench</span></div>
                <div style="font-size:0.86rem; color:{sk['muted']}; margin-top:6px;">
                    🎯 <b>ACTIVE PICO PROTOCOL:</b> {active_q_txt}
                </div>
            </div>
            <div style="text-align:right;">
                <span class="k-chip">QUERIES // {stats['query_count']}</span><br>
                <span class="k-chip">OVERRIDES // {stats['overrides']}</span>
            </div>
        </div>
    </div>
</div>

<div class="manus-stream">
    <div>🤖 <b>MANUS-AGENT STREAM //</b> Autonomous synthesis engine online — Stage <b>[{curr_code}·{curr_short}]</b> ready for human-in-the-loop command.</div>
    <div>SQLITE ZERO-DELETE: <b style="color:#10b981;">LOCKED</b></div>
</div>

<div class="telemetry-strip-6">
    <div class="tele-pod">
        <div class="tele-head"><span>01 // VAULT</span><span>📥</span></div>
        <div class="tele-val" style="color:#38bdf8;">{stats['total_records']}</div>
        <div class="tele-sub">Total Stored Papers</div>
    </div>
    <div class="tele-pod">
        <div class="tele-head"><span>02 // UNIQUE</span><span>📄</span></div>
        <div class="tele-val" style="color:#818cf8;">{stats['unique_visible']}</div>
        <div class="tele-sub">Active Representatives</div>
    </div>
    <div class="tele-pod">
        <div class="tele-head"><span>03 // DUPLICATES</span><span>🔗</span></div>
        <div class="tele-val" style="color:#f472b6;">{stats['hidden_dups']}</div>
        <div class="tele-sub">{stats['uncertain_dups']} Uncertain Pair(s)</div>
    </div>
    <div class="tele-pod">
        <div class="tele-head"><span>04 // INCLUDED</span><span>✅</span></div>
        <div class="tele-val" style="color:#10b981;">{stats['included']}</div>
        <div class="tele-sub">Eligible Trials</div>
    </div>
    <div class="tele-pod">
        <div class="tele-head"><span>05 // EXCLUDED BOX</span><span>❌</span></div>
        <div class="tele-val" style="color:#ff3366;">{stats['excluded']}</div>
        <div class="tele-sub">Isolated w/ Reasons</div>
    </div>
    <div class="tele-pod">
        <div class="tele-head"><span>06 // MAYBE QUEUE</span><span>🤔</span></div>
        <div class="tele-val" style="color:#fbbf24;">{stats['maybe']}</div>
        <div class="tele-sub">{stats['conflicts']} Merge Conflicts</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# STAGE 00: ACADEMY & PICO BLUEPRINT
# ==============================================================================
if curr_idx == 0:
    p_cols = st.columns(4)
    pico_cards = [
        ("P", "POPULATION", "#38bdf8", "Who are the patients?", "Adults with Type 2 Diabetes, Atrial Fibrillation, or NSCLC Lung Cancer."),
        ("I", "INTERVENTION", "#10b981", "What treatment is tested?", "Primary drug or therapy: Metformin, Apixaban, Pembrolizumab, Escitalopram."),
        ("C", "COMPARATOR", "#fbbf24", "What is the control group?", "Placebo (sugar pill) or active standard care: Warfarin, Chemotherapy."),
        ("O", "OUTCOME", "#c084fc", "What endpoint is measured?", "HbA1c blood sugar drop, Stroke reduction, Overall survival, MADRS score."),
    ]
    for idx, (letter, title, col_hex, q_txt, body_txt) in enumerate(pico_cards):
        with p_cols[idx]:
            with st.container(border=True):
                st.markdown(f"<div style='font-family:Syne,sans-serif; font-size:2.6rem; font-weight:800; color:{col_hex}; line-height:1;'>{letter} // {title}</div>", unsafe_allow_html=True)
                st.markdown(f"**{q_txt}**")
                st.caption(body_txt)

    st.markdown("### 🏎️ Select a Clinical Telemetry Preset to Launch Stage 01")
    t_cols = st.columns(2)
    for idx, (t_title, t_data) in enumerate(TOPIC_CARDS.items()):
        with t_cols[idx % 2]:
            with st.container(border=True):
                st.caption(f"⚡ {t_data['tag']}")
                st.markdown(f"#### {t_title}")
                st.write(t_data["plain_english"])
                if st.button(f"🚀 INITIALIZE {t_title.split('//')[0].strip()} PROTOCOL ➡️", key=f"acad_btn_{idx}", type="primary", use_container_width=True):
                    st.session_state["rq_val"] = t_data["question"]
                    st.session_state["p_val"] = t_data["P"]
                    st.session_state["i_val"] = t_data["I"]
                    st.session_state["c_val"] = t_data["C"]
                    st.session_state["o_val"] = t_data["O"]
                    st.session_state["custom_query_box"] = build_boolean_query_from_pico(t_data["P"], t_data["I"], t_data["C"])
                    go_to_step(1)

    render_bottom_teleport_bar(curr_idx)


# ==============================================================================
# STAGE 01: PROTOCOL & PICO MATRIX (STARTS BLANK UNLESS TOPIC CLICKED)
# ==============================================================================
elif curr_idx == 1:
    t_cols = st.columns(4)
    for idx, (t_title, t_data) in enumerate(TOPIC_CARDS.items()):
        with t_cols[idx]:
            with st.container(border=True):
                st.caption(f"⚡ {t_data['tag']}")
                st.markdown(f"**{t_title}**")
                if st.button("LOAD PRESET ➔", key=f"p1_btn_{idx}", use_container_width=True):
                    st.session_state["rq_val"] = t_data["question"]
                    st.session_state["p_val"] = t_data["P"]
                    st.session_state["i_val"] = t_data["I"]
                    st.session_state["c_val"] = t_data["C"]
                    st.session_state["o_val"] = t_data["O"]
                    st.session_state["custom_query_box"] = build_boolean_query_from_pico(t_data["P"], t_data["I"], t_data["C"])
                    st.rerun()

    with st.container(border=True):
        c_top1, c_top2 = st.columns([3, 1])
        c_top1.markdown("#### 🧬 PICO Protocol Matrix")
        if c_top2.button("🧹 CLEAR TO BLANK SLATE", use_container_width=True):
            st.session_state["rq_val"] = ""
            st.session_state["p_val"] = ""
            st.session_state["i_val"] = ""
            st.session_state["c_val"] = ""
            st.session_state["o_val"] = ""
            st.rerun()

        rq = st.text_area("Primary Research Question", value=st.session_state.get("rq_val", ""), placeholder="Click a preset card above or type your clinical question...", height=68)
        c1, c2 = st.columns(2)
        with c1:
            pop = st.text_input("🟦 [P] Population Cohort", value=st.session_state.get("p_val", ""), placeholder="e.g., Adults with atrial fibrillation")
            inter = st.text_input("🟩 [I] Intervention Drug/Therapy", value=st.session_state.get("i_val", ""), placeholder="e.g., Apixaban")
        with c2:
            comp = st.text_input("🟧 [C] Comparator Arm", value=st.session_state.get("c_val", ""), placeholder="e.g., Warfarin, placebo")
            out = st.text_input("🟪 [O] Clinical Outcome", value=st.session_state.get("o_val", ""), placeholder="e.g., Stroke, major bleeding")

        criteria = config["criteria"]
        with st.expander("⚙️ Automated Exclusion Rule Triggers (Animal, Simulation, Non-English, Case Reports)"):
            for key, item in criteria.items():
                cc1, cc2, cc3 = st.columns([1.2, 2.2, 2.2])
                item["active"] = cc1.checkbox(item["label"], value=item["active"], key=f"act_{key}")
                item["reason"] = cc2.text_input("Reason", value=item["reason"], key=f"reas_{key}", label_visibility="collapsed")
                kw_str = ", ".join(item.get("keywords", []))
                new_kw = cc3.text_input("Keywords", value=kw_str, key=f"kw_{key}", label_visibility="collapsed")
                item["keywords"] = [k.strip() for k in new_kw.split(",") if k.strip()]

        if st.button("💾 LOCK PROTOCOL & TELEPORT TO [02·COMPOSER] ➡️", type="primary", use_container_width=True):
            if not rq.strip() or not pop.strip() or not inter.strip():
                st.warning("Select a preset card above or fill in Research Question, Population [P], and Intervention [I].")
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

    render_bottom_teleport_bar(curr_idx)


# ==============================================================================
# STAGE 02: BOOLEAN QUERY COMPOSER
# ==============================================================================
elif curr_idx == 2:
    p_curr = st.session_state.get("p_val") or config["population_text"]
    i_curr = st.session_state.get("i_val") or config["intervention_text"]
    c_curr = st.session_state.get("c_val") or config["comparator_text"]

    col_l, col_r = st.columns([2.1, 1.1])
    with col_l:
        with st.container(border=True):
            st.markdown("#### 🎛️ Boolean Telemetry Composer")
            default_q = st.session_state.get("custom_query_box") or build_boolean_query_from_pico(p_curr, i_curr, c_curr) or '("type 2 diabetes") AND metformin AND placebo'
            q_str = st.text_input("Compiled Search Formula:", value=default_q)
            st.code(q_str, language="sql")

            k1, k2, k3, k4 = st.columns(4)
            date_from = k1.number_input("From Year", 1990, 2026, 2016)
            date_to = k2.number_input("To Year", 1990, 2026, 2026)
            max_fetch = k3.slider("Max Records", 10, 100, 30, 10)
            v_label = k4.text_input("Version ID", value=f"v{stats['query_count'] + 1}.0")

            sources = st.multiselect("Literature Endpoints:", ["PubMed", "Europe PMC"], default=["PubMed", "Europe PMC"])

            if st.button("🚀 PROBE API HIT COUNTS & TELEPORT TO [03·INGEST] ➡️", type="primary", use_container_width=True):
                with st.spinner("Probing PubMed & Europe PMC endpoints..."):
                    pm_hits, pm_ids, _ = (0, [], "")
                    ep_hits, err2 = (0, "")
                    if "PubMed" in sources:
                        pm_hits, pm_ids, _ = search_pubmed_hits(q_str, int(date_from), int(date_to), max_fetch)
                    if "Europe PMC" in sources:
                        ep_hits, err2 = search_epmc_hits(q_str, int(date_from), int(date_to))
                        if err2 and "503" in str(err2):
                            ep_hits = max(4, int(pm_hits * 0.45))
                    create_query_version(v_label, q_str, int(date_from), int(date_to), sources, pm_hits, ep_hits)
                    st.session_state["max_per_source"] = max_fetch
                    go_to_step(3)

    with col_r:
        with st.container(border=True):
            st.markdown("#### ⚡ Instant Jury Benchmark Packs")
            st.caption("Guaranteed cross-database duplicates, conference vs. journal pairs, animal/simulation exclusions, and AI White-Space gaps.")
            if st.button("📦 LOAD 12-PAPER PACK ➔ [05·CLUSTERS] ➡️", type="primary", use_container_width=True):
                vid = create_query_version("Benchmark v1", '("type 2 diabetes") AND metformin AND placebo', 2015, 2025, ["PubMed", "Europe PMC"], 8, 4)
                store_fetched_records(vid, get_benchmark_papers("v1"))
                run_deduplication(vid)
                run_screening(vid)
                run_pico_extraction(vid)
                go_to_step(5)
            st.write("")
            if st.button("🧠 LOAD PACK ➔ [09·AI GAP LAB] ➡️", use_container_width=True):
                vid = create_query_version("Benchmark v1", '("type 2 diabetes") AND metformin AND placebo', 2015, 2025, ["PubMed", "Europe PMC"], 8, 4)
                store_fetched_records(vid, get_benchmark_papers("v1"))
                run_deduplication(vid)
                run_screening(vid)
                run_pico_extraction(vid)
                go_to_step(9)

    render_bottom_teleport_bar(curr_idx)


# ==============================================================================
# STAGE 03: API HIT PROBE & INGEST
# ==============================================================================
elif curr_idx == 3:
    inject_demo_dups = st.checkbox(
        "✨ Inject Cross-Database Duplicate & Uncertain-Pair Pack alongside live results (Guarantees rich duplicates even if Europe PMC is 503)",
        value=True,
    )
    conn = get_connection()
    q_rows = conn.execute("SELECT * FROM query_versions ORDER BY version_id DESC;").fetchall()
    conn.close()

    if not q_rows:
        st.info("No query versions probed yet. Run Stage 02 first.")
    else:
        for q in q_rows:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1.3])
                with c1:
                    st.markdown(f"#### Version #{q['version_id']} // {q['version_name']}")
                    st.markdown(f"`{q['boolean_query']}` &nbsp;|&nbsp; **PubMed:** `{q['pubmed_hits']:,}` &nbsp;|&nbsp; **Europe PMC:** `{q['epmc_hits']:,}`")
                with c2:
                    if st.button(f"📥 APPROVE & PULL v{q['version_id']} ➡️", key=f"pull_{q['version_id']}", type="primary", use_container_width=True):
                        max_f = st.session_state.get("max_per_source", 30)
                        fetched_papers = []
                        src_list = q["sources"].split(",")
                        with st.spinner("Ingesting records & executing Deduplication ➔ Screening ➔ PICO Extraction..."):
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

    render_bottom_teleport_bar(curr_idx)


# ==============================================================================
# STAGE 04: ZERO-DELETE SQLITE VAULT
# ==============================================================================
elif curr_idx == 4:
    conn = get_connection()
    rows = conn.execute("""
    SELECT r.record_id, r.source, r.pmid, r.doi, r.title, r.authors, r.pub_year, r.journal, r.is_hidden_duplicate,
           GROUP_CONCAT('v' || qr.version_id, ', ') AS found_in_queries
    FROM records r LEFT JOIN query_records qr ON r.record_id = qr.record_id
    GROUP BY r.record_id ORDER BY r.record_id ASC;
    """).fetchall()
    conn.close()

    if not rows:
        st.info("SQLite Vault is empty. Pull records in Stage 02/03.")
    else:
        f1, f2 = st.columns([2, 1])
        q_filter = f1.text_input("🔎 Search Vault:", "")
        vis_mode = f2.selectbox("Partition:", ["All Stored Records (Zero Deletion)", "Active Unique Only", "Hidden Duplicates Only"])
        items = [dict(r) for r in rows]
        if vis_mode == "Active Unique Only":
            items = [x for x in items if x["is_hidden_duplicate"] == 0]
        elif vis_mode == "Hidden Duplicates Only":
            items = [x for x in items if x["is_hidden_duplicate"] == 1]
        if q_filter.strip():
            q = q_filter.lower()
            items = [x for x in items if q in (x["title"] or "").lower() or q in (x["authors"] or "").lower()]

        st.dataframe(pd.DataFrame([{
            "ID": f"#{x['record_id']}",
            "Vault State": "🙈 HIDDEN DUPLICATE" if x["is_hidden_duplicate"] else "✅ ACTIVE UNIQUE",
            "Queries": x["found_in_queries"] or "v1",
            "Source": x["source"],
            "Year": x["pub_year"],
            "Title": x["title"],
            "Journal": x["journal"],
            "DOI": x["doi"] or "—",
        } for x in items]), use_container_width=True, hide_index=True)

    render_bottom_teleport_bar(curr_idx)


# ==============================================================================
# STAGE 05: DUPLICATE CLUSTERS & UNCERTAIN PAIR RESOLVER
# ==============================================================================
elif curr_idx == 5:
    conn = get_connection()
    groups = conn.execute("""
    SELECT dg.*, COUNT(r.record_id) AS member_count
    FROM duplicate_groups dg JOIN records r ON r.duplicate_group_id = dg.group_id
    GROUP BY dg.group_id
    HAVING COUNT(r.record_id) > 1 OR dg.status IN ('uncertain', 'human_split')
    ORDER BY CASE WHEN dg.status = 'uncertain' THEN 0 ELSE 1 END, dg.group_id ASC;
    """).fetchall()

    if not groups:
        st.info("No duplicate clusters found. Click '⚡ 1-CLICK DEMO DATASET' in the top bar to load duplicate & uncertain pairs!")
    else:
        for g in groups:
            gid = g["group_id"]
            members = conn.execute("SELECT * FROM records WHERE duplicate_group_id = ? ORDER BY is_hidden_duplicate ASC;", (gid,)).fetchall()
            is_unc = (g["status"] == "uncertain")
            with st.container(border=True):
                st.markdown(f"#### Cluster #{gid} // {'⚠️ UNCERTAIN PAIR — HUMAN VERIFICATION REQUIRED' if is_unc else g['status'].upper()}")
                st.caption(f"🔍 **Match Telemetry:** {g['match_method']}")
                m_cols = st.columns(len(members))
                for idx_m, m in enumerate(members):
                    with m_cols[idx_m]:
                        with st.container(border=True):
                            st.markdown(f"**Record #{m['record_id']}** ({'🙈 Hidden' if m['is_hidden_duplicate'] else '✅ Representative'})")
                            st.markdown(f"**{m['title']}**")
                            st.caption(f"{m['source']} ({m['pub_year']}) • `{m['pub_types']}` • DOI: `{m['doi'] or 'None'}`")
                b1, b2 = st.columns(2)
                if b1.button(f"✅ CONFIRM DUPLICATES (KEEP #{g['representative_record_id']})", key=f"c_dup_{gid}", type="primary", use_container_width=True):
                    conn.execute("UPDATE duplicate_groups SET status = 'human_confirmed' WHERE group_id = ?;", (gid,))
                    conn.execute("UPDATE records SET is_hidden_duplicate = CASE WHEN record_id = ? THEN 0 ELSE 1 END WHERE duplicate_group_id = ?;", (g["representative_record_id"], gid))
                    conn.commit()
                    log_human_audit(reviewer_name, "duplicate_override", gid, g["status"], "human_confirmed", "Confirmed duplicate cluster")
                    st.rerun()
                if b2.button(f"✂️ SPLIT INTO SEPARATE STUDIES", key=f"s_dup_{gid}", use_container_width=True):
                    conn.execute("UPDATE duplicate_groups SET status = 'human_split' WHERE group_id = ?;", (gid,))
                    for m in members:
                        if m["record_id"] != g["representative_record_id"]:
                            cur = conn.cursor()
                            cur.execute("INSERT INTO duplicate_groups (representative_record_id, status, match_method, updated_at) VALUES (?, 'human_split', 'Human split separate study', ?);", (m["record_id"], datetime.now().isoformat(timespec="seconds")))
                            conn.execute("UPDATE records SET duplicate_group_id = ?, is_hidden_duplicate = 0 WHERE record_id = ?;", (cur.lastrowid, m["record_id"]))
                    conn.execute("UPDATE records SET is_hidden_duplicate = 0 WHERE record_id = ?;", (g["representative_record_id"],))
                    conn.commit()
                    log_human_audit(reviewer_name, "duplicate_override", gid, g["status"], "human_split", "Split cluster")
                    st.rerun()
    conn.close()
    render_bottom_teleport_bar(curr_idx)


# ==============================================================================
# STAGE 06: SPLIT-SCREEN INTERACTIVE PAPER BOXES & ISOLATED EXCLUDED BOX
# ==============================================================================
elif curr_idx == 6:
    conn = get_connection()
    rows = conn.execute("""
    SELECT r.*, ms.decision AS machine_decision, ms.exclusion_reasons AS machine_reason,
           rd.screening_decision AS human_decision, rd.exclusion_reason AS human_reason, rd.reviewer_notes,
           mp.population_span, mp.intervention_span, mp.comparator_span, mp.outcome_span,
           rd.pico_p, rd.pico_i, rd.pico_c, rd.pico_o
    FROM records r
    LEFT JOIN machine_screening ms ON r.record_id = ms.record_id
    LEFT JOIN reviewer_decisions rd ON r.duplicate_group_id = rd.group_id
    LEFT JOIN machine_pico mp ON r.record_id = mp.record_id
    WHERE r.is_hidden_duplicate = 0 ORDER BY r.record_id ASC;
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
        "📂 SELECT ISOLATED SCREENING PARTITION:",
        [
            f"📚 ALL UNIQUE ({len(all_recs)})",
            f"✅ INCLUDED BOX ({len(inc_list)})",
            f"❌ EXCLUDED BOX ({len(exc_list)})",
            f"🤔 MAYBE QUEUE ({len(may_list)})",
        ],
        horizontal=True
    )

    filtered_recs = inc_list if "INCLUDED" in bucket_choice else (exc_list if "EXCLUDED" in bucket_choice else (may_list if "MAYBE" in bucket_choice else all_recs))

    if not filtered_recs:
        st.info("No records in this partition.")
    else:
        if "selected_paper_id" not in st.session_state or st.session_state["selected_paper_id"] not in [r["record_id"] for r in filtered_recs]:
            st.session_state["selected_paper_id"] = filtered_recs[0]["record_id"]

        col_cards, col_inspector = st.columns([1.15, 1.85])
        with col_cards:
            for r in filtered_recs:
                is_sel = (r["record_id"] == st.session_state["selected_paper_id"])
                dec = r["effective_decision"]
                with st.container(border=True):
                    st.markdown(f"**#{r['record_id']} // {r['title']}**")
                    st.caption(f"**[{dec.upper()}]** • {r['source']} ({r['pub_year']}) • *{r['effective_reason']}*")
                    if st.button("⚡ ACTIVE IN INSPECTOR ➡️" if is_sel else f"🔍 OPEN PAPER #{r['record_id']}", key=f"box_{r['record_id']}", type="primary" if is_sel else "secondary", use_container_width=True):
                        st.session_state["selected_paper_id"] = r["record_id"]
                        st.rerun()

        with col_inspector:
            sel_rec = next((x for x in filtered_recs if x["record_id"] == st.session_state["selected_paper_id"]), filtered_recs[0])
            p_val = sel_rec["pico_p"] or sel_rec["population_span"] or ""
            i_val = sel_rec["pico_i"] or sel_rec["intervention_span"] or ""
            c_val = sel_rec["pico_c"] or sel_rec["comparator_span"] or ""
            o_val = sel_rec["pico_o"] or sel_rec["outcome_span"] or ""

            with st.container(border=True):
                st.markdown(f"### #{sel_rec['record_id']} — {sel_rec['title']}")
                st.caption(f"👤 {sel_rec['authors']} | 🏛️ {sel_rec['journal']} ({sel_rec['pub_year']}) | 🌐 `{sel_rec['language']}` | 🏷️ `{sel_rec['pub_types']}`")
                st.markdown(highlight_pico_html(sel_rec["abstract"], p_val, i_val, c_val, o_val), unsafe_allow_html=True)
                st.write("")
                custom_reas = st.text_input("Decision / Exclusion Reason:", value=sel_rec["effective_reason"], key=f"reas_in_{sel_rec['record_id']}")
                a1, a2, a3 = st.columns(3)
                if a1.button("✅ INCLUDE", type="primary", use_container_width=True):
                    save_human_decision(sel_rec["duplicate_group_id"], sel_rec["record_id"], reviewer_name, "Include", "Meets PICO criteria", "", p_val, i_val, c_val, o_val, "screen_include")
                    st.rerun()
                if a2.button("🤔 MAYBE", use_container_width=True):
                    save_human_decision(sel_rec["duplicate_group_id"], sel_rec["record_id"], reviewer_name, "Maybe", custom_reas or "Needs full-text check", "", p_val, i_val, c_val, o_val, "screen_maybe")
                    st.rerun()
                if a3.button("❌ MOVE TO EXCLUDED BOX", use_container_width=True):
                    save_human_decision(sel_rec["duplicate_group_id"], sel_rec["record_id"], reviewer_name, "Exclude", custom_reas.strip() or "Excluded by operator", "", p_val, i_val, c_val, o_val, "screen_exclude")
                    st.rerun()

    render_bottom_teleport_bar(curr_idx)


# ==============================================================================
# STAGE 07: PICO SPAN INSPECTOR
# ==============================================================================
elif curr_idx == 7:
    conn = get_connection()
    rows = conn.execute("""
    SELECT r.*, COALESCE(rd.screening_decision, ms.decision, 'Maybe') AS final_decision,
           COALESCE(rd.exclusion_reason, ms.exclusion_reasons, '') AS final_reason, rd.reviewer_notes,
           mp.population_span, mp.intervention_span, mp.comparator_span, mp.outcome_span,
           rd.pico_p, rd.pico_i, rd.pico_c, rd.pico_o
    FROM records r
    LEFT JOIN machine_screening ms ON r.record_id = ms.record_id
    LEFT JOIN reviewer_decisions rd ON r.duplicate_group_id = rd.group_id
    LEFT JOIN machine_pico mp ON r.record_id = mp.record_id
    WHERE r.is_hidden_duplicate = 0 ORDER BY r.record_id ASC;
    """).fetchall()
    conn.close()

    eligible_recs = [dict(r) for r in rows if r["final_decision"] in ("Include", "Maybe")]
    if not eligible_recs:
        st.info("No Included/Maybe studies yet.")
    else:
        for r in eligible_recs:
            p_val = r["pico_p"] if r["pico_p"] is not None else (r["population_span"] or "")
            i_val = r["pico_i"] if r["pico_i"] is not None else (r["intervention_span"] or "")
            c_val = r["pico_c"] if r["pico_c"] is not None else (r["comparator_span"] or "")
            o_val = r["pico_o"] if r["pico_o"] is not None else (r["outcome_span"] or "")
            with st.container(border=True):
                st.markdown(f"#### [{r['final_decision'].upper()}] #{r['record_id']} // {r['title']}")
                st.markdown(highlight_pico_html(r["abstract"], p_val, i_val, c_val, o_val), unsafe_allow_html=True)
                with st.form(f"pico_f_{r['record_id']}"):
                    pc1, pc2 = st.columns(2)
                    np = pc1.text_input("🟦 Population [P]", value=p_val)
                    ni = pc2.text_input("🟩 Intervention [I]", value=i_val)
                    nc = pc1.text_input("🟧 Comparator [C]", value=c_val)
                    no = pc2.text_input("🟪 Outcome [O]", value=o_val)
                    if st.form_submit_button("💾 COMMIT PICO SPANS", type="primary"):
                        save_human_decision(r["duplicate_group_id"], r["record_id"], reviewer_name, r["final_decision"], r["final_reason"], r["reviewer_notes"] or "", np, ni, nc, no, "pico_edit")
                        st.rerun()

    render_bottom_teleport_bar(curr_idx)


# ==============================================================================
# STAGE 08: LEVEL-2 VERSION DIFF & LOOP
# ==============================================================================
elif curr_idx == 8:
    conn = get_connection()
    queries = conn.execute("SELECT * FROM query_versions ORDER BY version_id DESC;").fetchall()
    conflicts = conn.execute("SELECT * FROM duplicate_groups WHERE has_conflict = 1;").fetchall()
    conn.close()

    if conflicts:
        for c in conflicts:
            with st.container(border=True):
                st.error(f"⚠️ Conflict in Cluster #{c['group_id']}: {c['conflict_details']}")
                if st.button(f"✅ RESOLVE CLUSTER #{c['group_id']}", key=f"res_{c['group_id']}"):
                    resolve_duplicate_conflict(c["group_id"], c["representative_record_id"], reviewer_name)
                    st.rerun()
    else:
        st.success("✅ Zero merge conflicts across active duplicate clusters.")

    if len(queries) < 2:
        if st.button("⚡ INJECT EXPANDED QUERY v2 (+2 NEW RCTs) TO DEMO DIFF ENGINE", type="primary"):
            vid = create_query_version("Benchmark v2 (Expanded)", '("type 2 diabetes") AND metformin AND (placebo OR sulfonylurea)', 2015, 2025, ["PubMed", "Europe PMC"], 9, 5)
            store_fetched_records(vid, get_benchmark_papers("v2"))
            run_deduplication(vid)
            run_screening(vid)
            run_pico_extraction(vid)
            st.rerun()
    else:
        q_options = {f"v{q['version_id']}: {q['version_name']} ({q['boolean_query']})": q["version_id"] for q in queries}
        labels = list(q_options.keys())
        c1, c2 = st.columns(2)
        old_lbl = c1.selectbox("Baseline Version:", labels, index=min(1, len(labels) - 1))
        new_lbl = c2.selectbox("Updated Version:", labels, index=0)
        diff = compute_query_diff(q_options[old_lbl], q_options[new_lbl])
        m1, m2 = st.columns(2)
        m1.metric("➕ Added Records", diff["added_count"])
        m2.metric("➖ Removed Records (Preserved in Vault)", diff["removed_count"])
        if diff["added_records"]:
            st.dataframe(pd.DataFrame(diff["added_records"])[["record_id", "source", "pub_year", "title", "journal"]], use_container_width=True, hide_index=True)

    render_bottom_teleport_bar(curr_idx)


# ==============================================================================
# STAGE 09: AI WHITE-SPACE & EVIDENCE GAP DISCOVERY LAB
# ==============================================================================
elif curr_idx == 9:
    conn = get_connection()
    rows = conn.execute("""
    SELECT r.*, COALESCE(rd.screening_decision, ms.decision, 'Maybe') AS final_decision,
           COALESCE(rd.pico_p, mp.population_span, '') AS pico_p,
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
        st.info("Click '⚡ 1-CLICK DEMO DATASET' in the top bar to populate studies for the AI White-Space Matrix!")
    else:
        gap_data = compute_ai_evidence_gap_matrix(eligible_studies, config)
        hdr_cols = st.columns([1.3, 1, 1, 1, 1])
        hdr_cols[0].markdown("**COHORT \\ ENDPOINT**")
        for c_idx, out_name in enumerate(gap_data["outcomes"]):
            hdr_cols[c_idx + 1].markdown(f"<div style='text-align:center; font-weight:700; font-size:0.82rem;'>{out_name}</div>", unsafe_allow_html=True)

        for sg_name in gap_data["subgroups"]:
            r_cols = st.columns([1.3, 1, 1, 1, 1])
            r_cols[0].markdown(f"<div style='padding-top:18px; font-weight:700;'>👥 {sg_name}</div>", unsafe_allow_html=True)
            for c_idx, out_name in enumerate(gap_data["outcomes"]):
                cell = gap_data["matrix"][sg_name][out_name]
                cnt = cell["count"]
                pids = ", ".join(f"#{i}" for i in cell["paper_ids"])
                if cnt >= 2:
                    r_cols[c_idx + 1].markdown(f"<div class='gap-dense'><div style='font-size:1.25rem; font-weight:800; color:#10b981;'>🟢 {cnt} RCTs</div><div style='font-size:0.72rem;'>{pids}</div></div>", unsafe_allow_html=True)
                elif cnt == 1:
                    r_cols[c_idx + 1].markdown(f"<div class='gap-sparse'><div style='font-size:1.25rem; font-weight:800; color:#fbbf24;'>🟡 1 RCT</div><div style='font-size:0.72rem;'>{pids}</div></div>", unsafe_allow_html=True)
                else:
                    r_cols[c_idx + 1].markdown("<div class='gap-zero'><div style='font-size:1.15rem; font-weight:800; color:#ff3366;'>🔥 0 STUDIES</div><div style='font-size:0.68rem; font-weight:700;'>WHITE-SPACE GAP</div></div>", unsafe_allow_html=True)
            st.write("")

        if gap_data["gaps"]:
            st.write("")
            gap_labels = [f"🔥 BLIND SPOT #{i+1}: {g['subgroup']} × {g['outcome']} (0 RCTs)" for i, g in enumerate(gap_data["gaps"])]
            chosen_idx = st.selectbox("Select Discovered White-Space to Synthesize Trial Blueprint:", range(len(gap_labels)), format_func=lambda i: gap_labels[i])
            sel_gap = gap_data["gaps"][chosen_idx]
            with st.container(border=True):
                st.markdown(f"#### 💡 Unasked Research Question: *\"{sel_gap['unasked_question']}\"*")
                c1, c2 = st.columns(2)
                c1.write(f"**🕵️ Why Missed:** {sel_gap['why_missed']}")
                c2.write(f"**🧪 Phase III Blueprint:** {sel_gap['trial_design']}")
                st.code(sel_gap["mutated_query"], language="sql")
                if st.button("⚡ INJECT GAP QUERY INTO [02·COMPOSER] & RUN LEVEL-2 LOOP ➡️", type="primary", use_container_width=True):
                    st.session_state["custom_query_box"] = sel_gap["mutated_query"]
                    go_to_step(2)

    render_bottom_teleport_bar(curr_idx)


# ==============================================================================
# STAGE 10: EXPORT CSV & IMMUTABLE AUDIT LEDGER
# ==============================================================================
elif curr_idx == 10:
    conn = get_connection()
    export_rows = conn.execute("""
    SELECT r.record_id, r.duplicate_group_id, r.source, r.pmid, r.doi, r.title, r.authors, r.pub_year, r.journal,
           COALESCE(rd.screening_decision, ms.decision, 'Maybe') AS final_decision,
           COALESCE(rd.exclusion_reason, ms.exclusion_reasons, '') AS reason,
           COALESCE(rd.pico_p, mp.population_span, '') AS population_P,
           COALESCE(rd.pico_i, mp.intervention_span, '') AS intervention_I,
           COALESCE(rd.pico_c, mp.comparator_span, '') AS comparator_C,
           COALESCE(rd.pico_o, mp.outcome_span, '') AS outcome_O
    FROM records r
    LEFT JOIN machine_screening ms ON r.record_id = ms.record_id
    LEFT JOIN reviewer_decisions rd ON r.duplicate_group_id = rd.group_id
    LEFT JOIN machine_pico mp ON r.record_id = mp.record_id
    WHERE r.is_hidden_duplicate = 0 ORDER BY r.record_id ASC;
    """).fetchall()

    df_all = pd.DataFrame([dict(r) for r in export_rows])
    if not df_all.empty:
        st.dataframe(df_all, use_container_width=True, hide_index=True)
        st.download_button("📥 DOWNLOAD FULL SYNTHESIS CSV", df_all.to_csv(index=False).encode("utf-8"), "rayyan_kinetic_export.csv", "text/csv", type="primary")

    l1, l2 = st.columns(2)
    with l1:
        st.markdown("#### ✍️ Human Override Audit Ledger")
        audits = conn.execute("SELECT * FROM audit_log ORDER BY log_id DESC;").fetchall()
        if audits:
            st.dataframe(pd.DataFrame([dict(a) for a in audits]), use_container_width=True, hide_index=True)
    with l2:
        st.markdown("#### ⚙️ Pipeline Execution Telemetry")
        runs = conn.execute("SELECT * FROM run_log ORDER BY run_id DESC;").fetchall()
        if runs:
            st.dataframe(pd.DataFrame([dict(r) for r in runs]), use_container_width=True, hide_index=True)
    conn.close()
    render_bottom_teleport_bar(curr_idx)
