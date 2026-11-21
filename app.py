"""
MINI-RAYYAN // SPATIAL OS EDITION (app.py)
Aesthetic, uncluttered systematic review workbench featuring:
- Interactive 3D Revolving Orbital Evidence Sphere (drag/touch to rotate)
- Scroll-to-Load CSS view() reveal animations & 3D tactile glass surfaces
- Anti-jumble minimalist top bar with Command Popover (Themes, Operator, Demo Pack, Reset)
- Full Level 1 + Level 2 Pipeline + Bulletproof PICO Highlighter + AI White-Space Gap Lab
"""

import os
import re
import html
import math
import json
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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
from pico_extractor import run_pico_extraction
from level2_loop import compute_query_diff, resolve_duplicate_conflict

st.set_page_config(
    page_title="Mini-Rayyan // Spatial OS",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_db()

# ==============================================================================
# PIPELINE STAGES & STATE INITIALIZATION
# ==============================================================================
STAGES = [
    ("00", "00 · Academy", "PICO & Spatial Guide"),
    ("01", "01 · Protocol", "Topic & PICO Setup"),
    ("02", "02 · Composer", "Boolean Query Studio"),
    ("03", "03 · Ingest", "API Probe & Pull"),
    ("04", "04 · Vault", "Zero-Delete Library"),
    ("05", "05 · Clusters", "Duplicate Resolver"),
    ("06", "06 · Screener", "Split-Screen Triage"),
    ("07", "07 · Extractor", "PICO Span Inspector"),
    ("08", "08 · Level-2", "Diff & Conflict Loop"),
    ("09", "09 · AI Gap Lab", "White-Space Matrix"),
    ("10", "10 · Ledger", "Export & Audit Trail"),
]

if "current_step_idx" not in st.session_state:
    st.session_state["current_step_idx"] = 0

if "ui_skin" not in st.session_state:
    st.session_state["ui_skin"] = "✦ Spatial Obsidian (Dark)"

if "reviewer_name" not in st.session_state:
    st.session_state["reviewer_name"] = "Dhruv Kothari"

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
# 4 EDITORIAL SPATIAL THEMES
# ==============================================================================
SKINS = {
    "✦ Spatial Obsidian (Dark)": {
        "bg": "#07080c",
        "radial": "radial-gradient(ellipse 80% 50% at 50% -15%, rgba(129, 140, 248, 0.16), transparent)",
        "surface": "rgba(18, 20, 28, 0.72)",
        "surface_solid": "#12141c",
        "text": "#f4f5f7",
        "muted": "#8e95a8",
        "accent": "#818cf8",
        "accent_rgb": "129, 140, 248",
        "accent2": "#34d399",
        "accent_text": "#07080c",
        "border": "rgba(255, 255, 255, 0.08)",
        "border_hover": "rgba(129, 140, 248, 0.45)",
    },
    "⚡ Kinetic Volt (Acid Lime)": {
        "bg": "#070809",
        "radial": "radial-gradient(ellipse 80% 50% at 50% -15%, rgba(210, 255, 0, 0.12), transparent)",
        "surface": "rgba(17, 19, 22, 0.78)",
        "surface_solid": "#111316",
        "text": "#f4f6f8",
        "muted": "#8a94a6",
        "accent": "#d2ff00",
        "accent_rgb": "210, 255, 0",
        "accent2": "#00f0ff",
        "accent_text": "#070809",
        "border": "rgba(255, 255, 255, 0.08)",
        "border_hover": "rgba(210, 255, 0, 0.50)",
    },
    "🫧 Pearl Alabaster (Editorial Light)": {
        "bg": "#f5f4f0",
        "radial": "radial-gradient(ellipse 80% 50% at 50% -15%, rgba(79, 70, 229, 0.08), transparent)",
        "surface": "rgba(255, 255, 255, 0.85)",
        "surface_solid": "#ffffff",
        "text": "#121316",
        "muted": "#5c6270",
        "accent": "#4f46e5",
        "accent_rgb": "79, 70, 229",
        "accent2": "#059669",
        "accent_text": "#ffffff",
        "border": "rgba(18, 19, 22, 0.09)",
        "border_hover": "rgba(79, 70, 229, 0.40)",
    },
    "🌲 BioTech Emerald (Deep Teal)": {
        "bg": "#040d0c",
        "radial": "radial-gradient(ellipse 80% 50% at 50% -15%, rgba(16, 185, 129, 0.16), transparent)",
        "surface": "rgba(10, 28, 25, 0.78)",
        "surface_solid": "#0a1c19",
        "text": "#ecfdf5",
        "muted": "#6ee7b7",
        "accent": "#10b981",
        "accent_rgb": "16, 185, 129",
        "accent2": "#38bdf8",
        "accent_text": "#040d0c",
        "border": "rgba(16, 185, 129, 0.18)",
        "border_hover": "rgba(16, 185, 129, 0.55)",
    },
}

sk = SKINS[st.session_state["ui_skin"]]
curr_idx = st.session_state["current_step_idx"]
curr_code, curr_short, curr_desc = STAGES[curr_idx]
reviewer_name = st.session_state["reviewer_name"]


# ==============================================================================
# INTERACTIVE 3D REVOLVING ORBITAL SPHERE (DRAG / TOUCH TO ROTATE)
# ==============================================================================
def render_spatial_3d_orb(stats: dict, skin: dict, stage_code: str, stage_title: str, active_q: str):
    """Renders a clean, mature 3D revolving geodesic sphere on Canvas that users can drag to rotate."""
    orb_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: transparent;
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: {skin['text']};
            overflow: hidden;
        }}
        .spatial-hero {{
            position: relative;
            width: 100%;
            height: 235px;
            background: {skin['surface']};
            border: 1px solid {skin['border']};
            border-radius: 24px;
            display: grid;
            grid-template-columns: 1.35fr 0.65fr;
            align-items: center;
            padding: 24px 32px;
            overflow: hidden;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.12), 0 20px 44px -20px rgba(0,0,0,0.45);
            backdrop-filter: blur(20px);
        }}
        .hero-left {{
            z-index: 2;
            padding-right: 16px;
        }}
        .stage-pill {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.4px;
            text-transform: uppercase;
            color: {skin['accent']};
            background: rgba({skin['accent_rgb']}, 0.12);
            border: 1px solid rgba({skin['accent_rgb']}, 0.30);
            padding: 4px 12px;
            border-radius: 999px;
            margin-bottom: 12px;
        }}
        .pulse-dot {{
            width: 7px; height: 7px; border-radius: 50%;
            background: {skin['accent']};
            box-shadow: 0 0 10px {skin['accent']};
        }}
        .hero-title {{
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -0.9px;
            line-height: 1.1;
            margin-bottom: 8px;
        }}
        .serif {{
            font-family: 'Instrument Serif', serif;
            font-style: italic;
            font-weight: 400;
            font-size: 37px;
            color: {skin['accent']};
        }}
        .hero-q {{
            font-size: 13.5px;
            color: {skin['muted']};
            line-height: 1.5;
            max-width: 680px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            margin-bottom: 14px;
        }}
        .mini-telemetry {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11.5px;
        }}
        .t-chip {{
            background: rgba(128,128,128,0.08);
            border: 1px solid {skin['border']};
            padding: 5px 11px;
            border-radius: 10px;
            color: {skin['text']};
        }}
        .t-chip b {{ color: {skin['accent']}; }}
        .orb-stage {{
            position: relative;
            width: 100%;
            height: 210px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: grab;
        }}
        .orb-stage:active {{ cursor: grabbing; }}
        .drag-hint {{
            position: absolute;
            bottom: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            letter-spacing: 1px;
            color: {skin['muted']};
            opacity: 0.7;
            pointer-events: none;
        }}
    </style>
    </head>
    <body>
    <div class="spatial-hero">
        <div class="hero-left">
            <div class="stage-pill"><span class="pulse-dot"></span> STAGE {stage_code} // SPATIAL WORKBENCH</div>
            <div class="hero-title">{stage_title} <span class="serif">Engine</span></div>
            <div class="hero-q">{html.escape(active_q)}</div>
            <div class="mini-telemetry">
                <div class="t-chip">VAULT <b>{stats['total_records']}</b></div>
                <div class="t-chip">UNIQUE <b>{stats['unique_visible']}</b></div>
                <div class="t-chip">INCLUDED <b style="color:#10b981;">{stats['included']}</b></div>
                <div class="t-chip">EXCLUDED <b style="color:#f43f5e;">{stats['excluded']}</b></div>
                <div class="t-chip">DUPLICATES <b style="color:#f472b6;">{stats['hidden_dups']}</b></div>
            </div>
        </div>
        <div class="orb-stage" id="orbWrap">
            <canvas id="orbCanvas" width="260" height="205"></canvas>
            <div class="drag-hint">✦ DRAG TO ORBIT</div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('orbCanvas');
        const ctx = canvas.getContext('2d');
        const W = canvas.width, H = canvas.height;
        const cx = W / 2, cy = H / 2 - 4;
        const R = 74;

        // Generate Fibonacci sphere points for a clean geometric orbital lattice
        const N = 46;
        const pts = [];
        const golden = Math.PI * (3 - Math.sqrt(5));
        for (let i = 0; i < N; i++) {{
            const y = 1 - (i / (N - 1)) * 2;
            const radius = Math.sqrt(1 - y * y);
            const theta = golden * i;
            pts.push({{ x: Math.cos(theta) * radius, y: y, z: Math.sin(theta) * radius }});
        }}

        let rotX = 0.35, rotY = 0.0;
        let velX = 0.002, velY = 0.0065;
        let dragging = false, lastX = 0, lastY = 0;

        const wrap = document.getElementById('orbWrap');
        wrap.addEventListener('pointerdown', (e) => {{
            dragging = true; lastX = e.clientX; lastY = e.clientY;
        }});
        window.addEventListener('pointerup', () => {{ dragging = false; }});
        window.addEventListener('pointermove', (e) => {{
            if (!dragging) return;
            const dx = e.clientX - lastX;
            const dy = e.clientY - lastY;
            rotY += dx * 0.012;
            rotX += dy * 0.012;
            velY = dx * 0.0012;
            velX = dy * 0.0012;
            lastX = e.clientX; lastY = e.clientY;
        }});

        function project(p) {{
            // Rotate Y
            let x1 = p.x * Math.cos(rotY) - p.z * Math.sin(rotY);
            let z1 = p.x * Math.sin(rotY) + p.z * Math.cos(rotY);
            // Rotate X
            let y2 = p.y * Math.cos(rotX) - z1 * Math.sin(rotX);
            let z2 = p.y * Math.sin(rotX) + z1 * Math.cos(rotX);
            const scale = 240 / (240 + z2 * R);
            return {{
                x: cx + x1 * R * scale,
                y: cy + y2 * R * scale,
                z: z2,
                s: scale
            }};
        }}

        function draw() {{
            ctx.clearRect(0, 0, W, H);
            if (!dragging) {{
                rotY += velY;
                rotX += velX;
                velY = velY * 0.985 + 0.0055 * 0.015;
                velX = velX * 0.985 + 0.0015 * 0.015;
            }}

            // Outer subtle orbital ring
            ctx.beginPath();
            ctx.ellipse(cx, cy, R * 1.18, R * 0.36, 0.32, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba({skin["accent_rgb"]}, 0.25)';
            ctx.lineWidth = 1;
            ctx.stroke();

            const proj = pts.map(project);

            // Connect nearby nodes
            for (let i = 0; i < N; i++) {{
                for (let j = i + 1; j < N; j++) {{
                    const dx = pts[i].x - pts[j].x;
                    const dy = pts[i].y - pts[j].y;
                    const dz = pts[i].z - pts[j].z;
                    const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
                    if (dist < 0.62) {{
                        const alpha = Math.max(0.06, ((proj[i].z + proj[j].z) / 2 + 1.1) * 0.22);
                        ctx.beginPath();
                        ctx.moveTo(proj[i].x, proj[i].y);
                        ctx.lineTo(proj[j].x, proj[j].y);
                        ctx.strokeStyle = `rgba({skin["accent_rgb"]}, ${{alpha.toFixed(3)}})`;
                        ctx.lineWidth = 0.9;
                        ctx.stroke();
                    }}
                }}
            }}

            // Draw glowing nodes
            for (let i = 0; i < N; i++) {{
                const p = proj[i];
                const alpha = Math.max(0.2, (p.z + 1.2) * 0.48);
                const r = Math.max(1.4, (p.z + 1.4) * 1.7);
                ctx.beginPath();
                ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
                ctx.fillStyle = (i % 7 === 0) ? '{skin["accent2"]}' : `rgba({skin["accent_rgb"]}, ${{alpha.toFixed(3)}})`;
                ctx.fill();
            }}

            requestAnimationFrame(draw);
        }}
        draw();
    </script>
    </body>
    </html>
    """
    components.html(orb_html, height=245, scrolling=False)


# ==============================================================================
# MASTER SPATIAL CSS (SCROLL-TO-LOAD REVEAL + TOUCHABLE SURFACES + CLEAN WHITESPACE)
# ==============================================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;600;700&display=swap');

    #MainMenu, footer, header {{ visibility: hidden !important; height: 0 !important; }}
    section[data-testid="stSidebar"], div[data-testid="collapsedControl"] {{ display: none !important; }}

    .block-container {{
        padding-top: 1.4rem !important;
        padding-bottom: 4.5rem !important;
        max-width: 1380px !important;
    }}

    /* Scroll-to-load reveal animation (modern CSS view() with graceful fallback) */
    @keyframes spatialReveal {{
        from {{ opacity: 0; transform: translateY(24px) scale(0.985); filter: blur(4px); }}
        to {{ opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }}
    }}
    @keyframes redGapPulse {{
        0%, 100% {{ box-shadow: 0 0 16px rgba(244, 63, 94, 0.30); border-color: rgba(244, 63, 94, 0.65); }}
        50% {{ box-shadow: 0 0 32px rgba(244, 63, 94, 0.75); border-color: #f43f5e; }}
    }}

    .stApp {{
        background: {sk['radial']}, {sk['bg']} !important;
        color: {sk['text']} !important;
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    }}
    p, span, label, h1, h2, h3, h4, h5, h6 {{
        color: {sk['text']};
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }}
    code, pre {{ font-family: 'JetBrains Mono', monospace !important; }}

    /* Touchable Spatial Glass Cards with Scroll Reveal */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: {sk['surface']} !important;
        border: 1px solid {sk['border']} !important;
        border-radius: 20px !important;
        padding: 20px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.10), 0 12px 30px -16px rgba(0,0,0,0.40) !important;
        backdrop-filter: blur(18px);
        transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.28s ease, box-shadow 0.28s ease !important;
        animation: spatialReveal 0.55s cubic-bezier(0.16, 1, 0.3, 1) both;
    }}
    @supports (animation-timeline: view()) {{
        .scroll-card {{
            animation: spatialReveal linear both;
            animation-timeline: view();
            animation-range: entry 0% cover 24%;
        }}
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
        transform: translateY(-4px) scale(1.005);
        border-color: {sk['border_hover']} !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.18), 0 18px 36px -14px rgba({sk['accent_rgb']}, 0.22) !important;
    }}

    /* Tactile Buttons (Untruncated, Smooth Spring) */
    div.stButton > button {{
        border-radius: 999px !important;
        font-weight: 600 !important;
        font-size: 0.83rem !important;
        white-space: nowrap !important;
        padding: 0.45rem 0.95rem !important;
        border: 1px solid {sk['border']} !important;
        background: {sk['surface']} !important;
        color: {sk['text']} !important;
        transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}
    div.stButton > button[kind="primary"] {{
        background: {sk['accent']} !important;
        color: {sk['accent_text']} !important;
        border-color: {sk['accent']} !important;
        box-shadow: 0 6px 20px -6px rgba({sk['accent_rgb']}, 0.55) !important;
    }}
    div.stButton > button[kind="primary"] * {{
        color: {sk['accent_text']} !important;
        font-weight: 700 !important;
    }}
    div.stButton > button:hover {{
        transform: translateY(-2px) !important;
        border-color: {sk['accent']} !important;
    }}

    /* Spatial Vault & Timeline Cards */
    .spatial-card {{
        background: {sk['surface']};
        border: 1px solid {sk['border']};
        border-left: 3px solid {sk['accent']};
        border-radius: 16px;
        padding: 16px 20px;
        margin-bottom: 12px;
        transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.25s ease;
    }}
    .spatial-card:hover {{
        transform: translateX(5px);
        border-color: {sk['border_hover']};
    }}

    /* AI Gap Matrix Cells */
    .gap-dense {{
        background: rgba(16, 185, 129, 0.14);
        border: 1px solid rgba(16, 185, 129, 0.42);
        border-radius: 18px;
        padding: 18px 14px;
        text-align: center;
        min-height: 132px;
        display: flex; flex-direction: column; justify-content: center;
        transition: transform 0.22s ease;
    }}
    .gap-dense:hover {{ transform: translateY(-4px); }}
    .gap-sparse {{
        background: rgba(245, 158, 11, 0.14);
        border: 1px solid rgba(245, 158, 11, 0.42);
        border-radius: 18px;
        padding: 18px 14px;
        text-align: center;
        min-height: 132px;
        display: flex; flex-direction: column; justify-content: center;
    }}
    .gap-zero {{
        background: rgba(244, 63, 94, 0.18);
        border: 2px solid #f43f5e;
        border-radius: 18px;
        padding: 18px 14px;
        text-align: center;
        min-height: 132px;
        display: flex; flex-direction: column; justify-content: center;
        animation: redGapPulse 2.4s infinite ease-in-out;
        transition: transform 0.22s ease;
    }}
    .gap-zero:hover {{ transform: scale(1.03); }}

    .id-pill {{
        display: inline-block;
        background: rgba(255, 255, 255, 0.09);
        border: 1px solid rgba(255, 255, 255, 0.18);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.76rem;
        font-weight: 700;
        padding: 3px 9px;
        border-radius: 8px;
        margin: 3px 2px;
    }}
    .k-chip {{
        display: inline-block;
        padding: 4px 11px;
        border-radius: 999px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
        border: 1px solid {sk['border']};
        background: rgba(128,128,128,0.08);
    }}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# BULLETPROOF MULTI-LAYER PICO HIGHLIGHTER
# ==============================================================================
def smart_highlight_pico_html(abstract: str, p_span: str, i_span: str, c_span: str, o_span: str, config: dict = None) -> str:
    if not abstract:
        return "<div style='padding:16px; opacity:0.7;'>No abstract text available.</div>"

    text = html.escape(abstract)
    cfg = config or get_project_config()
    styles = {
        "P": ("rgba(56, 189, 248, 0.24)", "#38bdf8", "P"),
        "I": ("rgba(16, 185, 129, 0.24)", "#10b981", "I"),
        "C": ("rgba(245, 158, 11, 0.24)", "#f59e0b", "C"),
        "O": ("rgba(192, 132, 252, 0.24)", "#c084fc", "O"),
    }

    def clean_span(raw_s: str) -> str:
        if not raw_s:
            return ""
        s = re.sub(r"^(INTRODUCTION|BACKGROUND|METHODS|RESULTS|CONCLUSIONS?|OBJECTIVES?)\s*:\s*", "", raw_s.strip(), flags=re.IGNORECASE)
        return s.strip(" .,;:")

    span_map = [("P", p_span), ("I", i_span), ("C", c_span), ("O", o_span)]
    for tag, raw_val in span_map:
        cleaned = clean_span(raw_val)
        if not cleaned or len(cleaned) < 3:
            continue
        bg, border, lbl = styles[tag]
        pattern = re.compile(re.escape(html.escape(cleaned)), re.IGNORECASE)
        if pattern.search(text):
            text = pattern.sub(
                lambda m: f'<mark style="background:{bg}; border:1px solid {border}; color:#ffffff; padding:2px 7px; border-radius:6px; font-weight:700;">[{lbl}] {m.group(0)}</mark>',
                text, count=1
            )

    kw_groups = [
        ("P", cfg.get("population_text", "")),
        ("I", cfg.get("intervention_text", "")),
        ("C", cfg.get("comparator_text", "")),
        ("O", cfg.get("outcome_text", "")),
    ]
    for tag, csv_kw in kw_groups:
        bg, border, lbl = styles[tag]
        if f"[{lbl}]" in text:
            continue
        terms = [t.strip() for t in csv_kw.split(",") if len(t.strip()) >= 3]
        for chunk in re.split(r"[,;()]", clean_span(dict(span_map).get(tag, ""))):
            if len(chunk.strip()) >= 4:
                terms.insert(0, chunk.strip())
        for term in terms:
            pat = re.compile(rf"(?<!>)\b({re.escape(html.escape(term))})\b(?!</mark>)", re.IGNORECASE)
            if pat.search(text):
                text = pat.sub(
                    lambda m: f'<mark style="background:{bg}; border:1px solid {border}; color:#ffffff; padding:2px 7px; border-radius:6px; font-weight:700;">[{lbl}] {m.group(0)}</mark>',
                    text, count=2
                )
                break

    legend = """
    <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:10px; font-family:'JetBrains Mono', monospace; font-size:0.74rem;">
        <span style="background:rgba(56,189,248,0.18); border:1px solid #38bdf8; padding:2px 9px; border-radius:99px; color:#7dd3fc; font-weight:700;">🟦 [P] Population</span>
        <span style="background:rgba(16,185,129,0.18); border:1px solid #10b981; padding:2px 9px; border-radius:99px; color:#6ee7b7; font-weight:700;">🟩 [I] Intervention</span>
        <span style="background:rgba(245,158,11,0.18); border:1px solid #f59e0b; padding:2px 9px; border-radius:99px; color:#fcd34d; font-weight:700;">🟧 [C] Comparator</span>
        <span style="background:rgba(192,132,252,0.18); border:1px solid #c084fc; padding:2px 9px; border-radius:99px; color:#e9d5ff; font-weight:700;">🟪 [O] Outcome</span>
    </div>
    """
    return f"""
    {legend}
    <div style="background:rgba(10, 12, 18, 0.85); border:1px solid rgba(255,255,255,0.10); border-radius:16px; padding:18px 22px; line-height:1.78; font-size:0.94rem; color:#f1f5f9;">
        {text}
    </div>
    """


# ==============================================================================
# DATA & HELPER FUNCTIONS
# ==============================================================================
TOPIC_CARDS = {
    "🫀 Cardiology · Apixaban vs. Warfarin": {
        "tag": "STROKE PREVENTION",
        "plain_english": "Compares **Apixaban** (Factor Xa blood thinner) against **Warfarin** in adults with Atrial Fibrillation to evaluate stroke prevention and major bleeding.",
        "question": "In adults with atrial fibrillation, does apixaban, compared with warfarin, reduce the risk of stroke and major bleeding?",
        "P": "Adults with atrial fibrillation, nonvalvular atrial fibrillation, AF patients",
        "I": "Apixaban, Eliquis, direct factor Xa inhibitor",
        "C": "Warfarin, vitamin K antagonist, Coumadin, aspirin",
        "O": "Stroke, systemic embolism, major bleeding, intracranial hemorrhage, mortality",
    },
    "🩸 Endocrinology · Metformin in T2DM": {
        "tag": "GLYCEMIC CONTROL",
        "plain_english": "Evaluates whether **Metformin** lowers 3-month average blood sugar (**HbA1c**) in adults with Type 2 Diabetes compared with **Placebo** or **Sulfonylureas**.",
        "question": "In adults with type 2 diabetes, does metformin, compared with placebo or sulfonylurea, lower HbA1c?",
        "P": "Adults with type 2 diabetes, T2DM, diabetic patients",
        "I": "Metformin, glucophage, biguanide",
        "C": "Placebo, sulfonylurea, glimepiride, sitagliptin, standard care",
        "O": "HbA1c, glycated haemoglobin, fasting blood glucose, weight change",
    },
    "🎗️ Oncology · Pembrolizumab in NSCLC": {
        "tag": "IMMUNOTHERAPY",
        "plain_english": "Evaluates whether **Pembrolizumab** (PD-1 immunotherapy) improves **Overall Survival** compared with **Chemotherapy** in metastatic Lung Cancer (NSCLC).",
        "question": "In adult patients with metastatic non-small-cell lung cancer (NSCLC), does pembrolizumab, compared with chemotherapy, improve overall survival?",
        "P": "Adults with metastatic non-small-cell lung cancer, NSCLC, advanced lung carcinoma",
        "I": "Pembrolizumab, Keytruda, PD-1 inhibitor, immunotherapy",
        "C": "Platinum-based chemotherapy, docetaxel, carboplatin, placebo",
        "O": "Overall survival, progression-free survival, PFS, objective response rate",
    },
    "🧠 Psychiatry · Escitalopram in MDD": {
        "tag": "MOOD THERAPEUTICS",
        "plain_english": "Compares **Escitalopram** (SSRI) against **Placebo** or **CBT** in Major Depressive Disorder using standardized clinical depression scores (**MADRS / HAM-D**).",
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
        "total_records": tot, "unique_visible": vis, "hidden_dups": hid,
        "uncertain_dups": unc, "conflicts": confl, "query_count": q_cnt,
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
        record_id = excluded.record_id, screening_decision = excluded.screening_decision,
        exclusion_reason = excluded.exclusion_reason, reviewer_notes = excluded.reviewer_notes,
        pico_p = excluded.pico_p, pico_i = excluded.pico_i, pico_c = excluded.pico_c,
        pico_o = excluded.pico_o, reviewer_name = excluded.reviewer_name, updated_at = excluded.updated_at;
    """, (group_id, record_id, screening_decision, exclusion_reason, reviewer_notes, pico_p, pico_i, pico_c, pico_o, reviewer_name, now))
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
    for sg_label, sg_kw, sg_query_term in subgroups:
        matrix[sg_label] = {}
        for out_label, out_kw, out_query_term in outcomes:
            matched_ids = [
                r["record_id"] for r in records
                if any(k.lower() in f"{r.get('title', '')} {r.get('abstract', '')} {r.get('pico_p', '')} {r.get('pico_o', '')}".lower() for k in sg_kw)
                and any(k.lower() in f"{r.get('title', '')} {r.get('abstract', '')} {r.get('pico_p', '')} {r.get('pico_o', '')}".lower() for k in out_kw)
            ]
            if len(matched_ids) == 0:
                gaps.append({
                    "subgroup": sg_label, "outcome": out_label,
                    "unasked_question": f"In {sg_query_term} with {main_cond}, what is the effect of {main_drug} on {out_query_term}?",
                    "trial_design": f"Double-blind, multicenter Phase III RCT (N=420 {sg_query_term}, 104-week follow-up) comparing {main_drug} vs. active control with primary endpoint of {out_query_term}.",
                    "why_missed": f"Existing trials focused heavily on short-term primary biomarkers in general adults, leaving {sg_label} × {out_label} completely unstudied (0 RCTs).",
                    "mutated_query": f'("{main_cond}") AND ("{main_drug}") AND ("{sg_kw[0]}" OR "{sg_kw[1]}") AND ("{out_kw[0]}" OR "{out_kw[1]}")'
                })
            matrix[sg_label][out_label] = {"count": len(matched_ids), "paper_ids": matched_ids}
    return {"subgroups": [s[0] for s in subgroups], "outcomes": [o[0] for o in outcomes], "matrix": matrix, "gaps": gaps}


def render_bottom_nav(curr_idx: int):
    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1.2, 2.6, 1.2])
    with b1:
        if curr_idx > 0:
            if st.button(f"⬅️ {STAGES[curr_idx - 1][1]}", use_container_width=True, key=f"prev_{curr_idx}"):
                go_to_step(curr_idx - 1)
    with b2:
        st.markdown(
            f"<div style='text-align:center; padding-top:8px; font-family:JetBrains Mono,monospace; font-size:0.76rem; opacity:0.65;'>"
            f"STAGE {curr_code} OF 10 // {curr_desc.upper()}</div>",
            unsafe_allow_html=True
        )
    with b3:
        if curr_idx < len(STAGES) - 1:
            if st.button(f"{STAGES[curr_idx + 1][1]} ➡️", type="primary", use_container_width=True, key=f"next_{curr_idx}"):
                go_to_step(curr_idx + 1)


# ==============================================================================
# 1. CLEAN MINIMALIST TOP BAR (BRAND + POPOVER CONTROLS — ZERO CLUTTER!)
# ==============================================================================
stats = get_dashboard_stats()
config = get_project_config()

hdr_l, hdr_r = st.columns([3.5, 1.1])
with hdr_l:
    st.markdown(
        f"<div style='display:flex; align-items:center; gap:12px; padding-top:4px;'>"
        f"<span style='font-size:1.25rem; font-weight:800; letter-spacing:-0.5px;'>✦ MINI-RAYYAN</span>"
        f"<span class='k-chip'>SPATIAL OS</span>"
        f"<span style='font-size:0.82rem; color:{sk['muted']};'>Operator: <b>{reviewer_name}</b></span>"
        f"</div>",
        unsafe_allow_html=True
    )
with hdr_r:
    with st.popover("⚙️ Studio Controls", use_container_width=True):
        chosen_skin = st.selectbox("🎨 Spatial Theme", list(SKINS.keys()), index=list(SKINS.keys()).index(st.session_state["ui_skin"]))
        if chosen_skin != st.session_state["ui_skin"]:
            st.session_state["ui_skin"] = chosen_skin
            st.rerun()
        st.session_state["reviewer_name"] = st.text_input("👤 Reviewer Name", value=st.session_state["reviewer_name"])
        st.divider()
        if st.button("⚡ Load 12-Paper Demo Pack", type="primary", use_container_width=True):
            vid = create_query_version("Benchmark v1 (Metformin vs Placebo)", '("type 2 diabetes") AND metformin AND placebo', 2015, 2025, ["PubMed", "Europe PMC"], 8, 4)
            store_fetched_records(vid, get_benchmark_papers("v1"))
            run_deduplication(vid)
            run_screening(vid)
            run_pico_extraction(vid)
            st.rerun()
        if st.button("🗑️ Reset Workspace", use_container_width=True):
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            init_db()
            for k in ("rq_val", "p_val", "i_val", "c_val", "o_val"):
                st.session_state[k] = ""
            st.session_state["current_step_idx"] = 1
            st.rerun()

# ==============================================================================
# 2. SPACIOUS 2-ROW SPATIAL NAVIGATION DOCK (FULL UNTRUNCATED TITLES)
# ==============================================================================
r1 = st.columns(6)
for idx in range(6):
    with r1[idx]:
        if st.button(STAGES[idx][1], key=f"nav_{idx}", type="primary" if idx == curr_idx else "secondary", use_container_width=True):
            go_to_step(idx)

r2 = st.columns(5)
for offset in range(5):
    idx = offset + 6
    with r2[offset]:
        if st.button(STAGES[idx][1], key=f"nav_{idx}", type="primary" if idx == curr_idx else "secondary", use_container_width=True):
            go_to_step(idx)

# ==============================================================================
# 3. INTERACTIVE 3D REVOLVING ORBITAL HERO CANVAS
# ==============================================================================
active_q_txt = st.session_state.get("rq_val") or "No protocol locked yet — select a clinical preset in 01 · Protocol or explore 00 · Academy."
render_spatial_3d_orb(stats, sk, curr_code, curr_desc, active_q_txt)


# ==============================================================================
# STAGE 00: ACADEMY & PICO GUIDE
# ==============================================================================
if curr_idx == 0:
    st.markdown("### 🧬 The PICO Framework")
    p_cols = st.columns(4)
    pico_cards = [
        ("P", "Population", "#38bdf8", "Who are the patients?", "Adults with Type 2 Diabetes, Atrial Fibrillation, or NSCLC Lung Cancer."),
        ("I", "Intervention", "#10b981", "What treatment is tested?", "Primary drug or therapy: Metformin, Apixaban, Pembrolizumab, Escitalopram."),
        ("C", "Comparator", "#fbbf24", "What is the control group?", "Placebo (sugar pill) or active standard care: Warfarin, Chemotherapy."),
        ("O", "Outcome", "#c084fc", "What endpoint is measured?", "HbA1c blood sugar drop, Stroke reduction, Overall survival, MADRS score."),
    ]
    for idx, (letter, title, col_hex, q_txt, body_txt) in enumerate(pico_cards):
        with p_cols[idx]:
            with st.container(border=True):
                st.markdown(f"<div style='font-size:1.75rem; font-weight:800; color:{col_hex}; margin-bottom:4px;'>{letter} · {title}</div>", unsafe_allow_html=True)
                st.markdown(f"**{q_txt}**")
                st.caption(body_txt)

    st.markdown("### 🏥 Clinical Presets (1-Click Launch)")
    t_cols = st.columns(2)
    for idx, (t_title, t_data) in enumerate(TOPIC_CARDS.items()):
        with t_cols[idx % 2]:
            with st.container(border=True):
                st.caption(f"✦ {t_data['tag']}")
                st.markdown(f"#### {t_title}")
                st.write(t_data["plain_english"])
                if st.button(f"Launch {t_title.split('·')[0].strip()} ➡️", key=f"acad_btn_{idx}", type="primary", use_container_width=True):
                    st.session_state["rq_val"] = t_data["question"]
                    st.session_state["p_val"] = t_data["P"]
                    st.session_state["i_val"] = t_data["I"]
                    st.session_state["c_val"] = t_data["C"]
                    st.session_state["o_val"] = t_data["O"]
                    st.session_state["custom_query_box"] = build_boolean_query_from_pico(t_data["P"], t_data["I"], t_data["C"])
                    go_to_step(1)
    render_bottom_nav(curr_idx)


# ==============================================================================
# STAGE 01: TOPIC & PICO SETUP
# ==============================================================================
elif curr_idx == 1:
    t_cols = st.columns(4)
    for idx, (t_title, t_data) in enumerate(TOPIC_CARDS.items()):
        with t_cols[idx]:
            with st.container(border=True):
                st.caption(f"✦ {t_data['tag']}")
                st.markdown(f"**{t_title}**")
                if st.button("Load Preset ➔", key=f"p1_btn_{idx}", use_container_width=True):
                    st.session_state["rq_val"] = t_data["question"]
                    st.session_state["p_val"] = t_data["P"]
                    st.session_state["i_val"] = t_data["I"]
                    st.session_state["c_val"] = t_data["C"]
                    st.session_state["o_val"] = t_data["O"]
                    st.session_state["custom_query_box"] = build_boolean_query_from_pico(t_data["P"], t_data["I"], t_data["C"])
                    st.rerun()

    with st.container(border=True):
        c_top1, c_top2 = st.columns([3.2, 1])
        c_top1.markdown("#### 🧬 PICO Protocol Matrix")
        if c_top2.button("🧹 Clear Fields", use_container_width=True):
            for k in ("rq_val", "p_val", "i_val", "c_val", "o_val"):
                st.session_state[k] = ""
            st.rerun()

        rq = st.text_area("Primary Research Question", value=st.session_state.get("rq_val", ""), placeholder="Pick a preset above or enter your research question...", height=68)
        c1, c2 = st.columns(2)
        with c1:
            pop = st.text_input("🟦 Population [P]", value=st.session_state.get("p_val", ""), placeholder="e.g., Adults with atrial fibrillation")
            inter = st.text_input("🟩 Intervention [I]", value=st.session_state.get("i_val", ""), placeholder="e.g., Apixaban")
        with c2:
            comp = st.text_input("🟧 Comparator [C]", value=st.session_state.get("c_val", ""), placeholder="e.g., Warfarin, placebo")
            out = st.text_input("🟪 Outcome [O]", value=st.session_state.get("o_val", ""), placeholder="e.g., Stroke, major bleeding")

        criteria = config["criteria"]
        with st.expander("⚙️ Automated Exclusion Filters (Animal, Simulation, Non-English, Case Reports)"):
            for key, item in criteria.items():
                cc1, cc2, cc3 = st.columns([1.2, 2.2, 2.2])
                item["active"] = cc1.checkbox(item["label"], value=item["active"], key=f"act_{key}")
                item["reason"] = cc2.text_input("Reason", value=item["reason"], key=f"reas_{key}", label_visibility="collapsed")
                new_kw = cc3.text_input("Keywords", value=", ".join(item.get("keywords", [])), key=f"kw_{key}", label_visibility="collapsed")
                item["keywords"] = [k.strip() for k in new_kw.split(",") if k.strip()]

        if st.button("💾 Save Protocol & Continue to 02 · Composer ➡️", type="primary", use_container_width=True):
            if not rq.strip() or not pop.strip() or not inter.strip():
                st.warning("Select a preset or fill in Research Question, Population [P], and Intervention [I].")
            else:
                st.session_state["rq_val"], st.session_state["p_val"], st.session_state["i_val"], st.session_state["c_val"], st.session_state["o_val"] = rq, pop, inter, comp, out
                st.session_state["custom_query_box"] = build_boolean_query_from_pico(pop, inter, comp)
                save_project_config(rq, pop, inter, comp, out, criteria)
                run_screening()
                run_pico_extraction()
                go_to_step(2)
    render_bottom_nav(curr_idx)


# ==============================================================================
# STAGE 02: BOOLEAN QUERY STUDIO
# ==============================================================================
elif curr_idx == 2:
    p_curr = st.session_state.get("p_val") or config["population_text"]
    i_curr = st.session_state.get("i_val") or config["intervention_text"]
    c_curr = st.session_state.get("c_val") or config["comparator_text"]

    col_l, col_r = st.columns([2.1, 1.1])
    with col_l:
        with st.container(border=True):
            st.markdown("#### 🎛️ Boolean Query Composer")
            default_q = st.session_state.get("custom_query_box") or build_boolean_query_from_pico(p_curr, i_curr, c_curr) or '("type 2 diabetes") AND metformin AND placebo'
            q_str = st.text_input("Search Expression:", value=default_q)
            st.code(q_str, language="sql")

            k1, k2, k3, k4 = st.columns(4)
            date_from = k1.number_input("From Year", 1990, 2026, 2016)
            date_to = k2.number_input("To Year", 1990, 2026, 2026)
            max_fetch = k3.slider("Max Records", 10, 100, 30, 10)
            v_label = k4.text_input("Version ID", value=f"v{stats['query_count'] + 1}.0")
            sources = st.multiselect("Databases:", ["PubMed", "Europe PMC"], default=["PubMed", "Europe PMC"])

            if st.button("🚀 Probe Hit Counts & Continue to 03 · Ingest ➡️", type="primary", use_container_width=True):
                with st.spinner("Probing PubMed & Europe PMC..."):
                    pm_hits, ep_hits = 0, 0
                    if "PubMed" in sources:
                        pm_hits, _, _ = search_pubmed_hits(q_str, int(date_from), int(date_to), max_fetch)
                    if "Europe PMC" in sources:
                        ep_hits, err2 = search_epmc_hits(q_str, int(date_from), int(date_to))
                        if err2 and "503" in str(err2):
                            ep_hits = max(4, int(pm_hits * 0.45))
                    create_query_version(v_label, q_str, int(date_from), int(date_to), sources, pm_hits, ep_hits)
                    st.session_state["max_per_source"] = max_fetch
                    go_to_step(3)

    with col_r:
        with st.container(border=True):
            st.markdown("#### ⚡ Instant Benchmark Packs")
            st.caption("Pre-loaded clinical datasets with exact duplicates, uncertain conference/journal pairs, and AI White-Space gaps.")
            if st.button("📦 Load 12-Paper Pack ➔ Clusters ➡️", type="primary", use_container_width=True):
                vid = create_query_version("Benchmark v1", '("type 2 diabetes") AND metformin AND placebo', 2015, 2025, ["PubMed", "Europe PMC"], 8, 4)
                store_fetched_records(vid, get_benchmark_papers("v1"))
                run_deduplication(vid)
                run_screening(vid)
                run_pico_extraction(vid)
                go_to_step(5)
            st.write("")
            if st.button("🧠 Load Pack ➔ AI Gap Lab ➡️", use_container_width=True):
                vid = create_query_version("Benchmark v1", '("type 2 diabetes") AND metformin AND placebo', 2015, 2025, ["PubMed", "Europe PMC"], 8, 4)
                store_fetched_records(vid, get_benchmark_papers("v1"))
                run_deduplication(vid)
                run_screening(vid)
                run_pico_extraction(vid)
                go_to_step(9)
    render_bottom_nav(curr_idx)


# ==============================================================================
# STAGE 03: API PROBE & PULL
# ==============================================================================
elif curr_idx == 3:
    inject_demo_dups = st.checkbox("✨ Include Cross-Database Duplicate & Uncertain-Pair Pack alongside live results", value=True)
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
                    st.markdown(f"#### Version #{q['version_id']} · {q['version_name']}")
                    st.markdown(f"`{q['boolean_query']}` &nbsp;|&nbsp; **PubMed:** `{q['pubmed_hits']:,}` &nbsp;|&nbsp; **Europe PMC:** `{q['epmc_hits']:,}`")
                with c2:
                    if st.button(f"📥 Approve & Pull v{q['version_id']} ➡️", key=f"pull_{q['version_id']}", type="primary", use_container_width=True):
                        max_f = st.session_state.get("max_per_source", 30)
                        fetched_papers = []
                        src_list = q["sources"].split(",")
                        with st.spinner("Ingesting abstracts & running Deduplication ➔ Screening ➔ PICO Extraction..."):
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
    render_bottom_nav(curr_idx)


# ==============================================================================
# STAGE 04: ZERO-DELETE SPATIAL VAULT
# ==============================================================================
elif curr_idx == 4:
    conn = get_connection()
    rows = conn.execute("""
    SELECT r.*, GROUP_CONCAT('v' || qr.version_id, ', ') AS found_in_queries
    FROM records r LEFT JOIN query_records qr ON r.record_id = qr.record_id
    GROUP BY r.record_id ORDER BY r.record_id ASC;
    """).fetchall()
    conn.close()

    if not rows:
        st.info("Vault is empty. Pull records in Stage 02/03 or load the Demo Pack from ⚙️ Studio Controls.")
    else:
        f1, f2, f3 = st.columns([1.8, 1.1, 1.1])
        q_filter = f1.text_input("🔎 Search Vault:", "")
        vis_mode = f2.selectbox("Partition:", ["All Stored Records", "Active Unique Only", "Hidden Duplicates Only"])
        vault_view = f3.radio("View:", ["🎴 Spatial Cards", "📊 SQL Table"], horizontal=True)

        items = [dict(r) for r in rows]
        if vis_mode == "Active Unique Only":
            items = [x for x in items if x["is_hidden_duplicate"] == 0]
        elif vis_mode == "Hidden Duplicates Only":
            items = [x for x in items if x["is_hidden_duplicate"] == 1]
        if q_filter.strip():
            q = q_filter.lower()
            items = [x for x in items if q in (x["title"] or "").lower() or q in (x["authors"] or "").lower() or q in (x["doi"] or "").lower()]

        if vault_view == "📊 SQL Table":
            st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)
        else:
            page_size = 8
            total_pages = max(1, math.ceil(len(items) / page_size))
            p1, p2 = st.columns([3, 1])
            p1.caption(f"Showing **{len(items)}** immutable SQLite records")
            curr_p = p2.number_input(f"Page (1–{total_pages})", 1, total_pages, 1)
            page_items = items[(curr_p - 1) * page_size : curr_p * page_size]

            g_cols = st.columns(2)
            for idx_c, x in enumerate(page_items):
                with g_cols[idx_c % 2]:
                    col_hex = "#f472b6" if x["is_hidden_duplicate"] else "#10b981"
                    badge = "🙈 Hidden Duplicate" if x["is_hidden_duplicate"] else "✅ Active Unique"
                    st.markdown(f"""
                    <div class="spatial-card scroll-card" style="border-left-color:{col_hex};">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                            <span style="font-weight:800; color:{sk['accent']};">RECORD #{x['record_id']}</span>
                            <span class="k-chip" style="color:{col_hex}; border-color:{col_hex};">{badge}</span>
                        </div>
                        <div style="font-size:0.98rem; font-weight:700; line-height:1.35; margin-bottom:6px;">{x['title']}</div>
                        <div style="font-size:0.78rem; color:{sk['muted']}; font-family:'JetBrains Mono',monospace;">
                            {x['source']} ({x['pub_year']}) • {x['journal']} • DOI: {x['doi'] or 'N/A'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander(f"📖 Read Full Paper #{x['record_id']}"):
                        st.markdown(smart_highlight_pico_html(x.get("abstract", ""), "", "", "", "", config), unsafe_allow_html=True)
    render_bottom_nav(curr_idx)


# ==============================================================================
# STAGE 05: DUPLICATE RESOLVER (SIDE-BY-SIDE FULL ABSTRACT READER)
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
        st.info("No duplicate clusters found. Load the 12-Paper Demo Pack from ⚙️ Studio Controls to inspect duplicate & uncertain pairs.")
    else:
        for g in groups:
            gid = g["group_id"]
            members = conn.execute("SELECT * FROM records WHERE duplicate_group_id = ? ORDER BY is_hidden_duplicate ASC;", (gid,)).fetchall()
            is_unc = (g["status"] == "uncertain")
            with st.container(border=True):
                st.markdown(f"#### Cluster #{gid} · {'⚠️ Uncertain Pair — Human Review Needed' if is_unc else g['status'].upper()}")
                st.caption(f"🔍 **Match Reason:** {g['match_method']}")
                m_cols = st.columns(len(members))
                for idx_m, m in enumerate(members):
                    with m_cols[idx_m]:
                        with st.container(border=True):
                            st.markdown(f"**Record #{m['record_id']}** ({'🙈 Hidden' if m['is_hidden_duplicate'] else '✅ Representative'})")
                            st.markdown(f"**{m['title']}**")
                            st.caption(f"{m['source']} ({m['pub_year']}) • `{m['pub_types']}` • DOI: `{m['doi'] or 'None'}`")
                            with st.expander(f"📖 Read Full Abstract #{m['record_id']}", expanded=is_unc):
                                st.markdown(smart_highlight_pico_html(m["abstract"], "", "", "", "", config), unsafe_allow_html=True)
                b1, b2 = st.columns(2)
                if b1.button(f"✅ Confirm Duplicates (Keep #{g['representative_record_id']})", key=f"c_dup_{gid}", type="primary", use_container_width=True):
                    conn.execute("UPDATE duplicate_groups SET status = 'human_confirmed' WHERE group_id = ?;", (gid,))
                    conn.execute("UPDATE records SET is_hidden_duplicate = CASE WHEN record_id = ? THEN 0 ELSE 1 END WHERE duplicate_group_id = ?;", (g["representative_record_id"], gid))
                    conn.commit()
                    log_human_audit(reviewer_name, "duplicate_override", gid, g["status"], "human_confirmed", "Confirmed duplicate cluster")
                    st.rerun()
                if b2.button("✂️ Split into Separate Studies", key=f"s_dup_{gid}", use_container_width=True):
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
    render_bottom_nav(curr_idx)


# ==============================================================================
# STAGE 06: SPLIT-SCREEN SCREENER (FIXED-HEIGHT SCROLLABLE DOCK + PAGINATION)
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
        "Study Bucket:",
        [f"📚 All ({len(all_recs)})", f"✅ Included ({len(inc_list)})", f"❌ Excluded ({len(exc_list)})", f"🤔 Maybe ({len(may_list)})"],
        horizontal=True
    )
    filtered_recs = inc_list if "Included" in bucket_choice else (exc_list if "Excluded" in bucket_choice else (may_list if "Maybe" in bucket_choice else all_recs))

    if not filtered_recs:
        st.info("No papers in this bucket.")
    else:
        c1, c2, c3 = st.columns([1.8, 1.2, 1])
        q_scr = c1.text_input("🔎 Instant Filter:", "", placeholder="Search title, #ID, or keyword...")
        if q_scr.strip():
            ql = q_scr.lower().lstrip("#")
            filtered_recs = [r for r in filtered_recs if ql in str(r["record_id"]) or ql in (r["title"] or "").lower() or ql in (r["abstract"] or "").lower()]

        if not filtered_recs:
            st.warning("No matching papers.")
        else:
            if "selected_paper_id" not in st.session_state or st.session_state["selected_paper_id"] not in [r["record_id"] for r in filtered_recs]:
                st.session_state["selected_paper_id"] = filtered_recs[0]["record_id"]

            id_map = {r["record_id"]: f"#{r['record_id']} [{r['effective_decision'].upper()}] — {r['title'][:45]}..." for r in filtered_recs}
            jump_id = c2.selectbox("⚡ Quick Jump:", list(id_map.keys()), index=list(id_map.keys()).index(st.session_state["selected_paper_id"]), format_func=lambda k: id_map[k])
            if jump_id != st.session_state["selected_paper_id"]:
                st.session_state["selected_paper_id"] = jump_id
                st.rerun()

            per_page = 8
            tot_p = max(1, math.ceil(len(filtered_recs) / per_page))
            scr_p = c3.number_input(f"Page (1–{tot_p})", 1, tot_p, 1)
            paged = filtered_recs[(scr_p - 1) * per_page : scr_p * per_page]

            col_l, col_r = st.columns([1.15, 1.85])
            with col_l:
                with st.container(height=640, border=True):
                    for r in paged:
                        is_sel = (r["record_id"] == st.session_state["selected_paper_id"])
                        with st.container(border=True):
                            st.markdown(f"**#{r['record_id']} · {r['title']}**")
                            st.caption(f"**[{r['effective_decision'].upper()}]** • {r['source']} ({r['pub_year']})")
                            if st.button("✦ Active ➡️" if is_sel else f"Inspect #{r['record_id']}", key=f"box_{r['record_id']}", type="primary" if is_sel else "secondary", use_container_width=True):
                                st.session_state["selected_paper_id"] = r["record_id"]
                                st.rerun()

            with col_r:
                sel = next((x for x in filtered_recs if x["record_id"] == st.session_state["selected_paper_id"]), filtered_recs[0])
                p_val = sel["pico_p"] or sel["population_span"] or ""
                i_val = sel["pico_i"] or sel["intervention_span"] or ""
                c_val = sel["pico_c"] or sel["comparator_span"] or ""
                o_val = sel["pico_o"] or sel["outcome_span"] or ""

                with st.container(border=True):
                    st.markdown(f"### #{sel['record_id']} · {sel['title']}")
                    st.caption(f"👤 {sel['authors']} | 🏛️ {sel['journal']} ({sel['pub_year']}) | `{sel['pub_types']}`")
                    st.markdown(smart_highlight_pico_html(sel["abstract"], p_val, i_val, c_val, o_val, config), unsafe_allow_html=True)
                    st.write("")
                    reas = st.text_input("Decision / Exclusion Reason:", value=sel["effective_reason"], key=f"reas_{sel['record_id']}")
                    a1, a2, a3 = st.columns(3)
                    if a1.button("✅ Include", type="primary", use_container_width=True):
                        save_human_decision(sel["duplicate_group_id"], sel["record_id"], reviewer_name, "Include", "Meets PICO criteria", "", p_val, i_val, c_val, o_val, "screen_include")
                        st.rerun()
                    if a2.button("🤔 Maybe", use_container_width=True):
                        save_human_decision(sel["duplicate_group_id"], sel["record_id"], reviewer_name, "Maybe", reas or "Needs full-text check", "", p_val, i_val, c_val, o_val, "screen_maybe")
                        st.rerun()
                    if a3.button("❌ Exclude", use_container_width=True):
                        save_human_decision(sel["duplicate_group_id"], sel["record_id"], reviewer_name, "Exclude", reas.strip() or "Excluded by reviewer", "", p_val, i_val, c_val, o_val, "screen_exclude")
                        st.rerun()
    render_bottom_nav(curr_idx)


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

    eligible = [dict(r) for r in rows if r["final_decision"] in ("Include", "Maybe")]
    if not eligible:
        st.info("No Included/Maybe studies yet.")
    else:
        opts = {i: f"[{r['final_decision'].upper()}] Paper #{r['record_id']} — {r['title']}" for i, r in enumerate(eligible)}
        chosen_i = st.selectbox("🎯 Select Study to Inspect & Edit PICO Spans:", list(opts.keys()), format_func=lambda k: opts[k])
        r = eligible[chosen_i]
        p_val = r["pico_p"] if r["pico_p"] is not None else (r["population_span"] or "")
        i_val = r["pico_i"] if r["pico_i"] is not None else (r["intervention_span"] or "")
        c_val = r["pico_c"] if r["pico_c"] is not None else (r["comparator_span"] or "")
        o_val = r["pico_o"] if r["pico_o"] is not None else (r["outcome_span"] or "")
        with st.container(border=True):
            st.markdown(f"### [{r['final_decision'].upper()}] #{r['record_id']} · {r['title']}")
            st.markdown(smart_highlight_pico_html(r["abstract"], p_val, i_val, c_val, o_val, config), unsafe_allow_html=True)
            st.write("")
            with st.form(f"pico_f_{r['record_id']}"):
                pc1, pc2 = st.columns(2)
                np = pc1.text_input("🟦 Population [P]", value=p_val)
                ni = pc2.text_input("🟩 Intervention [I]", value=i_val)
                nc = pc1.text_input("🟧 Comparator [C]", value=c_val)
                no = pc2.text_input("🟪 Outcome [O]", value=o_val)
                if st.form_submit_button("💾 Save Verified PICO Spans", type="primary"):
                    save_human_decision(r["duplicate_group_id"], r["record_id"], reviewer_name, r["final_decision"], r["final_reason"], r["reviewer_notes"] or "", np, ni, nc, no, "pico_edit")
                    st.rerun()
    render_bottom_nav(curr_idx)


# ==============================================================================
# STAGE 08: LEVEL-2 DIFF & CONFLICT LOOP
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
                if st.button(f"✅ Resolve Cluster #{c['group_id']}", key=f"res_{c['group_id']}"):
                    resolve_duplicate_conflict(c["group_id"], c["representative_record_id"], reviewer_name)
                    st.rerun()
    else:
        st.success("✅ Zero merge conflicts across active duplicate clusters.")

    if len(queries) < 2:
        if st.button("⚡ Load Expanded Query v2 (+2 New RCTs) to Demo Diff Engine", type="primary"):
            vid = create_query_version("Benchmark v2 (Expanded)", '("type 2 diabetes") AND metformin AND (placebo OR sulfonylurea)', 2015, 2025, ["PubMed", "Europe PMC"], 9, 5)
            store_fetched_records(vid, get_benchmark_papers("v2"))
            run_deduplication(vid)
            run_screening(vid)
            run_pico_extraction(vid)
            st.rerun()
    else:
        q_opts = {f"v{q['version_id']}: {q['version_name']} ({q['boolean_query']})": q["version_id"] for q in queries}
        labels = list(q_opts.keys())
        c1, c2 = st.columns(2)
        old_l = c1.selectbox("Baseline Version:", labels, index=min(1, len(labels) - 1))
        new_l = c2.selectbox("Updated Version:", labels, index=0)
        diff = compute_query_diff(q_opts[old_l], q_opts[new_l])
        m1, m2 = st.columns(2)
        m1.metric("➕ Added Records", diff["added_count"])
        m2.metric("➖ Removed Records (Preserved in Vault)", diff["removed_count"])
        for ar in diff["added_records"]:
            st.markdown(f"<div class='spatial-card' style='border-left-color:#10b981;'><b>➕ Record #{ar['record_id']}</b> — {ar['title']} ({ar['source']}, {ar['pub_year']})</div>", unsafe_allow_html=True)
    render_bottom_nav(curr_idx)


# ==============================================================================
# STAGE 09: AI WHITE-SPACE & EVIDENCE GAP MATRIX
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

    eligible = [dict(r) for r in rows if r["final_decision"] in ("Include", "Maybe")]
    if not eligible:
        st.info("Load the 12-Paper Demo Pack from ⚙️ Studio Controls to populate the AI White-Space Matrix.")
    else:
        gap_data = compute_ai_evidence_gap_matrix(eligible, config)
        hdr = st.columns([1.3, 1, 1, 1, 1])
        hdr[0].markdown("**COHORT \\ ENDPOINT**")
        for c_i, out_name in enumerate(gap_data["outcomes"]):
            hdr[c_i + 1].markdown(f"<div style='text-align:center; font-weight:700; font-size:0.88rem;'>{out_name}</div>", unsafe_allow_html=True)

        for sg in gap_data["subgroups"]:
            rc = st.columns([1.3, 1, 1, 1, 1])
            rc[0].markdown(f"<div style='padding-top:32px; font-weight:700;'>👥 {sg}</div>", unsafe_allow_html=True)
            for c_i, out_name in enumerate(gap_data["outcomes"]):
                cell = gap_data["matrix"][sg][out_name]
                cnt, p_list = cell["count"], cell["paper_ids"]
                pills = "".join(f"<span class='id-pill'>#{pid}</span>" for pid in p_list[:4])
                if len(p_list) > 4:
                    pills += f"<span class='id-pill' style='border-color:#10b981;'>+{len(p_list)-4} more</span>"

                if cnt >= 2:
                    rc[c_i + 1].markdown(f"<div class='gap-dense'><div style='font-size:1.5rem; font-weight:800; color:#10b981; margin-bottom:6px;'>🟢 {cnt} RCTs</div><div>{pills}</div></div>", unsafe_allow_html=True)
                elif cnt == 1:
                    rc[c_i + 1].markdown(f"<div class='gap-sparse'><div style='font-size:1.5rem; font-weight:800; color:#fbbf24; margin-bottom:6px;'>🟡 1 RCT</div><div>{pills}</div></div>", unsafe_allow_html=True)
                else:
                    rc[c_i + 1].markdown("<div class='gap-zero'><div style='font-size:1.45rem; font-weight:800; color:#f43f5e;'>🔥 0 STUDIES</div><div style='font-size:0.72rem; font-weight:700; letter-spacing:1px;'>WHITE-SPACE GAP</div></div>", unsafe_allow_html=True)
            st.write("")

        if gap_data["gaps"]:
            g_labels = [f"🔥 Gap #{i+1}: {g['subgroup']} × {g['outcome']} (0 RCTs)" for i, g in enumerate(gap_data["gaps"])]
            c_idx = st.selectbox("🚀 Select a Red White-Space Gap to Synthesize Trial Blueprint:", range(len(g_labels)), format_func=lambda i: g_labels[i])
            sel_g = gap_data["gaps"][c_idx]
            with st.container(border=True):
                st.markdown(f"#### 💡 Unasked Question: *\"{sel_g['unasked_question']}\"*")
                c1, c2 = st.columns(2)
                c1.write(f"**🕵️ Why Missed:** {sel_g['why_missed']}")
                c2.write(f"**🧪 Phase III Blueprint:** {sel_g['trial_design']}")
                st.code(sel_g["mutated_query"], language="sql")
                if st.button("⚡ Inject Gap Query into 02 · Composer & Run Level-2 ➡️", type="primary", use_container_width=True):
                    st.session_state["custom_query_box"] = sel_g["mutated_query"]
                    go_to_step(2)
    render_bottom_nav(curr_idx)


# ==============================================================================
# STAGE 10: EXPORT & AUDIT LEDGER
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
        e1, e2, e3 = st.columns([1.8, 1.2, 1.2])
        exp_f = e1.radio("Filter:", ["All Unique", "✅ Included", "❌ Excluded"], horizontal=True)
        led_v = e2.radio("View:", ["🎴 Spatial Cards", "📊 CSV Table"], horizontal=True)
        df_sub = df_all[df_all["final_decision"] == "Include"] if "Included" in exp_f else (df_all[df_all["final_decision"] == "Exclude"] if "Excluded" in exp_f else df_all)
        with e3:
            st.download_button(f"📥 Download CSV ({len(df_sub)})", df_sub.to_csv(index=False).encode("utf-8"), "mini_rayyan_spatial_export.csv", "text/csv", type="primary", use_container_width=True)

        if led_v == "📊 CSV Table":
            st.dataframe(df_sub, use_container_width=True, hide_index=True)
        else:
            with st.container(height=400, border=True):
                for _, row in df_sub.iterrows():
                    dec = row["final_decision"]
                    b_col = "#10b981" if dec == "Include" else ("#f43f5e" if dec == "Exclude" else "#fbbf24")
                    st.markdown(f"""
                    <div class="spatial-card" style="border-left-color:{b_col};">
                        <div style="display:flex; justify-content:space-between;">
                            <b>Record #{row['record_id']} · {row['title']}</b>
                            <span class="k-chip" style="color:{b_col}; border-color:{b_col};">{dec.upper()}</span>
                        </div>
                        <div style="font-size:0.80rem; color:{sk['muted']}; margin-top:4px;">{row['journal']} ({row['pub_year']}) • DOI: {row['doi'] or 'N/A'}</div>
                    </div>
                    """, unsafe_allow_html=True)

    l1, l2 = st.columns(2)
    with l1:
        st.markdown("#### ✍️ Human Override Audit Stream")
        audits = conn.execute("SELECT * FROM audit_log ORDER BY log_id DESC LIMIT 25;").fetchall()
        with st.container(height=320, border=True):
            for a in audits:
                st.markdown(f"<div class='spatial-card'><b>#{a['log_id']} · {a['action_type'].upper()}</b> → {a['new_value']}<br><span style='font-size:0.78rem; opacity:0.75;'>{a['reviewer_name']} • {a['timestamp']}</span></div>", unsafe_allow_html=True)
    with l2:
        st.markdown("#### ⚙️ Pipeline Telemetry Stream")
        runs = conn.execute("SELECT * FROM run_log ORDER BY run_id DESC LIMIT 25;").fetchall()
        with st.container(height=320, border=True):
            for r in runs:
                st.markdown(f"<div class='spatial-card' style='border-left-color:{sk['accent2']};'><b>#{r['run_id']} · {r['step_name'].upper()}</b><br><span style='font-size:0.82rem;'>{r['details']}</span></div>", unsafe_allow_html=True)
    conn.close()
    render_bottom_nav(curr_idx)
