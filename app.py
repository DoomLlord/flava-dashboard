import re
import json
import os
from collections import defaultdict

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_fetcher import fetch_sheet_data, get_sheet_names
from reports_fetcher import fetch_all_reports, save_report
from infloww_clientapi import parse_amount
from infloww_data import get_creator_stats, get_infloww_creators, week_range

# ── Notes persistence ─────────────────────────────────────────────────────────
_NOTES_FILE = os.path.join(os.path.dirname(__file__), "fan_notes.json")

def _load_notes() -> dict:
    if os.path.exists(_NOTES_FILE):
        with open(_NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save_note(creator_id: str, fan_id: str, text: str) -> None:
    notes = _load_notes()
    notes.setdefault(creator_id, {})[fan_id] = text
    with open(_NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Flava Management",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={},
)

# ── Auth ──────────────────────────────────────────────────────────────────────
_PASSWORD = "FlavaXCuhvet123"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;900&display=swap');
    * { font-family: 'Nunito', sans-serif; }
    .stApp { background-color: #000; }
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="InputInstructions"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    [data-testid="stForm"] { border: none !important; padding: 0 !important; }
    [data-testid="stForm"] [data-testid="stTextInput"] > div > div,
    [data-testid="stForm"] [data-testid="stTextInput"] > div > div > div,
    [data-testid="stForm"] [data-testid="stTextInput"] input,
    [data-testid="stForm"] [data-testid="stTextInput"] > div {
        background: #111 !important;
        border-color: #2a2a2a !important;
        border-radius: 12px !important;
        box-shadow: none !important;
    }
    [data-testid="stForm"] [data-testid="stTextInput"] > div > div {
        border: 1px solid #2a2a2a !important;
    }
    [data-testid="stForm"] [data-testid="stTextInput"] > div > div:focus-within,
    [data-testid="stForm"] [data-testid="stTextInput"] > div > div:focus-within > div {
        border-color: #7c4dff !important;
        box-shadow: 0 0 0 2px rgba(124,77,255,0.25) !important;
    }
    [data-testid="stForm"] [data-testid="stTextInput"] input {
        color: #fff !important; font-size: 1rem !important; font-weight: 600 !important;
    }
    [data-testid="stForm"] [data-testid="stTextInput"] input::placeholder { color: #444 !important; }
    [data-testid="stFormSubmitButton"] > button {
        background: #fff !important; color: #000 !important;
        border: none !important; border-radius: 12px !important;
        font-weight: 900 !important; font-size: 0.9rem !important;
        letter-spacing: 0.12em !important; text-transform: uppercase !important;
        width: 100% !important; padding: 0.75rem !important;
        transition: opacity 0.15s !important;
    }
    [data-testid="stFormSubmitButton"] > button:hover { opacity: 0.85 !important; }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        st.markdown("<div style='height:20vh'></div>", unsafe_allow_html=True)

        st.markdown(
            '<div style="text-align:center;margin-bottom:3rem">'
            '<div style="font-size:3.8rem;font-weight:900;color:#fff;letter-spacing:-0.03em;'
            'line-height:1;margin-bottom:0.5rem;font-family:Nunito">cuhvet</div>'
            '<div style="font-size:0.72rem;color:#555;font-weight:700;letter-spacing:0.3em;'
            'text-transform:uppercase">Management Dashboard</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            pw = st.text_input(
                "Password",
                type="password",
                placeholder="Enter password...",
                label_visibility="collapsed",
            )
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Enter", use_container_width=True)

        if submitted:
            if pw == _PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.markdown(
                    '<div style="color:#ff5252;font-size:0.8rem;font-weight:700;'
                    'text-align:center;margin-top:0.8rem;letter-spacing:0.05em">Incorrect password</div>',
                    unsafe_allow_html=True,
                )

    st.stop()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;900&display=swap');
* { font-family: 'Nunito', sans-serif; }
.stApp { background-color: #000000; color: #ffffff; }

[data-testid="stSidebar"] {
    background: #0c0c0c; border-right: 1px solid #1c1c1c;
    min-width: 210px !important; max-width: 210px !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important; display: flex;
    flex-direction: column; height: 100vh;
}
[data-testid="stSidebar"] .block-container,
[data-testid="stSidebarContent"] { padding: 0 !important; }
[data-testid="stSidebar"] .stButton,
[data-testid="stSidebar"] [data-testid="element-container"],
[data-testid="stSidebar"] .stElementContainer { margin: 0 !important; padding: 0 !important; }
[data-testid="stSidebar"] .stVerticalBlock { gap: 0 !important; }

.brand-wrap { padding: 1.8rem 1.4rem 1.6rem; border-bottom: 1px solid #1c1c1c; margin-bottom: 0.4rem; }
.brand-logo { font-size: 2.6rem; font-weight: 900; color: #fff; letter-spacing: -0.02em; line-height: 1; }

.nav-section-label {
    font-size: 0.58rem; color: #3a3a3a; letter-spacing: 0.25em;
    text-transform: uppercase; padding: 1rem 1.4rem 0.5rem; font-weight: 700;
}

[data-testid="stSidebar"] .stButton > button {
    width: 100% !important; background: transparent !important;
    color: #666 !important; border: none !important;
    border-left: 3px solid transparent !important; border-radius: 0 !important;
    padding: 0.7rem 1.4rem !important; text-align: left !important;
    font-size: 0.92rem !important; font-weight: 600 !important;
    transition: background 0.12s ease, color 0.12s ease !important;
    box-shadow: none !important; line-height: 1.4 !important;
    min-height: 2.6rem !important; height: auto !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #161616 !important; color: #ccc !important;
    border-left: 3px solid #333 !important;
}
[data-testid="stSidebar"] .nav-active .stButton > button {
    background: #222 !important; color: #fff !important;
    border-left: 3px solid #fff !important; font-weight: 900 !important;
}

[data-testid="stSidebar"] .refresh-wrap .stButton > button {
    color: #555 !important; border: 1px solid #1e1e1e !important;
    border-left: 1px solid #1e1e1e !important; border-radius: 8px !important;
    padding: 0.5rem 1rem !important; font-size: 0.72rem !important;
    text-align: center !important; letter-spacing: 0.12em !important;
    text-transform: uppercase !important; margin: 0 1.2rem !important;
    width: calc(100% - 2.4rem) !important;
}
[data-testid="stSidebar"] .refresh-wrap .stButton > button:hover {
    background: #161616 !important; color: #aaa !important;
    border-color: #333 !important; border-left-color: #333 !important;
}
.refresh-wrap { padding: 0.8rem 0 1.2rem; border-top: 1px solid #1c1c1c; }

[data-testid="stMetric"] {
    background: #0a0a0a; border: 1px solid #1a1a1a;
    border-radius: 16px; padding: 1.2rem 1.6rem;
}
[data-testid="stMetricLabel"] { color: #777 !important; font-size: 0.68rem !important; text-transform: uppercase; letter-spacing: 0.12em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
[data-testid="stMetricValue"] { color: #fff !important; font-size: 1.55rem !important; font-weight: 700; white-space: nowrap; }

.section-header {
    font-size: 0.7rem; font-weight: 900; color: #fff;
    text-transform: uppercase; letter-spacing: 0.22em;
    margin: 2.4rem 0 1.2rem; display: flex; align-items: center; gap: 1rem;
}
.section-header::after { content: ''; flex: 1; height: 1px; background: #222; }

.badge-wrap {
    display: inline-flex; align-items: center; gap: 0.5rem;
    background: #0d0d0d; border: 1px solid #1e1e1e;
    border-radius: 20px; padding: 0.3rem 0.9rem;
    font-size: 0.72rem; color: #888; letter-spacing: 0.08em;
    text-transform: uppercase; font-weight: 700; margin-bottom: 1.2rem;
}
.dot-purple { width: 6px; height: 6px; border-radius: 50%; background: #7c4dff; display:inline-block; }
.dot-green  { width: 6px; height: 6px; border-radius: 50%; background: #69f0ae; display:inline-block; }

[data-testid="stTabs"] button {
    color: #666 !important; font-size: 0.88rem !important;
    font-weight: 700 !important; font-family: 'Nunito', sans-serif !important;
    border-bottom: 2px solid transparent !important;
    padding: 0.6rem 1.2rem !important; background: transparent !important;
}
[data-testid="stTabs"] button:hover { color: #aaa !important; }
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #fff !important; border-bottom: 2px solid #7c4dff !important;
}
[data-testid="stTabs"] [data-testid="stTabsListContainer"] {
    background: transparent !important; border-bottom: 1px solid #1a1a1a !important; gap: 0 !important;
}

.dark-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.dark-table th {
    color: #555; text-transform: uppercase; font-size: 0.65rem;
    letter-spacing: 0.15em; padding: 0.9rem 1.2rem;
    border-bottom: 1px solid #1a1a1a; text-align: left; font-weight: 700;
}
.dark-table td { padding: 0.85rem 1.2rem; border-bottom: 1px solid #0d0d0d; color: #ccc; background: #050505; }
.dark-table tr:hover td { background: #0f0f0f; color: #fff; }
.dark-table tr:last-child td { border-bottom: none; }
.amt { color: #fff; font-weight: 600; font-variant-numeric: tabular-nums; }
.badge { border-radius: 6px; padding: 3px 10px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em; }
.badge-paid   { background: #0d1f0d; color: #4ade80; border: 1px solid #1a3a1a; }
.badge-unpaid { background: #1f0d0d; color: #888;    border: 1px solid #3a1a1a; }

.empty-state {
    color: #aaa !important; padding: 2.5rem; background: #050505;
    border: 1px solid #1a1a1a; border-radius: 12px;
    text-align: center; font-size: 0.88rem; letter-spacing: 0.05em; font-weight: 600;
}
.page-title { font-size: 3rem; font-weight: 900; color: #fff; letter-spacing: -0.02em; margin-bottom: 0.3rem; line-height: 1; }
.page-sub { font-size: 0.82rem; color: #555; margin-bottom: 1.8rem; letter-spacing: 0.04em; }

hr { border-color: #1a1a1a; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSpinner"] p { display: none !important; }
[data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebar"] {
    transform: none !important; display: flex !important;
    visibility: visible !important; opacity: 1 !important;
    min-width: 200px !important; max-width: 220px !important;
}
.sidebar-scroll { overflow-y: auto; flex: 1; }
.sidebar-scroll::-webkit-scrollbar { width: 3px; }
.sidebar-scroll::-webkit-scrollbar-thumb { background: #1e1e1e; border-radius: 2px; }

/* Selectbox — full dark override */
[data-testid="stSelectbox"] > div > div {
    background-color: #111 !important;
    border: 1px solid #333 !important;
    border-radius: 12px !important;
    box-shadow: none !important;
}
[data-testid="stSelectbox"] > div > div:hover { border-color: #7c4dff !important; }
[data-testid="stSelectbox"] [data-baseweb="select"] > div { background-color: #111 !important; border: 1px solid #333 !important; border-radius: 12px !important; box-shadow: none !important; }
[data-testid="stSelectbox"] [data-baseweb="select"] > div:hover { border-color: #7c4dff !important; }
[data-testid="stSelectbox"] * { background-color: transparent !important; color: #fff !important; font-weight: 700 !important; }
[data-testid="stSelectbox"] > div > div { background-color: #111 !important; }
[data-testid="stSelectbox"] svg { fill: #aaa !important; color: #aaa !important; }

/* Dropdown list */
[data-baseweb="popover"] { z-index: 9999 !important; }
[data-baseweb="popover"] > div { background: #111 !important; border: 1px solid #2a2a2a !important; border-radius: 14px !important; box-shadow: 0 20px 50px rgba(0,0,0,0.9) !important; overflow: hidden !important; padding: 6px !important; }
[data-baseweb="popover"] ul { background: transparent !important; }
[data-baseweb="popover"] li { background: transparent !important; color: #aaa !important; font-size: 0.82rem !important; font-weight: 700 !important; font-family: 'Nunito', sans-serif !important; border-radius: 8px !important; padding: 0.5rem 1rem !important; }
[data-baseweb="popover"] li:hover { background: #1e1e1e !important; color: #fff !important; }
[data-baseweb="popover"] li[aria-selected="true"] { background: #1a0f35 !important; color: #9c6fff !important; }

/* Fan rows */
.fan-row {
    display: flex; align-items: center;
    padding: 0.7rem 1.2rem;
    border-bottom: 1px solid #0d0d0d;
    background: #050505;
    transition: background 0.1s;
}
.fan-row:hover { background: #0f0f0f; }
.fan-row:last-child { border-bottom: none; }
.fan-rank { color: #333; font-size: 0.8rem; min-width: 36px; }
.fan-name { color: #fff; font-weight: 700; font-size: 0.9rem; flex: 1; }
.fan-amt  { color: #fff; font-weight: 700; min-width: 90px; text-align: right; font-variant-numeric: tabular-nums; }
.fan-sub  { color: #555; font-size: 0.82rem; min-width: 80px; text-align: right; font-variant-numeric: tabular-nums; }
.fan-has-note { color: #7c4dff !important; }

/* Notes popover button */
[data-testid="stPopover"] button {
    background: transparent !important;
    border: 1px solid #1e1e1e !important;
    border-radius: 6px !important;
    color: #333 !important;
    font-size: 0.75rem !important;
    padding: 0.2rem 0.6rem !important;
    min-height: unset !important;
    height: auto !important;
}
[data-testid="stPopover"] button:hover { border-color: #444 !important; color: #aaa !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
RAINBOW = ["#e040fb", "#7c4dff", "#448aff", "#00b0ff", "#00e5ff", "#69f0ae", "#eeff41", "#ffab40", "#ff5252"]
PLOT_LAYOUT = dict(paper_bgcolor="#050505", plot_bgcolor="#050505", font_color="#888", margin=dict(l=10, r=10, t=30, b=10))

# ── Grouping ──────────────────────────────────────────────────────────────────
_SUFFIX_RE = re.compile(r'\s+(FREE|Couple|Couples)\s*$', re.IGNORECASE)

def get_base_name(name: str) -> str:
    return _SUFFIX_RE.sub("", name).strip()

def group_creators(creators: list) -> dict:
    groups: dict = defaultdict(list)
    for c in creators:
        groups[get_base_name(c.get("name", "Unknown"))].append(c)
    return {k: sorted(v, key=lambda c: len(c.get("name", ""))) for k, v in groups.items()}

def tab_label(creator_name: str, base: str) -> str:
    suffix = creator_name[len(base):].strip()
    return suffix if suffix else "Main"

def find_matching_sheet(creator_name: str, sheet_names: list) -> str | None:
    cn = creator_name.lower().strip()
    for s in sheet_names:
        if s.lower().strip() == cn:
            return s
    stripped = _SUFFIX_RE.sub("", cn).strip()
    if stripped != cn:
        for s in sheet_names:
            if s.lower().strip() == stripped:
                return s
    return None

def is_truthy(val) -> bool:
    return str(val).strip().upper() in ("TRUE", "1", "YES")

def fmt_money(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:,.2f}"

def cents(v) -> float:
    try:
        return float(v) / 100
    except Exception:
        return 0.0

# ── Week selector helpers ─────────────────────────────────────────────────────
def _week_label(offset: int) -> str:
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    this_monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    ws = this_monday - timedelta(weeks=offset)
    we = now if offset == 0 else ws + timedelta(weeks=1) - timedelta(seconds=1)
    if offset == 0:
        return f"This Week  ({ws.strftime('%b %d')} – now)"
    elif offset == 1:
        return f"Last Week  ({ws.strftime('%b %d')} – {we.strftime('%b %d')})"
    else:
        return f"{offset} Weeks Ago  ({ws.strftime('%b %d')} – {we.strftime('%b %d')})"

_WEEK_OPTIONS = [_week_label(i) for i in range(8)]

# ── Session state ─────────────────────────────────────────────────────────────
if "selected_group" not in st.session_state:
    st.session_state.selected_group = None
if "week_offset" not in st.session_state:
    st.session_state.week_offset = 0

# ── Load creators + reports ───────────────────────────────────────────────────
with st.spinner(""):
    creators = get_infloww_creators()
    all_reports = fetch_all_reports()

if not creators:
    st.error("Nije moguće učitati creators sa Infloww API-ja.")
    st.stop()

grouped = group_creators(creators)
group_names = list(grouped.keys())

if st.session_state.selected_group not in group_names:
    st.session_state.selected_group = group_names[0]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="brand-wrap"><div class="brand-logo">cuhvet</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-section-label">Creators</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-scroll">', unsafe_allow_html=True)
    for gname in group_names:
        is_active = gname == st.session_state.selected_group
        st.markdown(f'<div class="{"nav-active" if is_active else ""}">', unsafe_allow_html=True)
        if st.button(gname, key=f"nav_{gname}"):
            st.session_state.selected_group = gname
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
    st.markdown('<div class="refresh-wrap">', unsafe_allow_html=True)
    if st.button("↺  Refresh Data", key="refresh"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── Resolve ───────────────────────────────────────────────────────────────────
selected_group = st.session_state.selected_group
members = grouped[selected_group]
sheet_names = get_sheet_names()

page_sub = "  ·  ".join(f"@{c.get('userName', '')}" for c in members)
week_offset = st.session_state.week_offset

title_col, week_col = st.columns([3, 1])
with title_col:
    st.markdown(
        f'<div class="page-title">{selected_group}</div>'
        f'<div class="page-sub">{page_sub}</div>',
        unsafe_allow_html=True,
    )
with week_col:
    st.markdown("<div style='height:1.1rem'></div>", unsafe_allow_html=True)
    st.markdown("<div class='week-select-wrap'>", unsafe_allow_html=True)
    selected_week_label = st.selectbox(
        "Week",
        options=_WEEK_OPTIONS,
        index=week_offset,
        label_visibility="collapsed",
        key="week_selector",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    new_offset = _WEEK_OPTIONS.index(selected_week_label)
    if new_offset != st.session_state.week_offset:
        st.session_state.week_offset = new_offset
        st.rerun()

week_offset = st.session_state.week_offset

# ── Per-creator render ────────────────────────────────────────────────────────
def render_creator(creator: dict, week_offset: int = 0, all_reports: dict = None) -> None:
    cid = str(creator.get("id", ""))
    cname = creator.get("name", "")

    # ── Fetch ─────────────────────────────────────────────────────────────────
    with st.spinner(""):
        tx_sum, ref_sum, raw_txns, trial_links, campaign_links, data_warning = get_creator_stats(cid, week_offset)

    if data_warning:
        st.warning(data_warning)

    gross   = tx_sum["total_gross"]
    net     = tx_sum["total_net"]
    tx_cnt  = tx_sum["count"]
    ref_cnt = ref_sum["count"]
    chargeback = (ref_sum["total_amount"] / gross * 100) if gross > 0 else 0.0

    # Sub stats from transactions
    new_sub_fans   = set(t["fanId"] for t in raw_txns if t.get("type") == "Subscription")
    renewal_txns   = [t for t in raw_txns if t.get("type") == "RecurringSubscription"]
    sub_revenue    = tx_sum["by_type"].get("Subscription", {}).get("net", 0) \
                   + tx_sum["by_type"].get("RecurringSubscription", {}).get("net", 0)

    # ── INFLOWW badge ─────────────────────────────────────────────────────────
    ws, we = week_range(week_offset)
    period_label = "This Week" if week_offset == 0 else ("Last Week" if week_offset == 1 else f"{week_offset} Weeks Ago")
    week_label = f"{ws[:10]} – {we[:10]}"
    st.markdown(f'<div class="badge-wrap"><span class="dot-purple"></span>Infloww · {period_label} &nbsp;<span style="color:#2a2a2a">{week_label}</span></div>', unsafe_allow_html=True)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    def kpi_card(label: str, value: str, accent: str = "#1e1e1e") -> str:
        return (
            f'<div style="background:#0a0a0a;border:1px solid #1a1a1a;border-top:2px solid {accent};'
            f'border-radius:16px;padding:1.1rem 1.4rem;flex:1;min-width:0">'
            f'<div style="color:#444;font-size:0.68rem;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.18em;margin-bottom:0.5rem;white-space:nowrap">{label}</div>'
            f'<div style="color:#fff;font-size:1.6rem;font-weight:900;font-family:Nunito;'
            f'letter-spacing:-0.01em;line-height:1">{value}</div>'
            f'</div>'
        )

    chargeback_accent = "#ff5252" if chargeback > 1 else "#1e1e1e"
    st.markdown(
        f'<div style="display:flex;gap:0.8rem;margin-bottom:1.5rem">'
        + kpi_card("Gross Revenue",   fmt_money(gross),          "#7c4dff")
        + kpi_card("Net Revenue",     fmt_money(net),            "#e040fb")
        + kpi_card("Transactions",    f"{tx_cnt:,}")
        + kpi_card("Refunds",         str(ref_cnt))
        + kpi_card("Refund Rate",     f"{chargeback:.2f}%",      chargeback_accent)
        + '</div>',
        unsafe_allow_html=True,
    )

    # ── Chatting Ratio ────────────────────────────────────────────────────────
    _sub_net  = tx_sum["by_type"].get("Subscription", {}).get("net", 0) \
              + tx_sum["by_type"].get("RecurringSubscription", {}).get("net", 0)
    _msg_net  = tx_sum["by_type"].get("Messages", {}).get("net", 0)
    _tips_net = tx_sum["by_type"].get("Tips", {}).get("net", 0)
    _chat_net = _msg_net + _tips_net

    if _sub_net > 0:
        _ratio = _chat_net / _sub_net
        ratio_display = f"1 : {_ratio:.1f}"
        if _ratio >= 5:
            ratio_color, ratio_label = "#69f0ae", "Excellent"
        elif _ratio >= 3:
            ratio_color, ratio_label = "#eeff41", "Good"
        elif _ratio >= 1:
            ratio_color, ratio_label = "#ffab40", "Average"
        else:
            ratio_color, ratio_label = "#ff5252", "Low"
    else:
        ratio_display = "N/A"
        ratio_color, ratio_label = "#333", "No sub data"

    _ratio_str = f"{_ratio:.1f}" if _sub_net > 0 else "—"
    st.markdown(
        f'''<div style="background:#0a0a0a;border:1px solid #1f1f1f;border-radius:20px;
                        padding:1.8rem 2rem;display:flex;align-items:center;
                        justify-content:space-between;margin-bottom:1.5rem;gap:2rem">
          <div style="flex:1">
            <div style="color:#444;font-size:0.65rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.2em;margin-bottom:0.8rem">Chatting Ratio</div>
            <div style="color:#fff;font-size:1rem;font-weight:600;line-height:1.6;margin-bottom:1rem">
              For every
              <span style="color:{ratio_color};font-weight:900">$1</span>
              in subscriptions, this creator earns
              <span style="color:{ratio_color};font-weight:900">${_ratio_str}</span>
              in messages &amp; tips
            </div>
            <div style="display:flex;gap:1.5rem">
              <div>
                <div style="color:#777;font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.15em;margin-bottom:2px">Messages + Tips</div>
                <div style="color:#fff;font-weight:700;font-size:0.95rem">{fmt_money(_chat_net)}</div>
              </div>
              <div style="color:#555;font-size:1.2rem;align-self:center">vs</div>
              <div>
                <div style="color:#777;font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.15em;margin-bottom:2px">Subscriptions</div>
                <div style="color:#fff;font-weight:700;font-size:0.95rem">{fmt_money(_sub_net)}</div>
              </div>
            </div>
          </div>
          <div style="text-align:center;flex-shrink:0;
                      background:#111;border:1px solid #1e1e1e;border-radius:16px;
                      padding:1.2rem 2rem">
            <div style="color:#777;font-size:0.62rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:.18em;margin-bottom:0.5rem">Ratio</div>
            <div style="color:#fff;font-size:2.8rem;font-weight:900;font-family:Nunito;
                        letter-spacing:-0.02em;line-height:1">1 : {_ratio_str}</div>
            <div style="color:{ratio_color};font-size:0.72rem;font-weight:700;
                        text-transform:uppercase;letter-spacing:0.15em;margin-top:0.5rem">{ratio_label}</div>
          </div>
        </div>''',
        unsafe_allow_html=True,
    )

    # Merge RecurringSubscription into Subscription for display
    merged_types: dict = {}
    for k, v in tx_sum["by_type"].items():
        display_key = "Subscription" if k == "RecurringSubscription" else k
        if display_key not in merged_types:
            merged_types[display_key] = {"gross": 0.0, "net": 0.0, "count": 0}
        merged_types[display_key]["gross"] += v["gross"]
        merged_types[display_key]["net"]   += v["net"]
        merged_types[display_key]["count"] += v["count"]

    TYPE_COLORS = {
        "Messages":     "#e040fb",
        "Tips":         "#00b0ff",
        "Subscription": "#69f0ae",
    }

    # ── Revenue Charts ────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-header">Revenue by Type</div>', unsafe_allow_html=True)
        if merged_types:
            type_rows = sorted(merged_types.items(), key=lambda x: x[1]["net"], reverse=True)
            labels = [k for k, _ in type_rows]
            nets   = [round(v["net"], 2) for _, v in type_rows]
            colors = [TYPE_COLORS.get(k, "#7c4dff") for k in labels]
            total_net_pie = sum(nets)
            fig = go.Figure(go.Pie(
                labels=labels,
                values=nets,
                hole=0.65,
                marker=dict(colors=colors, line=dict(color="#050505", width=3)),
                textinfo="none",
                hovertemplate="<b>%{label}</b><br>Net: $%{value:,.2f}<br>%{percent}<extra></extra>",
                sort=True,
            ))
            fig.update_layout(
                **{**PLOT_LAYOUT, "margin": dict(l=10, r=10, t=10, b=10)},
                showlegend=False,
                annotations=[dict(
                    text=f"<b>{fmt_money(net)}</b><br><span style='font-size:11px;color:#888'>NET</span>",
                    x=0.5, y=0.5,
                    font=dict(size=20, color="#fff", family="Nunito"),
                    showarrow=False,
                )],
                height=260,
            )
            st.plotly_chart(fig, width='stretch', key=f"pie_{cid}")

            # Custom legend
            legend_items = ""
            for label, net_val, color in zip(labels, nets, colors):
                pct = net_val / total_net_pie * 100 if total_net_pie > 0 else 0
                bar_width = f"{pct:.1f}%"
                legend_items += f"""
                <div style="padding:0.75rem 1.2rem;border-bottom:1px solid #0d0d0d">
                  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
                    <div style="display:flex;align-items:center;gap:8px">
                      <span style="width:10px;height:10px;border-radius:3px;background:{color};display:inline-block;flex-shrink:0"></span>
                      <span style="color:#999;font-size:0.72rem;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;font-family:Nunito">{label}</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:14px">
                      <span style="color:#fff;font-weight:900;font-size:1rem;font-family:Nunito">{fmt_money(net_val)}</span>
                      <span style="color:{color};font-size:0.85rem;font-weight:700;min-width:38px;text-align:right;font-family:Nunito">{pct:.1f}%</span>
                    </div>
                  </div>
                  <div style="height:3px;background:#111;border-radius:2px;overflow:hidden">
                    <div style="height:100%;width:{bar_width};background:{color};border-radius:2px"></div>
                  </div>
                </div>"""
            st.markdown(
                f'<div style="border:1px solid #111;border-radius:12px;overflow:hidden;margin-top:-0.5rem">'
                f'{legend_items}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="empty-state">No transactions this week</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="section-header">Daily Net Revenue</div>', unsafe_allow_html=True)
        if tx_sum["by_date"]:
            date_rows = sorted(tx_sum["by_date"].items())
            date_vals = pd.to_datetime([r[0] for r in date_rows])
            net_vals  = [round(r[1]["net"], 2) for r in date_rows]
            cnt_vals  = [r[1]["count"] for r in date_rows]
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=date_vals, y=net_vals,
                mode="lines+markers",
                line=dict(color="#7c4dff", width=2.5, shape="spline", smoothing=0.8),
                marker=dict(
                    color="#e040fb", size=8,
                    line=dict(color="#050505", width=2),
                ),
                fill="tozeroy",
                fillcolor="rgba(124,77,255,0.12)",
                customdata=cnt_vals,
                hovertemplate="<b>$%{y:,.2f}</b>  ·  %{customdata} txns<extra></extra>",
            ))
            fig2.update_layout(
                **{**PLOT_LAYOUT, "margin": dict(l=10, r=10, t=20, b=10)},
                hovermode="x",
                xaxis=dict(
                    gridcolor="#0d0d0d", zeroline=False,
                    tickfont=dict(color="#666", size=11), tickformat="%a %d",
                    showline=False,
                    showspikes=True,
                    spikemode="across",
                    spikecolor="#2a2a2a",
                    spikethickness=1,
                    spikedash="solid",
                    spikesnap="cursor",
                ),
                yaxis=dict(
                    gridcolor="#0d0d0d", zeroline=False,
                    tickfont=dict(color="#666", size=11),
                    tickprefix="$", tickformat=",.0f",
                    showline=False,
                    showspikes=False,
                ),
                hoverlabel=dict(
                    bgcolor="#0d0d0d",
                    bordercolor="#7c4dff",
                    font=dict(family="Nunito", size=14, color="#ffffff"),
                    align="left",
                    namelength=0,
                ),
            )
            st.plotly_chart(fig2, width='stretch', key=f"daily_{cid}")
        else:
            st.markdown('<div class="empty-state">No daily data</div>', unsafe_allow_html=True)

    # ── Subscriber Stats ──────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Subscriber Stats</div>', unsafe_allow_html=True)

    # Total subs from trial links
    total_trial_subs   = sum(int(l.get("subCount", 0) or 0) for l in trial_links)
    total_paying_fans  = sum(int(l.get("payingFansCount", 0) or 0) for l in trial_links)
    conversion_rate    = (total_paying_fans / total_trial_subs * 100) if total_trial_subs > 0 else 0.0

    st.markdown(
        f'<div style="display:flex;gap:0.8rem;margin-bottom:1.5rem">'
        + kpi_card("New Subs · Week",    str(len(new_sub_fans)),   "#69f0ae")
        + kpi_card("Renewals · Week",    str(len(renewal_txns)))
        + kpi_card("Sub Revenue · Week", fmt_money(sub_revenue),   "#00e5ff")
        + kpi_card("Total Trial Subs",   str(total_trial_subs))
        + kpi_card("Paying Fans",        f"{total_paying_fans} ({conversion_rate:.0f}%)", "#eeff41")
        + '</div>',
        unsafe_allow_html=True,
    )

    # ── Campaign Performance ──────────────────────────────────────────────────
    if campaign_links:
        st.markdown('<div class="section-header">Campaign Performance</div>', unsafe_allow_html=True)

        sorted_camp = sorted(campaign_links, key=lambda l: int(l.get("subCount", 0) or 0), reverse=True)
        rows_html = ""
        for camp in sorted_camp:
            msg       = (camp.get("message") or "—")[:60] + ("…" if len(camp.get("message") or "") > 60 else "")
            sub_cnt   = int(camp.get("subCount", 0) or 0)
            pay_cnt   = int(camp.get("payingFansCount", 0) or 0)
            earn_net  = cents(camp.get("earningsNet", 0))
            discount  = camp.get("discount", 0)
            c_type    = (camp.get("type") or "—").title()
            status    = "Expired" if camp.get("finishedFlag") else "Active"
            status_col = "#777" if status == "Expired" else "#4ade80"
            rows_html += (
                f"<tr>"
                f"<td style='color:#888;max-width:300px'>{msg}</td>"
                f"<td style='color:#aaa'>{c_type}</td>"
                f"<td style='color:#aaa'>{sub_cnt}</td>"
                f"<td style='color:#aaa'>{pay_cnt}</td>"
                f"<td class='amt'>${earn_net:,.2f}</td>"
                f"<td style='color:#888'>{discount}%</td>"
                f"<td style='color:{status_col};font-size:0.75rem;font-weight:700'>{status}</td>"
                f"</tr>"
            )
        st.markdown(
            '<div style="border:1px solid #111;border-radius:12px;overflow:hidden">'
            '<table class="dark-table"><thead><tr>'
            "<th>Message</th><th>Type</th><th>Subs</th><th>Paying</th>"
            "<th>Net Earnings</th><th>Discount</th><th>Status</th>"
            f"</tr></thead><tbody>{rows_html}</tbody></table></div>",
            unsafe_allow_html=True,
        )

    # ── Top Fans by Spending (LTV from transactions) ──────────────────────────
    if raw_txns:
        st.markdown('<div class="section-header">Top Spenders · This Week</div>', unsafe_allow_html=True)

        fan_map: dict = {}
        for tx in raw_txns:
            fid = tx.get("fanId", "")
            if fid not in fan_map:
                fan_map[fid] = {"name": tx.get("fanName", fid), "total": 0.0, "messages": 0.0, "sub": 0.0, "tips": 0.0}
            n = parse_amount(tx.get("net", 0))
            t = tx.get("type", "")
            fan_map[fid]["total"] += n
            if t == "Messages":
                fan_map[fid]["messages"] += n
            elif t in ("Subscription", "RecurringSubscription"):
                fan_map[fid]["sub"] += n
            elif t == "Tips":
                fan_map[fid]["tips"] += n

        top_fans = sorted(fan_map.items(), key=lambda x: x[1]["total"], reverse=True)[:15]
        notes = _load_notes()

        # Header
        st.markdown(
            '<div style="border:1px solid #111;border-radius:12px;overflow:hidden">'
            '<div style="display:grid;grid-template-columns:36px 1fr 100px 80px 80px 80px 80px;'
            'padding:0.6rem 1.2rem;border-bottom:1px solid #1a1a1a">'
            '<span style="color:#666;font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.15em">#</span>'
            '<span style="color:#666;font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.15em">Fan</span>'
            '<span style="color:#666;font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.15em;text-align:right">Total</span>'
            '<span style="color:#666;font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.15em;text-align:right">Msgs</span>'
            '<span style="color:#666;font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.15em;text-align:right">Sub</span>'
            '<span style="color:#666;font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.15em;text-align:right">Tips</span>'
            '<span style="color:#666;font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.15em;text-align:center">Notes</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        for i, (fid, fan) in enumerate(top_fans):
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"<span style='color:#666'>#{i+1}</span>"
            existing_note = notes.get(cid, {}).get(fid, "")
            note_icon = "📝" if existing_note else "·  ·  ·"
            note_color = "#7c4dff" if existing_note else "#444"
            border = "border-bottom:1px solid #0d0d0d;" if i < len(top_fans) - 1 else ""

            row_col, notes_col = st.columns([11, 1.2])
            with row_col:
                st.markdown(
                    f'<div style="display:grid;grid-template-columns:36px 1fr 100px 80px 80px 80px;'
                    f'padding:0.75rem 1.2rem;background:#050505;{border}align-items:center">'
                    f'<span style="font-size:0.85rem">{medal}</span>'
                    f'<span style="color:#fff;font-weight:700;font-size:0.9rem">{fan["name"]}</span>'
                    f'<span style="color:#fff;font-weight:700;text-align:right;font-variant-numeric:tabular-nums">${fan["total"]:,.2f}</span>'
                    f'<span style="color:#888;text-align:right;font-size:0.82rem;font-variant-numeric:tabular-nums">${fan["messages"]:,.2f}</span>'
                    f'<span style="color:#888;text-align:right;font-size:0.82rem;font-variant-numeric:tabular-nums">${fan["sub"]:,.2f}</span>'
                    f'<span style="color:#888;text-align:right;font-size:0.82rem;font-variant-numeric:tabular-nums">${fan["tips"]:,.2f}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with notes_col:
                with st.popover(note_icon, use_container_width=True):
                    st.markdown(f"**Notes for {fan['name']}**")
                    new_note = st.text_area(
                        "Note", value=existing_note, height=120,
                        placeholder="Dodaj beleška o ovom spenderu...",
                        key=f"note_ta_{cid}_{fid}",
                        label_visibility="collapsed",
                    )
                    if st.button("Sačuvaj", key=f"note_save_{cid}_{fid}", type="primary"):
                        _save_note(cid, fid, new_note)
                        st.success("Sačuvano!")
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Transaction Breakdown ─────────────────────────────────────────────────
    if merged_types:
        st.markdown('<div class="section-header">Transaction Breakdown</div>', unsafe_allow_html=True)
        rows_html = ""
        for tx_type, data in sorted(merged_types.items(), key=lambda x: x[1]["net"], reverse=True):
            dot_color = TYPE_COLORS.get(tx_type, "#555")
            rows_html += (
                f"<tr>"
                f"<td><span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:{dot_color};margin-right:8px'></span>{tx_type}</td>"
                f"<td class='amt'>${data['gross']:,.2f}</td>"
                f"<td class='amt'>${data['net']:,.2f}</td>"
                f"<td style='color:#888'>{data['count']}</td></tr>"
            )
        st.markdown(
            '<div style="border:1px solid #111;border-radius:12px;overflow:hidden">'
            '<table class="dark-table"><thead><tr>'
            "<th>Type</th><th>Gross</th><th>Net</th><th>Transactions</th>"
            f"</tr></thead><tbody>{rows_html}</tbody></table></div>",
            unsafe_allow_html=True,
        )

    # ── Google Sheets ─────────────────────────────────────────────────────────
    st.markdown("<hr style='border-color:#111;margin:2.5rem 0'>", unsafe_allow_html=True)
    st.markdown('<div class="badge-wrap"><span class="dot-green"></span>Custom Orders · Google Sheets</div>', unsafe_allow_html=True)

    matched = find_matching_sheet(cname, sheet_names)
    if not matched:
        st.markdown('<div class="empty-state">No pending custom orders</div>', unsafe_allow_html=True)
    else:
        with st.spinner(""):
            df = fetch_sheet_data(matched)

        if df.empty:
            st.markdown('<div class="empty-state">No pending custom orders</div>', unsafe_allow_html=True)
        else:
            total_orders   = len(df)
            total_revenue  = df["AMOUNT"].sum()
            total_fans     = df["Username"].nunique()
            avg_order      = df["AMOUNT"].mean() if total_orders > 0 else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Revenue",   f"${total_revenue:,.2f}")
            c2.metric("Unique Fans",     total_fans)
            c3.metric("Total Orders",    total_orders)
            c4.metric("Avg Order Value", f"${avg_order:,.2f}")

            st.markdown('<div class="section-header">Top Custom Fans</div>', unsafe_allow_html=True)
            top = (
                df.groupby("Username", dropna=False)["AMOUNT"]
                .sum().sort_values(ascending=False).head(10).reset_index()
            )
            top.columns = ["Username", "Total"]
            fig_bar = go.Figure(go.Bar(
                x=top["Username"], y=top["Total"],
                marker_color=[RAINBOW[i % len(RAINBOW)] for i in range(len(top))],
                text=[f"${v:,.0f}" for v in top["Total"]],
                textposition="outside", textfont=dict(color="#fff", size=11),
            ))
            fig_bar.update_layout(
                **PLOT_LAYOUT,
                xaxis=dict(tickangle=-30, gridcolor="#111", color="#444", tickfont=dict(color="#555")),
                yaxis=dict(gridcolor="#111", color="#444", tickfont=dict(color="#555")),
                showlegend=False,
            )
            st.plotly_chart(fig_bar, width='stretch', key=f"fans_{cid}")

            st.markdown('<div class="section-header">Pending Orders</div>', unsafe_allow_html=True)
            pending = df[~df["Delivered By Cuhvet"].apply(is_truthy) & ~df["Received"].apply(is_truthy)].copy()

            if pending.empty:
                st.markdown('<div class="empty-state">All orders delivered ✓</div>', unsafe_allow_html=True)
            else:
                pending["Date"] = pending["Date"].dt.strftime("%d/%m/%Y").fillna("")
                rows_html = ""
                for _, row in pending.iterrows():
                    paid_str = str(row["Paid"]).strip().upper()
                    badge = (
                        '<span class="badge badge-paid">PAID</span>'
                        if paid_str == "PAID"
                        else f'<span class="badge badge-unpaid">{row["Paid"] or "—"}</span>'
                    )
                    amt = f"${row['AMOUNT']:,.2f}" if isinstance(row["AMOUNT"], float) else str(row["AMOUNT"])
                    rows_html += (
                        f"<tr><td>{row['Fan Name']}</td>"
                        f"<td style='color:#555'>{row['Username']}</td>"
                        f"<td style='color:#555'>{row['Custom price']}</td>"
                        f"<td><span class='amt'>{amt}</span></td>"
                        f"<td style='color:#444'>{row['Date']}</td>"
                        f"<td>{badge}</td>"
                        f"<td style='color:#333'>{row['Notes']}</td></tr>"
                    )
                st.markdown(
                    '<div style="border:1px solid #111;border-radius:12px;overflow:hidden">'
                    '<table class="dark-table"><thead><tr>'
                    "<th>Fan Name</th><th>Username</th><th>Custom Price</th>"
                    "<th>Amount</th><th>Date</th><th>Paid</th><th>Notes</th>"
                    f"</tr></thead><tbody>{rows_html}</tbody></table></div>",
                    unsafe_allow_html=True,
                )

    # ── Weekly Reports ────────────────────────────────────────────────────────
    _base = get_base_name(cname).strip().lower()
    rep = (all_reports or {}).get(_base, {
        "chatters":  {"headline": "", "body": ""},
        "executive": {"headline": "", "body": ""},
    })
    chatters  = rep["chatters"]
    executive = rep["executive"]

    st.markdown("<hr style='border-color:#111;margin:2.5rem 0'>", unsafe_allow_html=True)
    st.markdown(
        '<div class="badge-wrap"><span class="dot-purple"></span>Weekly Reports</div>',
        unsafe_allow_html=True,
    )

    _edit_key = f"edit_report_{cid}"
    if _edit_key not in st.session_state:
        st.session_state[_edit_key] = False

    # ── View mode ────────────────────────────────────────────────────────────
    if not st.session_state[_edit_key]:
        def _report_card(title: str, headline: str, body: str, accent: str) -> None:
            headline_html = (
                f'<div style="color:#fff;font-size:1.15rem;font-weight:900;line-height:1.3;margin-bottom:1rem">{headline}</div>'
                if headline else
                f'<div style="color:#555;font-size:0.85rem;font-style:italic;margin-bottom:1rem">No report yet...</div>'
            )
            body_html = "".join(
                f'<p style="color:#aaa;font-size:0.9rem;line-height:1.7;margin:0 0 0.4rem">{line}</p>'
                for line in body.split("\n") if line.strip()
            ) if body else ""
            st.markdown(
                f'<div style="background:#0a0a0a;border:1px solid #1a1a1a;border-top:2px solid {accent};'
                f'border-radius:16px;padding:1.6rem 1.8rem;margin-bottom:1rem">'
                f'<div style="color:#555;font-size:0.62rem;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:0.2em;margin-bottom:0.8rem">{title}</div>'
                f'{headline_html}{body_html}'
                f'</div>',
                unsafe_allow_html=True,
            )

        _report_card("Chatters Report",  chatters["headline"], chatters["body"],  "#7c4dff")
        _report_card("Executive Report", executive["headline"], executive["body"], "#e040fb")

        st.markdown(
            f'<div style="display:flex;justify-content:flex-end;margin-top:0.5rem">',
            unsafe_allow_html=True,
        )
        if st.button("✏️ Edit Reports", key=f"edit_btn_{cid}"):
            st.session_state[_edit_key] = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Edit mode ────────────────────────────────────────────────────────────
    else:
        st.markdown(
            '<div style="background:#0a0a0a;border:1px solid #222;border-radius:16px;padding:1.6rem 1.8rem;margin-bottom:1rem">',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="color:#7c4dff;font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:0.2em;margin-bottom:1rem">Chatters Report</div>',
            unsafe_allow_html=True,
        )
        ch_hl = st.text_input("Headline", value=chatters["headline"], key=f"ch_hl_{cid}", placeholder="Short headline...")
        ch_bd = st.text_area("Body", value=chatters["body"], key=f"ch_bd_{cid}", placeholder="Detailed report text...", height=120)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            '<div style="background:#0a0a0a;border:1px solid #222;border-radius:16px;padding:1.6rem 1.8rem;margin-bottom:1rem">',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="color:#e040fb;font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:0.2em;margin-bottom:1rem">Executive Report</div>',
            unsafe_allow_html=True,
        )
        ex_hl = st.text_input("Headline", value=executive["headline"], key=f"ex_hl_{cid}", placeholder="Short headline...")
        ex_bd = st.text_area("Body", value=executive["body"], key=f"ex_bd_{cid}", placeholder="Detailed report text...", height=120)
        st.markdown("</div>", unsafe_allow_html=True)

        col_save, col_cancel = st.columns([1, 1])
        with col_save:
            if st.button("💾 Save", key=f"save_btn_{cid}", use_container_width=True):
                ok = save_report(_base, ch_hl, ch_bd, ex_hl, ex_bd)
                if ok:
                    st.session_state[_edit_key] = False
                    st.success("Saved!")
                    st.rerun()
                else:
                    st.error("Save failed — check logs.")
        with col_cancel:
            if st.button("Cancel", key=f"cancel_btn_{cid}", use_container_width=True):
                st.session_state[_edit_key] = False
                st.rerun()


# ── Main ──────────────────────────────────────────────────────────────────────
if len(members) == 1:
    render_creator(members[0], week_offset, all_reports)
else:
    tabs = st.tabs([tab_label(c.get("name", ""), selected_group) for c in members])
    for tab, creator in zip(tabs, members):
        with tab:
            render_creator(creator, week_offset, all_reports)
