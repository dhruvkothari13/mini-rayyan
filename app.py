import difflib
import json
import re
from typing import Dict, List, Tuple

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# PAGE CONFIG & SESSION STATE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Mini Rayyan AI — Spatial Literature Screening",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def init_state():
    defaults = {
        "theme": "dark",
        "step": 1,
        "papers": [],
        "duplicates_removed": 0,
        "decisions": {},  # {paper_id: "Include" | "Exclude" | "Maybe"}
        "query": "atrial fibrillation AND anticoagulants",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# -----------------------------------------------------------------------------
# THEME TOKENS & GLOBAL AESTHETIC CSS
# -----------------------------------------------------------------------------
def get_palette(theme: str) -> Dict[str, str]:
    if theme == "dark":
        return {
            "bg": "#07090E",
            "bg_radial": "radial-gradient(circle at 18% 12%, rgba(56, 189, 248, 0.10), transparent 42%), radial-gradient(circle at 82% 8%, rgba(16, 185, 129, 0.08), transparent 40%)",
            "surface": "rgba(17, 22, 34, 0.65)",
            "surface_hover": "rgba(24, 31, 48, 0.85)",
            "border": "rgba(255, 255, 255, 0.09)",
            "border_strong": "rgba(56, 189, 248, 0.35)",
            "text": "#F1F5F9",
            "muted": "#94A3B8",
            "accent": "#38BDF8",
            "accent_2": "#10B981",
            "canvas_node": "56, 189, 248",
            "canvas_link": "148, 163, 184",
        }
    return {
        "bg": "#F8FAFC",
        "bg_radial": "radial-gradient(circle at 18% 12%, rgba(14, 165, 233, 0.10), transparent 42%), radial-gradient(circle at 82% 8%, rgba(16, 185, 129, 0.08), transparent 40%)",
        "surface": "rgba(255, 255, 255, 0.78)",
        "surface_hover": "rgba(255, 255, 255, 0.96)",
        "border": "rgba(15, 23, 42, 0.09)",
        "border_strong": "rgba(2, 132, 199, 0.35)",
        "text": "#0F172A",
        "muted": "#475569",
        "accent": "#0284C7",
        "accent_2": "#059669",
        "canvas_node": "2, 132, 199",
        "canvas_link": "71, 85, 105",
    }

P = get_palette(st.session_state.theme)

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: __BG__;
    --surface: __SURFACE__;
    --surface-hover: __SURFACE_HOVER__;
    --border: __BORDER__;
    --border-strong: __BORDER_STRONG__;
    --text: __TEXT__;
    --muted: __MUTED__;
    --accent: __ACCENT__;
    --accent-2: __ACCENT_2__;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    background-image: __BG_RADIAL__ !important;
    color: var(--text) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    scroll-behavior: smooth;
}

[data-testid="stHeader"], [data-testid="stToolbar"] {
    background: transparent !important;
}

/* Hide default Streamlit chrome for a cleaner web-app feel */
#MainMenu, footer { visibility: hidden; }

/* Tactile Glassmorphic Cards */
.glass-card {
    background: var(--surface);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
    transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1),
                border-color 0.25s ease,
                box-shadow 0.28s ease;
    animation: fadeSlideUp 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.glass-card:hover {
    transform: translateY(-3px);
    border-color: var(--border-strong);
    box-shadow: 0 18px 40px -18px rgba(0, 0, 0, 0.35);
}

@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* Stepper Pipeline */
.stepper-wrap {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
    margin: 0.5rem 0 1.5rem 0;
}

.step-pill {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.7rem 1rem;
    border-radius: 12px;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--muted);
    font-size: 0.85rem;
    font-weight: 500;
    transition: all 0.25s ease;
}

.step-pill.active {
    border-color: var(--accent);
    color: var(--text);
    box-shadow: 0 0 24px -8px var(--accent);
}

.step-pill.done {
    border-color: var(--accent-2);
    color: var(--text);
}

.step-num {
    width: 22px;
    height: 22px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    background: var(--border);
    color: var(--text);
}

.step-pill.active .step-num { background: var(--accent); color: #07090E; font-weight: 700; }
.step-pill.done .step-num   { background: var(--accent-2); color: #07090E; font-weight: 700; }

/* PICO Badges */
.pico-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    margin-right: 6px;
    font-family: 'JetBrains Mono', monospace;
}
.pico-p { background: rgba(56, 189, 248, 0.16); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.35); }
.pico-i { background: rgba(16, 185, 129, 0.16); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.35); }
.pico-c { background: rgba(245, 158, 11, 0.16); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.35); }
.pico-o { background: rgba(168, 85, 247, 0.16); color: #A855F7; border: 1px solid rgba(168, 85, 247, 0.35); }

/* Tactile Buttons */
.stButton > button {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    padding: 0.45rem 1rem !important;
    transition: transform 0.16s ease, border-color 0.2s ease, box-shadow 0.2s ease !important;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 20px -10px var(--accent) !important;
}
.stButton > button:active {
    transform: scale(0.97) !important;
}

/* Inputs */
.stTextInput input, .stSelectbox div[data-baseweb="select"] {
    background: var(--surface) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
}

/* Metric styling */
[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.9rem 1.1rem;
}
</style>
"""

for token, val in {
    "__BG__": P["bg"],
    "__BG_RADIAL__": P["bg_radial"],
    "__SURFACE__": P["surface"],
    "__SURFACE_HOVER__": P["surface_hover"],
    "__BORDER__": P["border"],
    "__BORDER_STRONG__": P["border_strong"],
    "__TEXT__": P["text"],
    "__MUTED__": P["muted"],
    "__ACCENT__": P["accent"],
    "__ACCENT_2__": P["accent_2"],
}.items():
    GLOBAL_CSS = GLOBAL_CSS.replace(token, val)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# BACKEND LOGIC: EUROPE PMC, DEDUPLICATION, PICO EXTRACTION
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=600)
def fetch_europe_pmc(query: str, limit: int = 18) -> List[Dict]:
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": query,
        "format": "json",
        "resultType": "core",
        "pageSize": limit,
    }
    resp = requests.get(url, params=params, timeout=12)
    resp.raise_for_status()
    results = resp.json().get("resultList", {}).get("result", [])
    papers = []
    for idx, item in enumerate(results):
        papers.append({
            "id": item.get("pmid") or item.get("id") or f"paper_{idx}",
            "title": (item.get("title") or "Untitled Study").strip(),
            "authors": item.get("authorString") or "Unknown Authors",
            "journal": item.get("journalTitle") or "Preprint / Journal",
            "year": str(item.get("pubYear") or "N/A"),
            "doi": item.get("doi") or "",
            "abstract": (item.get("abstractText") or "No abstract available.").strip(),
        })
    return papers


def deduplicate_papers(papers: List[Dict], threshold: float = 0.88) -> Tuple[List[Dict], int]:
    unique, seen_dois, seen_titles = [], set(), []
    removed = 0
    for p in papers:
        doi = p["doi"].lower().strip()
        norm_title = re.sub(r"[^a-z0-9\s]", "", p["title"].lower()).strip()
        if doi and doi in seen_dois:
            removed += 1
            continue
        is_dup = any(
            difflib.SequenceMatcher(None, norm_title, t).ratio() >= threshold
            for t in seen_titles
        )
        if is_dup:
            removed += 1
            continue
        if doi:
            seen_dois.add(doi)
        seen_titles.append(norm_title)
        unique.append(p)
    return unique, removed


PICO_PATTERNS = {
    "P": r"\b(patients?|adults?|elderly|children|cohort|participants?|subjects?|population|individuals?)\b",
    "I": r"\b(therapy|treatment|drug|anticoagulants?|warfarin|apixaban|rivaroxaban|intervention|surgery|dose|administered)\b",
    "C": r"\b(placebo|control|versus|vs\.?|compared with|standard care|usual care|comparator)\b",
    "O": r"\b(mortality|stroke|bleeding|survival|efficacy|safety|outcome|risk|reduction|incidence|rate)\b",
}

def extract_pico(text: str) -> Dict[str, List[str]]:
    found = {}
    for key, pattern in PICO_PATTERNS.items():
        matches = sorted(set(m.group(0).lower() for m in re.finditer(pattern, text, re.I)))
        found[key] = matches[:4]
    return found


def highlight_pico_html(text: str) -> str:
    colors = {
        "P": "rgba(56,189,248,0.22)",
        "I": "rgba(16,185,129,0.22)",
        "C": "rgba(245,158,11,0.22)",
        "O": "rgba(168,85,247,0.22)",
    }
    highlighted = text
    for key, pattern in PICO_PATTERNS.items():
        highlighted = re.sub(
            pattern,
            lambda m, c=colors[key]: f'<mark style="background:{c};color:inherit;padding:1px 4px;border-radius:4px;">{m.group(0)}</mark>',
            highlighted,
            flags=re.IGNORECASE,
        )
    return highlighted


# -----------------------------------------------------------------------------
# COMPONENT 1: REVOLVING 3D INTERACTIVE KNOWLEDGE SPHERE (HERO)
# -----------------------------------------------------------------------------
def render_3d_hero(palette: Dict[str, str], paper_count: int):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
      * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', system-ui, sans-serif; }
      body { background: transparent; overflow: hidden; color: __TEXT__; }
      .hero {
        position: relative;
        width: 100%;
        height: 250px;
        border-radius: 20px;
        border: 1px solid __BORDER__;
        background: __SURFACE__;
        backdrop-filter: blur(20px);
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 2.2rem;
        cursor: grab;
      }
      .hero:active { cursor: grabbing; }
      .hero-copy {
        position: relative;
        z-index: 2;
        max-width: 58%;
        pointer-events: none;
      }
      .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 11px;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: __ACCENT__;
        margin-bottom: 10px;
        font-weight: 600;
      }
      .pulse {
        width: 7px; height: 7px; border-radius: 50%;
        background: __ACCENT_2__;
        box-shadow: 0 0 10px __ACCENT_2__;
      }
      h1 {
        font-size: 2rem;
        font-weight: 600;
        letter-spacing: -0.03em;
        line-height: 1.15;
        margin-bottom: 10px;
      }
      p {
        font-size: 0.92rem;
        color: __MUTED__;
        line-height: 1.5;
      }
      .hint {
        margin-top: 14px;
        font-size: 11px;
        color: __MUTED__;
        opacity: 0.8;
        font-family: monospace;
      }
      canvas {
        position: absolute;
        right: 0;
        top: 0;
        width: 100%;
        height: 100%;
        z-index: 1;
      }
    </style>
    </head>
    <body>
      <div class="hero" id="hero">
        <div class="hero-copy">
          <div class="eyebrow"><span class="pulse"></span> Systematic Review Engine • __COUNT__ Active Nodes</div>
          <h1>Mini Rayyan AI</h1>
          <p>Spatial literature screening, automated deduplication, and real-time PICO extraction powered by Europe PMC.</p>
          <div class="hint">DRAG OR HOVER SURFACE TO ROTATE 3D CITATION LATTICE</div>
        </div>
        <canvas id="sphere"></canvas>
      </div>

      <script>
        const canvas = document.getElementById('sphere');
        const ctx = canvas.getContext('2d');
        const hero = document.getElementById('hero');

        let W, H, cx, cy;
        function resize() {
          const dpr = window.devicePixelRatio || 1;
          W = hero.clientWidth;
          H = hero.clientHeight;
          canvas.width = W * dpr;
          canvas.height = H * dpr;
          ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
          cx = W * 0.78;
          cy = H * 0.50;
        }
        resize();
        window.addEventListener('resize', resize);

        // Fibonacci Sphere Points
        const N = 64;
        const R = 88;
        const pts = [];
        const golden = Math.PI * (3 - Math.sqrt(5));
        for (let i = 0; i < N; i++) {
          const y = 1 - (i / (N - 1)) * 2;
          const r = Math.sqrt(1 - y * y);
          const theta = golden * i;
          pts.push({ x: Math.cos(theta) * r * R, y: y * R, z: Math.sin(theta) * r * R });
        }

        let rotX = 0.25, rotY = 0.0;
        let velX = 0.002, velY = 0.0045;
        let dragging = false, lastX = 0, lastY = 0;

        hero.addEventListener('pointerdown', (e) => {
          dragging = true; lastX = e.clientX; lastY = e.clientY;
        });
        window.addEventListener('pointerup', () => dragging = false);
        window.addEventListener('pointermove', (e) => {
          if (dragging) {
            const dx = e.clientX - lastX;
            const dy = e.clientY - lastY;
            velY = dx * 0.003;
            velX = dy * 0.003;
            lastX = e.clientX; lastY = e.clientY;
          } else {
            const rect = hero.getBoundingClientRect();
            const nx = (e.clientX - rect.left) / rect.width - 0.5;
            const ny = (e.clientY - rect.top) / rect.height - 0.5;
            velY = 0.0035 + nx * 0.008;
            velX = 0.001 + ny * 0.006;
          }
        });

        function project(p) {
          // Rotate X
          let y1 = p.y * Math.cos(rotX) - p.z * Math.sin(rotX);
          let z1 = p.y * Math.sin(rotX) + p.z * Math.cos(rotX);
          // Rotate Y
          let x2 = p.x * Math.cos(rotY) + z1 * Math.sin(rotY);
          let z2 = -p.x * Math.sin(rotY) + z1 * Math.cos(rotY);

          const fov = 320;
          const scale = fov / (fov + z2 + 110);
          return { x: cx + x2 * scale, y: cy + y1 * scale, z: z2, s: scale };
        }

        function animate() {
          ctx.clearRect(0, 0, W, H);
          rotX += velX;
          rotY += velY;
          if (!dragging) {
            velX *= 0.985;
            velY = velY * 0.985 + 0.004 * 0.015;
          }

          const proj = pts.map(project);

          // Draw subtle orbital ring
          ctx.beginPath();
          ctx.ellipse(cx, cy, R * 1.18, R * 0.36, rotY * 0.25, 0, Math.PI * 2);
          ctx.strokeStyle = 'rgba(__NODE_RGB__, 0.18)';
          ctx.lineWidth = 1;
          ctx.stroke();

          // Connect nearby nodes
          for (let i = 0; i < N; i++) {
            for (let j = i + 1; j < N; j++) {
              const dx = pts[i].x - pts[j].x;
              const dy = pts[i].y - pts[j].y;
              const dz = pts[i].z - pts[j].z;
              const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
              if (dist < 46) {
                const alpha = Math.max(0.04, ((proj[i].s + proj[j].s) * 0.5 - 0.55) * 0.45);
                ctx.beginPath();
                ctx.moveTo(proj[i].x, proj[i].y);
                ctx.lineTo(proj[j].x, proj[j].y);
                ctx.strokeStyle = `rgba(__LINK_RGB__, ${alpha.toFixed(3)})`;
                ctx.lineWidth = 0.8;
                ctx.stroke();
              }
            }
          }

          // Draw nodes back-to-front
          proj.sort((a, b) => a.z - b.z);
          for (const p of proj) {
            const alpha = Math.min(1, Math.max(0.18, (p.s - 0.45) * 1.4));
            ctx.beginPath();
            ctx.arc(p.x, p.y, Math.max(1.4, p.s * 3.0), 0, Math.PI * 2);
            ctx.fillStyle = `rgba(__NODE_RGB__, ${alpha.toFixed(3)})`;
            ctx.fill();
          }

          requestAnimationFrame(animate);
        }
        animate();
      </script>
    </body>
    </html>
    """
    replacements = {
        "__TEXT__": palette["text"],
        "__MUTED__": palette["muted"],
        "__BORDER__": palette["border"],
        "__SURFACE__": palette["surface"],
        "__ACCENT__": palette["accent"],
        "__ACCENT_2__": palette["accent_2"],
        "__NODE_RGB__": palette["canvas_node"],
        "__LINK_RGB__": palette["canvas_link"],
        "__COUNT__": str(paper_count),
    }
    for k, v in replacements.items():
        html = html.replace(k, v)
    components.html(html, height=265)


# -----------------------------------------------------------------------------
# COMPONENT 2: SPATIAL BROWSER WITH 3D TILT, CURSOR SPOTLIGHT & SCROLL-TO-LOAD
# -----------------------------------------------------------------------------
def render_spatial_browser(papers: List[Dict], decisions: Dict[str, str], palette: Dict[str, str]):
    payload = []
    for p in papers:
        pico = extract_pico(p["abstract"])
        payload.append({
            "id": p["id"],
            "title": p["title"],
            "authors": p["authors"][:90] + ("…" if len(p["authors"]) > 90 else ""),
            "journal": p["journal"],
            "year": p["year"],
            "abstract": p["abstract"][:260] + ("…" if len(p["abstract"]) > 260 else ""),
            "decision": decisions.get(p["id"], "Unscreened"),
            "pico": pico,
        })

    safe_json = json.dumps(payload).replace("</", "<\\/")

    html = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
      * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', system-ui, sans-serif; }
      body { background: transparent; color: __TEXT__; padding: 6px 4px; overflow-x: hidden; }

      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
        gap: 18px;
        perspective: 1200px;
      }

      .spatial-card {
        position: relative;
        background: __SURFACE__;
        border: 1px solid __BORDER__;
        border-radius: 16px;
        padding: 18px 20px;
        overflow: hidden;
        transform-style: preserve-3d;
        transition: transform 0.18s cubic-bezier(0.22, 1, 0.36, 1),
                    opacity 0.6s cubic-bezier(0.22, 1, 0.36, 1),
                    filter 0.6s ease,
                    border-color 0.25s ease;
        opacity: 0;
        transform: translateY(28px) scale(0.97);
        filter: blur(4px);
        cursor: pointer;
      }

      .spatial-card.visible {
        opacity: 1;
        transform: translateY(0) scale(1);
        filter: blur(0);
      }

      /* Touchable Cursor Spotlight */
      .spatial-card::before {
        content: "";
        position: absolute;
        inset: 0;
        background: radial-gradient(320px circle at var(--mx, 50%) var(--my, 50%), rgba(__NODE_RGB__, 0.18), transparent 60%);
        opacity: 0;
        transition: opacity 0.25s ease;
        pointer-events: none;
      }

      .spatial-card:hover::before { opacity: 1; }
      .spatial-card:hover { border-color: __BORDER_STRONG__; }

      .meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 11px;
        color: __MUTED__;
        margin-bottom: 10px;
        font-family: monospace;
      }

      .status-pill {
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        border: 1px solid __BORDER__;
      }
      .status-Include { color: #10B981; border-color: rgba(16,185,129,0.4); background: rgba(16,185,129,0.12); }
      .status-Exclude { color: #F43F5E; border-color: rgba(244,63,94,0.4); background: rgba(244,63,94,0.12); }
      .status-Maybe   { color: #F59E0B; border-color: rgba(245,158,11,0.4); background: rgba(245,158,11,0.12); }

      h3 {
        font-size: 0.96rem;
        line-height: 1.38;
        font-weight: 600;
        margin-bottom: 8px;
        transform: translateZ(18px);
      }

      .authors {
        font-size: 0.78rem;
        color: __MUTED__;
        margin-bottom: 10px;
      }

      .abstract {
        font-size: 0.82rem;
        line-height: 1.5;
        color: __MUTED__;
        margin-bottom: 12px;
      }

      .pico-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        transform: translateZ(12px);
      }

      .tag {
        font-size: 10px;
        padding: 2px 7px;
        border-radius: 6px;
        font-family: monospace;
        background: rgba(__NODE_RGB__, 0.12);
        color: __ACCENT__;
        border: 1px solid rgba(__NODE_RGB__, 0.25);
      }

      .spatial-card.expanded {
        grid-column: 1 / -1;
        border-color: __ACCENT__;
        box-shadow: 0 20px 50px -20px rgba(0, 0, 0, 0.5);
      }
    </style>
    </head>
    <body>
      <div class="grid" id="grid"></div>

      <script>
        const papers = __DATA__;
        const grid = document.getElementById('grid');

        papers.forEach((p, idx) => {
          const card = document.createElement('div');
          card.className = 'spatial-card';
          card.style.transitionDelay = `${(idx % 6) * 55}ms`;

          const picoTags = Object.entries(p.pico)
            .filter(([_, vals]) => vals.length > 0)
            .map(([k, vals]) => `<span class="tag">${k}: ${vals[0]}</span>`)
            .join('');

          card.innerHTML = `
            <div class="meta">
              <span>${p.journal} • ${p.year}</span>
              <span class="status-pill status-${p.decision}">${p.decision}</span>
            </div>
            <h3>${p.title}</h3>
            <div class="authors">${p.authors}</div>
            <div class="abstract">${p.abstract}</div>
            <div class="pico-row">${picoTags || '<span class="tag">PICO: Pending</span>'}</div>
          `;

          // 3D Tilt + Cursor Spotlight
          card.addEventListener('pointermove', (e) => {
            if (card.classList.contains('expanded')) return;
            const r = card.getBoundingClientRect();
            const x = e.clientX - r.left;
            const y = e.clientY - r.top;
            card.style.setProperty('--mx', `${x}px`);
            card.style.setProperty('--my', `${y}px`);
            const rx = ((y / r.height) - 0.5) * -9;
            const ry = ((x / r.width) - 0.5) * 9;
            card.style.transform = `perspective(900px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-4px)`;
          });

          card.addEventListener('pointerleave', () => {
            card.style.transform = 'perspective(900px) rotateX(0deg) rotateY(0deg) translateY(0)';
          });

          // Click to spatially focus/expand
          card.addEventListener('click', () => {
            card.classList.toggle('expanded');
            card.style.transform = 'none';
          });

          grid.appendChild(card);
        });

        // Scroll-to-Load Staggered Reveal
        const observer = new IntersectionObserver((entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add('visible');
              observer.unobserve(entry.target);
            }
          });
        }, { threshold: 0.12 });

        document.querySelectorAll('.spatial-card').forEach((el) => observer.observe(el));
      </script>
    </body>
    </html>
    """
    replacements = {
        "__TEXT__": palette["text"],
        "__MUTED__": palette["muted"],
        "__SURFACE__": palette["surface"],
        "__BORDER__": palette["border"],
        "__BORDER_STRONG__": palette["border_strong"],
        "__ACCENT__": palette["accent"],
        "__NODE_RGB__": palette["canvas_node"],
        "__DATA__": safe_json,
    }
    for k, v in replacements.items():
        html = html.replace(k, v)

    components.html(html, height=620, scrolling=True)


# -----------------------------------------------------------------------------
# TOP BAR & THEME TOGGLE
# -----------------------------------------------------------------------------
top_left, top_right = st.columns([5, 1])
with top_left:
    st.caption("MINI RAYYAN AI  •  SYSTEMATIC LITERATURE WORKBENCH")
with top_right:
    toggle_label = "☀ Light Mode" if st.session_state.theme == "dark" else "☾ Dark Mode"
    if st.button(toggle_label, use_container_width=True):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

# 3D Revolving Hero
render_3d_hero(P, len(st.session_state.papers))

# Step-by-Step Progress Bar
steps = [
    (1, "Query Europe PMC"),
    (2, "Deduplicate"),
    (3, "Spatial & PICO Screen"),
    (4, "Export Dataset"),
]
stepper_html = '<div class="stepper-wrap">'
for num, label in steps:
    cls = "active" if st.session_state.step == num else ("done" if st.session_state.step > num else "")
    stepper_html += f'<div class="step-pill {cls}"><span class="step-num">{num}</span><span>{label}</span></div>'
stepper_html += "</div>"
st.markdown(stepper_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SEARCH & DEDUPLICATION BAR
# -----------------------------------------------------------------------------
with st.container():
    c1, c2, c3 = st.columns([4, 1, 1])
    with c1:
        query = st.text_input(
            "Europe PMC Boolean Query",
            value=st.session_state.query,
            placeholder="e.g., atrial fibrillation AND (apixaban OR warfarin)",
            label_visibility="collapsed",
        )
    with c2:
        limit = st.selectbox("Max Results", [12, 20, 30, 50], index=0, label_visibility="collapsed")
    with c3:
        run_search = st.button("Fetch Papers →", use_container_width=True)

if run_search and query.strip():
    st.session_state.query = query.strip()
    with st.spinner("Querying Europe PMC and running duplicate detection..."):
        try:
            raw = fetch_europe_pmc(st.session_state.query, limit=limit)
            clean, dupes = deduplicate_papers(raw)
            st.session_state.papers = clean
            st.session_state.duplicates_removed = dupes
            st.session_state.step = 3
            st.rerun()
        except Exception as exc:
            st.error(f"Europe PMC request failed: {exc}")

# -----------------------------------------------------------------------------
# MAIN WORKSPACE
# -----------------------------------------------------------------------------
papers = st.session_state.papers
decisions = st.session_state.decisions

if not papers:
    st.markdown(
        """
        <div class="glass-card" style="text-align:center; padding: 2.5rem 1.5rem;">
            <h3 style="margin-bottom: 0.4rem;">Ready to Screen</h3>
            <p style="color: var(--muted); max-width: 520px; margin: 0 auto;">
                Enter a clinical or biomedical query above and click <b>Fetch Papers →</b> to populate the spatial browser, deduplicate records, and highlight PICO criteria.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    # Live Metrics Row
    inc = sum(1 for v in decisions.values() if v == "Include")
    exc = sum(1 for v in decisions.values() if v == "Exclude")
    may = sum(1 for v in decisions.values() if v == "Maybe")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Unique Papers", len(papers), f"-{st.session_state.duplicates_removed} dupes")
    m2.metric("Included", inc)
    m3.metric("Excluded", exc)
    m4.metric("Maybe", may)

    tab_spatial, tab_workbench, tab_export = st.tabs([
        "◈ Spatial Browser (3D Tilt & Scroll Reveal)",
        "✦ PICO Screening Workbench",
        "↓ Export Results",
    ])

    # TAB 1: SPATIAL BROWSER
    with tab_spatial:
        st.caption("Hover cards for 3D tilt & spotlight • Scroll to trigger reveal • Click any card to spatially expand")
        render_spatial_browser(papers, decisions, P)

    # TAB 2: INTERACTIVE PICO SCREENING WORKBENCH
    with tab_workbench:
        filter_status = st.radio(
            "Filter Queue",
            ["All", "Unscreened", "Include", "Exclude", "Maybe"],
            horizontal=True,
        )

        for p in papers:
            status = decisions.get(p["id"], "Unscreened")
            if filter_status != "All" and status != filter_status:
                continue

            pico = extract_pico(p["abstract"])
            badges = ""
            for key, cls in [("P", "pico-p"), ("I", "pico-i"), ("C", "pico-c"), ("O", "pico-o")]:
                if pico[key]:
                    badges += f'<span class="pico-badge {cls}">{key}: {", ".join(pico[key][:2])}</span>'

            highlighted_abs = highlight_pico_html(p["abstract"])

            st.markdown(
                f"""
                <div class="glass-card">
                    <div style="font-size:0.78rem; color:var(--muted); margin-bottom:6px; font-family:'JetBrains Mono', monospace;">
                        {p['journal']} • {p['year']} • Status: <b>{status}</b>
                    </div>
                    <div style="font-size:1.05rem; font-weight:600; margin-bottom:8px;">{p['title']}</div>
                    <div style="margin-bottom:10px;">{badges}</div>
                    <div style="font-size:0.88rem; line-height:1.6; color:var(--muted);">{highlighted_abs}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            b1, b2, b3, _ = st.columns([1, 1, 1, 4])
            if b1.button("✓ Include", key=f"inc_{p['id']}", use_container_width=True):
                st.session_state.decisions[p["id"]] = "Include"
                st.rerun()
            if b2.button("✕ Exclude", key=f"exc_{p['id']}", use_container_width=True):
                st.session_state.decisions[p["id"]] = "Exclude"
                st.rerun()
            if b3.button("? Maybe", key=f"may_{p['id']}", use_container_width=True):
                st.session_state.decisions[p["id"]] = "Maybe"
                st.rerun()

    # TAB 3: EXPORT
    with tab_export:
        st.session_state.step = 4
        df = pd.DataFrame([
            {
                "ID": p["id"],
                "Title": p["title"],
                "Journal": p["journal"],
                "Year": p["year"],
                "DOI": p["doi"],
                "Decision": decisions.get(p["id"], "Unscreened"),
                "PICO_Summary": "; ".join(
                    f"{k}:{','.join(v)}" for k, v in extract_pico(p["abstract"]).items() if v
                ),
            }
            for p in papers
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Screened Dataset (CSV)",
            data=csv_bytes,
            file_name="mini_rayyan_screened.csv",
            mime="text/csv",
        )
