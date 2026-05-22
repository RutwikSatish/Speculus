"""
SPECULUS — Supply Chain Risk Intelligence
ISO 31000 · COSO ERM · SCOR · World Bank WGI 2024
Built by Rutwik Satish · MS Engineering Management, Northeastern University
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json

from data_ingestor import fetch_gdelt_signals, fetch_federal_register_signals
from scoring_engine import score_supplier, RISK_DIMENSIONS, COSO_RESPONSES
from risk_register import build_register, export_register_csv
from ai_briefer import generate_risk_brief
from demo_data import DEMO_SUPPLIERS, DEMO_SIGNALS, DEMO_BANNER
from alternatives_engine import get_alternatives, format_alternatives_for_ai

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SPECULUS — Supply Chain Risk Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS — Dark scientific aesthetic ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500&family=Syne:wght@400;700;800&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"], .stApp {
    background-color: #080c14 !important;
    color: #e2e8f0 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 2px; }

/* ── Main content padding ── */
.main .block-container {
    padding: 1.5rem 2rem 3rem !important;
    max-width: 1400px !important;
}

/* ── Hero header ── */
.speculus-hero {
    position: relative;
    padding: 2.5rem 0 2rem;
    margin-bottom: 0;
    overflow: hidden;
}

.speculus-hero::before {
    content: '';
    position: absolute;
    top: -60px; left: -40px;
    width: 600px; height: 300px;
    background: radial-gradient(ellipse at 30% 50%, rgba(0, 120, 255, 0.08) 0%, transparent 70%);
    pointer-events: none;
}

.speculus-hero::after {
    content: '';
    position: absolute;
    top: 0; right: -100px;
    width: 400px; height: 200px;
    background: radial-gradient(ellipse, rgba(0, 200, 150, 0.05) 0%, transparent 70%);
    pointer-events: none;
}

.speculus-wordmark {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 400;
    letter-spacing: 0.35em;
    text-transform: uppercase;
    color: #3b82f6;
    margin-bottom: 0.6rem;
    opacity: 0.9;
}

.speculus-name {
    font-family: 'Syne', sans-serif;
    font-size: 56px;
    font-weight: 800;
    letter-spacing: -0.04em;
    line-height: 1;
    background: linear-gradient(135deg, #e2e8f0 0%, #93c5fd 40%, #34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.4rem;
}

.speculus-tagline {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 15px;
    font-weight: 300;
    color: #64748b;
    letter-spacing: 0.02em;
    margin-bottom: 1.2rem;
}

.speculus-tags {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 0;
}

.spec-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    padding: 4px 10px;
    border-radius: 3px;
    border: 1px solid rgba(59, 130, 246, 0.25);
    color: #3b82f6;
    background: rgba(59, 130, 246, 0.06);
    letter-spacing: 0.08em;
}

.spec-tag.green {
    border-color: rgba(52, 211, 153, 0.25);
    color: #34d399;
    background: rgba(52, 211, 153, 0.06);
}

/* ── Divider ── */
.spec-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.3), rgba(52, 211, 153, 0.2), transparent);
    margin: 1.5rem 0;
}

/* ── Section header ── */
.spec-section {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #3b82f6;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 10px;
}

.spec-section::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(59, 130, 246, 0.3), transparent);
}

/* ── Metric cards ── */
.metric-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 1.5rem;
}

.metric-card {
    background: linear-gradient(135deg, rgba(13, 17, 30, 0.8), rgba(15, 23, 42, 0.6));
    border: 1px solid rgba(59, 130, 246, 0.12);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #3b82f6, #34d399);
    opacity: 0.6;
}

.metric-card.red::before { background: linear-gradient(90deg, #ef4444, #f97316); }
.metric-card.amber::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.metric-card.green::before { background: linear-gradient(90deg, #34d399, #10b981); }

.metric-num {
    font-family: 'Syne', sans-serif;
    font-size: 36px;
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1;
    margin-bottom: 4px;
}

.metric-num.red   { color: #ef4444; }
.metric-num.amber { color: #f59e0b; }
.metric-num.green { color: #34d399; }
.metric-num.blue  { color: #3b82f6; }

.metric-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #475569;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* ── Risk cards ── */
.risk-card {
    background: linear-gradient(135deg, rgba(13, 17, 30, 0.9), rgba(15, 23, 42, 0.7));
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 10px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}

.risk-card:hover { border-color: rgba(59, 130, 246, 0.25); }

.risk-card.critical {
    border-color: rgba(239, 68, 68, 0.3);
    background: linear-gradient(135deg, rgba(30, 10, 10, 0.9), rgba(20, 8, 8, 0.8));
}

.risk-card.critical::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #ef4444, #f97316);
}

.risk-card.high {
    border-color: rgba(245, 158, 11, 0.25);
    background: linear-gradient(135deg, rgba(25, 18, 8, 0.9), rgba(20, 15, 5, 0.8));
}

.risk-card.high::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.risk-card.moderate::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: rgba(100, 116, 139, 0.4);
}

.risk-card.low::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #34d399, #10b981);
    opacity: 0.5;
}

.risk-score {
    font-family: 'Syne', sans-serif;
    font-size: 44px;
    font-weight: 800;
    letter-spacing: -0.04em;
    line-height: 1;
}

.score-critical { color: #ef4444; }
.score-high     { color: #f59e0b; }
.score-moderate { color: #94a3b8; }
.score-low      { color: #34d399; }

.risk-supplier {
    font-family: 'Syne', sans-serif;
    font-size: 17px;
    font-weight: 700;
    color: #e2e8f0;
    margin-bottom: 2px;
}

.risk-country {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #475569;
    letter-spacing: 0.1em;
}

.coso-pill {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.08em;
    margin-top: 6px;
}

.coso-avoid   { background: rgba(239,68,68,0.12); color: #ef4444; border: 1px solid rgba(239,68,68,0.25); }
.coso-reduce  { background: rgba(245,158,11,0.12); color: #f59e0b; border: 1px solid rgba(245,158,11,0.25); }
.coso-share   { background: rgba(59,130,246,0.12); color: #60a5fa; border: 1px solid rgba(59,130,246,0.25); }
.coso-accept  { background: rgba(52,211,153,0.12); color: #34d399; border: 1px solid rgba(52,211,153,0.25); }

.breach-alert {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #ef4444;
    background: rgba(239,68,68,0.08);
    border: 1px solid rgba(239,68,68,0.2);
    border-radius: 4px;
    padding: 4px 10px;
    margin-top: 6px;
    display: inline-block;
}

.signal-line {
    font-size: 12px;
    color: #475569;
    padding: 3px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    line-height: 1.5;
}

.signal-line:last-child { border-bottom: none; }

.signal-src {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #3b82f6;
    margin-right: 6px;
    opacity: 0.7;
}

.signal-src.demo { color: #f59e0b; }

.dim-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.dim-score {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 500;
}

.dim-breach { color: #ef4444; }
.dim-ok     { color: #475569; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080c14 0%, #0a0f1e 100%) !important;
    border-right: 1px solid rgba(59,130,246,0.1) !important;
}

section[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem !important;
}

/* ── Streamlit component overrides ── */
.stButton > button {
    background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
    color: white !important;
    border: 1px solid rgba(59,130,246,0.4) !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 0 20px rgba(29,78,216,0.2) !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    box-shadow: 0 0 30px rgba(59,130,246,0.3) !important;
    transform: translateY(-1px) !important;
}

.stTextArea textarea, .stTextInput input {
    background: rgba(13,17,30,0.8) !important;
    border: 1px solid rgba(59,130,246,0.2) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
}

.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: rgba(59,130,246,0.5) !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.1) !important;
}

.stSlider > div > div > div {
    background: linear-gradient(90deg, #1d4ed8, #34d399) !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: rgba(13,17,30,0.6) !important;
    border-radius: 8px !important;
    padding: 4px !important;
    gap: 4px !important;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 13px !important;
    color: #475569 !important;
    border-radius: 6px !important;
    padding: 6px 16px !important;
}

.stTabs [aria-selected="true"] {
    background: rgba(29,78,216,0.3) !important;
    color: #93c5fd !important;
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #1d4ed8, #34d399) !important;
    border-radius: 4px !important;
}

div[data-testid="stExpander"] {
    background: rgba(13,17,30,0.5) !important;
    border: 1px solid rgba(59,130,246,0.12) !important;
    border-radius: 10px !important;
}

.stAlert {
    background: rgba(13,17,30,0.8) !important;
    border-radius: 8px !important;
}

/* ── Toggle ── */
.stToggle label { color: #94a3b8 !important; font-family: 'Space Grotesk', sans-serif !important; }

/* ── Download button ── */
.stDownloadButton > button {
    background: rgba(13,17,30,0.8) !important;
    border: 1px solid rgba(59,130,246,0.25) !important;
    color: #60a5fa !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
}

/* ── Metric override ── */
div[data-testid="metric-container"] {
    background: rgba(13,17,30,0.6) !important;
    border: 1px solid rgba(59,130,246,0.1) !important;
    border-radius: 10px !important;
    padding: 1rem !important;
}

div[data-testid="metric-container"] label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    color: #475569 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}

div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif !important;
    font-size: 28px !important;
    font-weight: 800 !important;
    color: #e2e8f0 !important;
}

/* ── Footer ── */
.spec-footer {
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid rgba(255,255,255,0.05);
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #1e3a5f;
    letter-spacing: 0.05em;
    text-align: center;
    line-height: 1.8;
}

/* ── Plotly chart containers ── */
.js-plotly-plot { border-radius: 10px; overflow: hidden; }

/* ── Info banner ── */
.stInfo {
    background: rgba(29,78,216,0.08) !important;
    border: 1px solid rgba(59,130,246,0.2) !important;
    border-radius: 8px !important;
    color: #93c5fd !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 13px !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #3b82f6 !important; }

/* ── Select box ── */
.stSelectbox > div > div {
    background: rgba(13,17,30,0.8) !important;
    border: 1px solid rgba(59,130,246,0.2) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Session state ────────────────────────────────────────────────────────────
# Initialize ALL keys unconditionally with setdefault to prevent
# KeyError on Python 3.14 / Streamlit 1.57 re-renders
_DEFAULT_APPETITE = {
    "geopolitical": 35,
    "supplier_health": 45,
    "logistics": 40,
    "single_source": 50,
    "regulatory": 40
}
if "register" not in st.session_state:
    st.session_state["register"] = []
if "last_run" not in st.session_state:
    st.session_state["last_run"] = None
if "appetite" not in st.session_state:
    st.session_state["appetite"] = _DEFAULT_APPETITE.copy()

# ─── Groq key from secrets ────────────────────────────────────────────────────
groq_key = ""
try:
    groq_key = st.secrets["groq"]["api_key"]
    if groq_key == "your_groq_api_key_here":
        groq_key = ""
except Exception:
    pass

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 0.5rem 0 1.5rem">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 9px; 
                    letter-spacing: 0.3em; color: #1e3a5f; text-transform: uppercase; 
                    margin-bottom: 6px;">Supply Chain Risk Intelligence</div>
        <div style="font-family: 'Syne', sans-serif; font-size: 24px; font-weight: 800;
                    background: linear-gradient(135deg, #e2e8f0, #93c5fd);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    letter-spacing: -0.02em;">SPECULUS</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="spec-section">Risk Appetite</div>', unsafe_allow_html=True)
    st.caption("ISO 31000 §6.4.3 — Set max acceptable score per dimension")

    appetite = {}
    dim_config = [
        ("geopolitical",    "Geopolitical",    "🌍"),
        ("supplier_health", "Supplier Health", "🏭"),
        ("logistics",       "Logistics",       "🚢"),
        ("single_source",   "Single Source",   "⚠"),
        ("regulatory",      "Regulatory",      "📋"),
    ]
    for key, label, icon in dim_config:
        appetite[key] = st.slider(
            f"{icon} {label}",
            min_value=10, max_value=90,
            value=st.session_state["appetite"].get(key, _DEFAULT_APPETITE[key]),
            step=5
        )
    st.session_state["appetite"] = appetite

    st.markdown('<div class="spec-section" style="margin-top:1.5rem">API</div>', unsafe_allow_html=True)
    if groq_key:
        st.success("AI briefs active", icon="◈")
    else:
        groq_key = st.text_input(
            "Groq API Key",
            type="password",
            help="Free at console.groq.com — enables AI risk briefs"
        )

    st.markdown('<div class="spec-section" style="margin-top:1.5rem">Frameworks</div>', unsafe_allow_html=True)
    for fw in ["ISO 31000:2018", "COSO ERM 2017", "SCOR v13", "WB WGI 2024"]:
        st.markdown(f'<span class="spec-tag">◈ {fw}</span>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; 
                color: #1e3a5f; letter-spacing: 0.05em; line-height: 1.8;">
        Built by Rutwik Satish<br>
        MS Engineering Management<br>
        Northeastern University
    </div>
    """, unsafe_allow_html=True)

# ─── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="speculus-hero">
    <div class="speculus-wordmark">◈ Supply Chain Risk Intelligence Platform</div>
    <div class="speculus-name">SPECULUS</div>
    <div class="speculus-tagline">See the risk before it sees you — ISO 31000 · COSO ERM · SCOR · World Bank WGI 2024</div>
    <div class="speculus-tags">
        <span class="spec-tag">◈ Living Risk Register</span>
        <span class="spec-tag">◈ Real-time GDELT Signals</span>
        <span class="spec-tag green">◈ WGI 2024 Verified</span>
        <span class="spec-tag green">◈ COSO Response Engine</span>
        <span class="spec-tag">◈ AI Risk Briefs</span>
    </div>
</div>
<div class="spec-divider"></div>
""", unsafe_allow_html=True)

# ─── Mode toggle + supplier input ────────────────────────────────────────────
col_toggle, col_info = st.columns([1, 3])

with col_toggle:
    demo_mode = st.toggle("Demo Mode", value=True)  # Default ON — instant results

with col_info:
    if demo_mode:
        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; 
                    color: #f59e0b; padding: 8px 0;">
            ◈ DEMO — Pre-loaded portfolio · WGI scores real · Signals simulated
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; 
                    color: #34d399; padding: 8px 0;">
            ◈ LIVE — GDELT real-time signals · Federal Register trade policy
        </div>""", unsafe_allow_html=True)

if demo_mode:
    suppliers = DEMO_SUPPLIERS
    demo_signal_map = DEMO_SIGNALS
else:
    demo_signal_map = {}
    tab_manual, tab_upload = st.tabs(["Manual Entry", "Upload CSV"])

    with tab_manual:
        st.markdown('<p style="font-family: JetBrains Mono, monospace; font-size: 11px; color: #475569; margin-bottom: 8px;">One supplier per line · Format: Name, Country Code (ISO 2-letter)</p>', unsafe_allow_html=True)
        raw_input = st.text_area(
            "Suppliers",
            value="",
            height=160,
            placeholder="Pakistan Vendor, PK\nFoxconn Technology, CN\nTSMC, TW\nBosch Automotive, DE\nFlex Ltd, SG",
            label_visibility="collapsed"
        )
        suppliers = []
        for line in raw_input.strip().split("\n"):
            if "," in line.strip():
                parts = line.strip().split(",", 1)
                name = parts[0].strip()
                country = parts[1].strip().upper()[:2]
                if name and country:
                    suppliers.append({"name": name, "country": country})

    with tab_upload:
        uploaded = st.file_uploader("CSV: supplier_name, country_code", type=["csv"])
        if uploaded:
            df_up = pd.read_csv(uploaded)
            if "supplier_name" in df_up.columns and "country_code" in df_up.columns:
                suppliers = [{"name": r["supplier_name"], "country": str(r["country_code"]).upper()[:2]} for _, r in df_up.iterrows()]
                st.success(f"Loaded {len(suppliers)} suppliers")
            else:
                st.error("CSV must have columns: supplier_name, country_code")
                suppliers = []

st.markdown("<br>", unsafe_allow_html=True)

# ─── Run button ───────────────────────────────────────────────────────────────
col_btn, col_meta = st.columns([2, 4])
with col_btn:
    run = st.button("◈  Run Risk Register", type="primary", use_container_width=True)
with col_meta:
    if st.session_state["last_run"]:
        st.markdown(f'<div style="font-family: JetBrains Mono, monospace; font-size: 11px; color: #1e3a5f; padding: 12px 0;">Last run: {st.session_state["last_run"]}</div>', unsafe_allow_html=True)

# ─── Execution ────────────────────────────────────────────────────────────────
if run and suppliers:
    with st.spinner("Scoring suppliers..." if demo_mode else "Fetching live signals and scoring suppliers..."):
        prog = st.progress(0)
        all_scored = []

        for i, s in enumerate(suppliers):
            prog.progress(int((i / len(suppliers)) * 85),
                         text=f"Analysing {s['name']} ({s['country']})...")

            if demo_mode and s["name"] in demo_signal_map:
                g_sig = demo_signal_map[s["name"]]
                f_sig = []
            else:
                g_sig = fetch_gdelt_signals(s["name"], s["country"])
                f_sig = fetch_federal_register_signals(s["country"])

            scored = score_supplier(
                s["name"], s["country"], g_sig, f_sig,
                st.session_state["appetite"]
            )
            all_scored.append(scored)

        prog.progress(95, text="Building register...")
        register = build_register(all_scored)
        st.session_state["register"] = register
        st.session_state["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        prog.empty()

    breaches = sum(1 for r in register if r["breach"])
    if breaches:
        st.error(f"◈  {breaches} threshold breach{'es' if breaches > 1 else ''} detected — COSO response required")
    else:
        st.success(f"◈  Register built for {len(register)} suppliers — all within appetite")

elif run and not suppliers:
    st.warning("Add at least one supplier above")

# ─── Results ─────────────────────────────────────────────────────────────────
if st.session_state["register"]:
    register = st.session_state["register"]

    st.markdown('<div class="spec-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="spec-section">Risk Summary</div>', unsafe_allow_html=True)

    # ── Summary metrics ──────────────────────────────────────────────────────
    total      = len(register)
    critical   = sum(1 for r in register if r["composite_score"] >= 70)
    high_risk  = sum(1 for r in register if 55 <= r["composite_score"] < 70)
    moderate   = sum(1 for r in register if 40 <= r["composite_score"] < 55)
    low_risk   = sum(1 for r in register if r["composite_score"] < 40)
    breaches   = sum(1 for r in register if r["breach"])

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card blue">
            <div class="metric-num blue">{total}</div>
            <div class="metric-label">Suppliers Analysed</div>
        </div>
        <div class="metric-card {'red' if breaches else 'green'}">
            <div class="metric-num {'red' if breaches else 'green'}">{breaches}</div>
            <div class="metric-label">Threshold Breaches</div>
        </div>
        <div class="metric-card {'amber' if (critical + high_risk) else 'green'}">
            <div class="metric-num {'amber' if (critical + high_risk) else 'green'}">{critical + high_risk}</div>
            <div class="metric-label">Critical / High Risk</div>
        </div>
        <div class="metric-card green">
            <div class="metric-num green">{low_risk}</div>
            <div class="metric-label">Within Appetite</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Radar + Bar charts ───────────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns([1.2, 1])

    with chart_col1:
        st.markdown('<div class="spec-section">Risk Distribution</div>', unsafe_allow_html=True)
        names  = [r["name"][:20] for r in register]
        scores = [r["composite_score"] for r in register]
        colors = ["#ef4444" if s >= 70 else "#f59e0b" if s >= 55 else "#94a3b8" if s >= 40 else "#34d399" for s in scores]

        fig_bar = go.Figure(go.Bar(
            x=scores,
            y=names,
            orientation='h',
            marker=dict(
                color=colors,
                opacity=0.85,
                line=dict(color='rgba(255,255,255,0.05)', width=0.5)
            ),
            hovertemplate='<b>%{y}</b><br>Score: %{x}/100<extra></extra>'
        ))

        # Appetite lines
        avg_app = sum(st.session_state["appetite"].values()) / len(st.session_state["appetite"])
        fig_bar.add_vline(
            x=avg_app,
            line_dash="dot",
            line_color="rgba(59,130,246,0.5)",
            annotation_text="avg appetite",
            annotation_font=dict(color="#3b82f6", size=10)
        )

        fig_bar.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(13,17,30,0.4)',
            margin=dict(l=0, r=20, t=10, b=10),
            height=340,
            xaxis=dict(
                range=[0, 100],
                gridcolor='rgba(255,255,255,0.04)',
                tickfont=dict(family='JetBrains Mono', size=10, color='#475569'),
                title=dict(text='Risk Score', font=dict(family='JetBrains Mono', size=10, color='#475569'))
            ),
            yaxis=dict(
                tickfont=dict(family='Space Grotesk', size=11, color='#94a3b8'),
                gridcolor='rgba(255,255,255,0.02)'
            ),
            font=dict(family='Space Grotesk')
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

    with chart_col2:
        st.markdown('<div class="spec-section">COSO Response Mix</div>', unsafe_allow_html=True)
        coso_counts = {"Avoid": 0, "Reduce": 0, "Share": 0, "Accept": 0}
        for r in register:
            coso_counts[r["coso_response"]] = coso_counts.get(r["coso_response"], 0) + 1

        active = {k: v for k, v in coso_counts.items() if v > 0}
        coso_colors = {"Avoid": "#ef4444", "Reduce": "#f59e0b", "Share": "#60a5fa", "Accept": "#34d399"}

        fig_pie = go.Figure(go.Pie(
            labels=list(active.keys()),
            values=list(active.values()),
            marker=dict(
                colors=[coso_colors[k] for k in active.keys()],
                line=dict(color='#080c14', width=2)
            ),
            textfont=dict(family='JetBrains Mono', size=11),
            hovertemplate='<b>%{label}</b><br>%{value} suppliers<extra></extra>',
            hole=0.6
        ))
        fig_pie.add_annotation(
            text=f"<b>{total}</b><br><span style='font-size:10px'>suppliers</span>",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(family='Syne', size=16, color='#e2e8f0')
        )
        fig_pie.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=10, b=10),
            height=340,
            showlegend=True,
            legend=dict(
                font=dict(family='JetBrains Mono', size=10, color='#475569'),
                bgcolor='rgba(0,0,0,0)',
                bordercolor='rgba(0,0,0,0)'
            )
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

    # ── Choropleth world map ─────────────────────────────────────────────────
    st.markdown('<div class="spec-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="spec-section">Global Risk Map</div>', unsafe_allow_html=True)
    st.caption("Supplier locations colored by composite risk score · WGI 2024 + ACLED 2025 + GDELT signals")

    # Build map data
    iso3_map = {
        "CN":"CHN","TW":"TWN","KR":"KOR","JP":"JPN","DE":"DEU","US":"USA",
        "IN":"IND","MX":"MEX","VN":"VNM","MY":"MYS","SG":"SGP","TH":"THA",
        "ID":"IDN","BD":"BGD","PH":"PHL","PK":"PAK","BR":"BRA","TR":"TUR",
        "GB":"GBR","FR":"FRA","IT":"ITA","NL":"NLD","SE":"SWE","PL":"POL",
        "CA":"CAN","AU":"AUS","SA":"SAU","AE":"ARE","ZA":"ZAF","EG":"EGY",
        "NG":"NGA","UA":"UKR","RU":"RUS","IL":"ISR","CZ":"CZE","HU":"HUN",
        "RO":"ROU","ES":"ESP",
    }
    map_countries  = [iso3_map.get(r["country"], r["country"]) for r in register]
    map_scores     = [r["composite_score"] for r in register]
    map_labels     = [f"{r['name']} ({r['country']})<br>Score: {r['composite_score']}/100<br>COSO: {r['coso_response']}" for r in register]

    fig_map = go.Figure(go.Choropleth(
        locations=map_countries,
        z=map_scores,
        text=map_labels,
        colorscale=[
            [0.0,  "#0f2940"],
            [0.3,  "#1a4a6e"],
            [0.5,  "#0d7a4e"],
            [0.65, "#f59e0b"],
            [0.8,  "#ef4444"],
            [1.0,  "#7f1d1d"],
        ],
        zmin=0, zmax=100,
        marker_line_color="rgba(255,255,255,0.08)",
        marker_line_width=0.5,
        colorbar=dict(
            title=dict(text="Risk Score", font=dict(family="JetBrains Mono", size=10, color="#475569")),
            tickfont=dict(family="JetBrains Mono", size=9, color="#475569"),
            bgcolor="rgba(0,0,0,0)",
            outlinecolor="rgba(255,255,255,0.1)",
            len=0.6,
        ),
        hovertemplate="%{text}<extra></extra>",
    ))

    fig_map.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0),
        height=360,
        geo=dict(
            bgcolor="rgba(8,12,20,1)",
            showframe=False,
            showcoastlines=True,
            coastlinecolor="rgba(255,255,255,0.08)",
            showland=True,
            landcolor="rgba(20,30,50,0.8)",
            showocean=True,
            oceancolor="rgba(8,12,20,1)",
            showcountries=True,
            countrycolor="rgba(255,255,255,0.05)",
            projection_type="natural earth",
        ),
    )
    st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})

    # ── Risk register cards ──────────────────────────────────────────────────
    st.markdown('<div class="spec-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="spec-section">Risk Register</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-family: JetBrains Mono, monospace; font-size: 11px; '
        'color: #1e3a5f; margin-bottom: 1rem;">'
        'Ranked by composite score · ISO 31000 dimensions · COSO ERM responses · WB WGI 2024 baseline</p>',
        unsafe_allow_html=True
    )

    for r in register:
        score  = r["composite_score"]
        breach = r["breach"]
        coso   = r["coso_response"]
        sigs   = r.get("signals", [])

        if score >= 70:   card_cls = "critical"; score_cls = "score-critical"
        elif score >= 55: card_cls = "high";     score_cls = "score-high"
        elif score >= 40: card_cls = "moderate"; score_cls = "score-moderate"
        else:             card_cls = "low";      score_cls = "score-low"

        coso_cls = f"coso-{coso.lower()}"

        with st.container():
            st.markdown(f'<div class="risk-card {card_cls}">', unsafe_allow_html=True)

            c1, c2, c3 = st.columns([1, 2.5, 3])

            with c1:
                breach_html = '<div class="breach-alert">⚠ BREACH</div>' if breach else ''
                st.markdown(f"""
                <div style="padding: 4px 0">
                    <div class="risk-score {score_cls}">{score}</div>
                    <div style="font-family: JetBrains Mono, monospace; font-size: 10px; 
                                color: #1e3a5f; margin: 2px 0 8px">/100</div>
                    <span class="coso-pill {coso_cls}">COSO: {coso}</span>
                    {breach_html}
                </div>
                """, unsafe_allow_html=True)

            with c2:
                scor  = r.get("scor_impact", "")
                zsid  = r.get("zsidisin_source", "")
                breach_dims = ", ".join(r.get("breached_dims", [])) if breach else ""

                st.markdown(f"""
                <div style="padding: 4px 0">
                    <div class="risk-supplier">{r['name']}</div>
                    <div class="risk-country">{r['country']} · SCOR: {scor} · {zsid} risk</div>
                    <div style="height:8px"></div>
                """, unsafe_allow_html=True)

                if breach_dims:
                    st.markdown(f'<div style="font-family: JetBrains Mono, monospace; font-size: 10px; color: #ef4444; margin-bottom: 6px;">⚠ {breach_dims}</div>', unsafe_allow_html=True)

                if sigs:
                    for sig in sigs[:3]:
                        is_demo = "DEMO" in sig.get("source", "")
                        src_cls = "demo" if is_demo else ""
                        title   = sig.get("title", "")[:88]
                        st.markdown(
                            f'<div class="signal-line">'
                            f'<span class="signal-src {src_cls}">[{sig.get("source","")[:12]}]</span>'
                            f'{title}{"…" if len(sig.get("title","")) > 88 else ""}</div>',
                            unsafe_allow_html=True
                        )
                else:
                    if demo_mode:
                        st.markdown('<div style="font-family: JetBrains Mono, monospace; font-size: 11px; color: #1e3a5f;">◈ No pre-seeded signals for this supplier · WGI baseline score only</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="font-family: JetBrains Mono, monospace; font-size: 11px; color: #1e3a5f;">◈ No GDELT signals detected in past 72h · Score based on WGI 2024 baseline</div>', unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

            with c3:
                st.markdown('<div class="dim-label" style="margin-bottom:8px">ISO 31000 Dimensions</div>', unsafe_allow_html=True)
                dims = r.get("dimensions", {})
                dim_labels = [
                    ("geopolitical",    "Geopolitical"),
                    ("supplier_health", "Supplier Health"),
                    ("logistics",       "Logistics"),
                    ("single_source",   "Single Source"),
                    ("regulatory",      "Regulatory"),
                ]
                for dk, dl in dim_labels:
                    d_score = dims.get(dk, 0)
                    d_app   = st.session_state["appetite"].get(dk, 50)
                    over    = d_score > d_app
                    score_cls_d = "dim-breach" if over else "dim-ok"

                    ca, cb, cc = st.columns([2.2, 4, 0.7])
                    ca.markdown(f'<div class="dim-label">{dl}</div>', unsafe_allow_html=True)
                    cb.progress(min(d_score, 100) / 100)
                    # Show geopolitical breakdown tooltip
                    if dk == "geopolitical" and r.get("geo_detail"):
                        gd = r["geo_detail"]
                        wgi_v  = round(gd.get("wgi_component", 0))
                        acl_v  = round(gd.get("acled_component", 0))
                        gdt_v  = round(gd.get("gdelt_component", 0))
                        acled_lbl = gd.get("acled_data", {}).get("source", "")
                        geo_html = f'<div class="dim-score {score_cls_d}">{d_score}</div>'
                        geo_note = f'<div style="font-family:JetBrains Mono,monospace;font-size:8px;color:#1e3a5f;line-height:1.4;">WGI {wgi_v} · ACLED {acl_v}<br>{acled_lbl[:12]}</div>'
                        cc.markdown(geo_html + geo_note, unsafe_allow_html=True)
                    else:
                        cc.markdown(f'<div class="dim-score {score_cls_d}">{d_score}</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        # Fix 5: Show alternatives for breaching suppliers
        if breach:
            alts = get_alternatives(r['name'], r['country'], r['composite_score'])
            if alts:
                with st.expander(f"◈  Alternative Suppliers — {r['name']}", expanded=False):
                    st.markdown('<div style="font-family: JetBrains Mono, monospace; font-size: 9px; letter-spacing: 0.2em; text-transform: uppercase; color: #3b82f6; margin-bottom: 12px;">Lower-risk alternatives · Same category · Sorted by risk score</div>', unsafe_allow_html=True)
                    for alt in alts:
                        risk_c = "#ef4444" if alt["risk"] >= 55 else "#f59e0b" if alt["risk"] >= 40 else "#34d399"
                        st.markdown(f'''<div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.05);">
                            <div>
                                <span style="font-family: Syne, sans-serif; font-weight:700; font-size:15px; color:#e2e8f0;">{alt["name"]}</span>
                                <span style="font-family: JetBrains Mono, monospace; font-size:10px; color:#475569; margin-left:8px;">{alt["country"]}</span>
                                <div style="font-size:12px; color:#64748b; margin-top:2px;">{alt["note"]}</div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-family:Syne,sans-serif; font-size:22px; font-weight:800; color:{risk_c};">{alt["risk"]}</div>
                                <div style="font-family:JetBrains Mono,monospace; font-size:9px; color:#475569;">~{alt["qual_months"]}mo to qualify</div>
                            </div>
                        </div>''', unsafe_allow_html=True)
                    st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:#1e3a5f;margin-top:8px;">Qualification timelines per APICS CSCP guidelines. Verify suitability before engagement.</div>', unsafe_allow_html=True)

        # AI brief with alternatives injected into prompt
        if breach and groq_key:
            with st.expander(f"◈  AI Risk Brief — {r['name']}", expanded=False):
                with st.spinner("Generating brief..."):
                    # Inject alternatives context into brief
                    alt_context = format_alternatives_for_ai(r["name"], r["country"], r["composite_score"], r.get("breached_dims", []))
                    r_with_alts = {**r, "alternatives_context": alt_context}
                    brief = generate_risk_brief(r_with_alts, st.session_state["appetite"], groq_key)
                st.markdown(f'<div style="font-family: Space Grotesk, sans-serif; font-size: 13px; line-height: 1.7; color: #94a3b8;">{brief}</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Export ───────────────────────────────────────────────────────────────
    st.markdown('<div class="spec-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="spec-section">Export</div>', unsafe_allow_html=True)

    ec1, ec2 = st.columns(2)
    with ec1:
        csv_data = export_register_csv(register)
        st.download_button(
            "↓  Download Register CSV",
            data=csv_data,
            file_name=f"speculus_register_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with ec2:
        json_data = json.dumps(register, indent=2, default=str)
        st.download_button(
            "↓  Download Register JSON",
            data=json_data,
            file_name=f"speculus_register_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="spec-footer">
    SPECULUS · Supply Chain Risk Intelligence · ISO 31000:2018 · COSO ERM 2017 · SCOR v13 (ASCM)<br>
    Country baseline: World Bank Worldwide Governance Indicators 2024 · Signals: GDELT 2.0 + US Federal Register<br>
    Zsidisin & Ritchie (2009) · Chopra & Meindl (2021) · Built by Rutwik Satish · Northeastern University
</div>
""", unsafe_allow_html=True)
