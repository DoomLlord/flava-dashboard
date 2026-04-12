import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_fetcher import get_sheet_names, fetch_sheet_data

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Flava Management",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={},
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;900&display=swap');

* { font-family: 'Nunito', sans-serif; }

/* ── Reset & base ── */
.stApp { background-color: #000000; color: #ffffff; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0c0c0c;
    border-right: 1px solid #1c1c1c;
    min-width: 210px !important;
    max-width: 210px !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
    display: flex;
    flex-direction: column;
    height: 100vh;
}
[data-testid="stSidebar"] .block-container { padding: 0 !important; }
[data-testid="stSidebarContent"] { padding: 0 !important; }

/* ── Brand / Logo ── */
.brand-wrap {
    padding: 1.8rem 1.4rem 1.6rem;
    border-bottom: 1px solid #1c1c1c;
    margin-bottom: 0.4rem;
}
.brand-logo {
    font-family: 'Nunito', sans-serif;
    font-size: 2.6rem;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -0.02em;
    line-height: 1;
}

/* ── Ukloni default margin oko elemenata u sidebaru ── */
[data-testid="stSidebar"] .stButton { margin: 0 !important; padding: 0 !important; }
[data-testid="stSidebar"] [data-testid="element-container"] { margin: 0 !important; padding: 0 !important; }
[data-testid="stSidebar"] .stElementContainer { margin: 0 !important; padding: 0 !important; }
[data-testid="stSidebar"] .stVerticalBlock { gap: 0 !important; }

/* ── Nav section label ── */
.nav-section-label {
    font-size: 0.58rem; color: #2a2a2a; letter-spacing: 0.25em;
    text-transform: uppercase; padding: 1rem 1.4rem 0.5rem;
    font-weight: 700;
}

/* ── Nav dugmici ── */
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background: transparent !important;
    color: #666 !important;
    border: none !important;
    border-left: 3px solid transparent !important;
    border-radius: 0 !important;
    padding: 0.7rem 1.4rem !important;
    text-align: left !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    font-family: 'Nunito', sans-serif !important;
    letter-spacing: 0.01em !important;
    transition: background 0.12s ease, color 0.12s ease !important;
    box-shadow: none !important;
    line-height: 1.4 !important;
    min-height: 2.6rem !important;
    height: auto !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #161616 !important;
    color: #ccc !important;
    border-left: 3px solid #333 !important;
}
[data-testid="stSidebar"] .nav-active .stButton > button {
    background: #222 !important;
    color: #ffffff !important;
    border-left: 3px solid #ffffff !important;
    font-weight: 900 !important;
}

/* ── Refresh button ── */
[data-testid="stSidebar"] .refresh-wrap .stButton > button {
    color: #2e2e2e !important;
    border: 1px solid #1e1e1e !important;
    border-left: 1px solid #1e1e1e !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    font-size: 0.72rem !important;
    text-align: center !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    margin: 0 1.2rem !important;
    width: calc(100% - 2.4rem) !important;
}
[data-testid="stSidebar"] .refresh-wrap .stButton > button:hover {
    background: #161616 !important;
    color: #aaa !important;
    border-color: #333 !important;
    border-left-color: #333 !important;
}
.refresh-wrap { padding: 0.8rem 0 1.2rem; border-top: 1px solid #1c1c1c; }

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: #0a0a0a;
    border: 1px solid #1a1a1a;
    border-radius: 16px;
    padding: 1.2rem 1.6rem;
}
[data-testid="stMetricLabel"] {
    color: #444 !important; font-size: 0.72rem !important;
    text-transform: uppercase; letter-spacing: 0.12em;
}
[data-testid="stMetricValue"] {
    color: #ffffff !important; font-size: 2rem !important; font-weight: 700;
}

/* ── Section headers ── */
.section-header {
    font-size: 0.68rem; font-weight: 700; color: #444;
    text-transform: uppercase; letter-spacing: 0.2em;
    margin: 2.2rem 0 1.2rem; display: flex; align-items: center; gap: 0.8rem;
}
.section-header::after {
    content: ''; flex: 1; height: 1px; background: #1a1a1a;
}

/* ── Table ── */
.dark-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.dark-table th {
    color: #333; text-transform: uppercase; font-size: 0.65rem;
    letter-spacing: 0.15em; padding: 0.9rem 1.2rem;
    border-bottom: 1px solid #1a1a1a; text-align: left; font-weight: 600;
}
.dark-table td {
    padding: 0.85rem 1.2rem; border-bottom: 1px solid #0d0d0d;
    color: #ccc; background: #050505;
}
.dark-table tr:hover td { background: #0f0f0f; color: #fff; }
.dark-table tr:last-child td { border-bottom: none; }
.amt { color: #fff; font-weight: 600; font-variant-numeric: tabular-nums; }
.badge {
    border-radius: 6px; padding: 3px 10px;
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em;
}
.badge-paid   { background: #0d1f0d; color: #4ade80; border: 1px solid #1a3a1a; }
.badge-unpaid { background: #1f0d0d; color: #888;    border: 1px solid #3a1a1a; }

/* ── Empty state ── */
.empty-state {
    color: #333; padding: 2.5rem; background: #050505;
    border: 1px solid #111; border-radius: 12px;
    text-align: center; font-size: 0.85rem; letter-spacing: 0.05em;
}

/* ── Page title ── */
.page-title {
    font-size: 1.8rem; font-weight: 900; color: #fff;
    letter-spacing: 0.01em; margin-bottom: 0.2rem;
    font-family: 'Nunito', sans-serif;
}
.page-sub { font-size: 0.78rem; color: #333; margin-bottom: 1.8rem; }

hr { border-color: #1a1a1a; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Loading spinner ── */
[data-testid="stSpinner"] {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 4rem 0 !important;
}
[data-testid="stSpinner"] > div {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.2rem;
}
[data-testid="stSpinner"] svg {
    width: 2rem !important;
    height: 2rem !important;
    stroke: #ffffff !important;
    opacity: 0.6;
}
[data-testid="stSpinner"] p {
    display: none !important;
}

/* ── Sakrij dugmad za collapse/expand sidebar ── */
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="collapsedControl"]        { display: none !important; }

/* ── Forsiraj sidebar da uvek bude vidljiv ── */
[data-testid="stSidebar"] {
    transform: none !important;
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    min-width: 200px !important;
    max-width: 220px !important;
}
</style>
""", unsafe_allow_html=True)

# ── JS: forsiraj sidebar da uvek bude otvoren ────────────────────────────────
st.markdown("""
<script>
(function() {
    // Obrisi cached stanje sidebara iz localStorage
    const keys = Object.keys(window.localStorage);
    keys.forEach(k => {
        if (k.includes('sidebar') || k.includes('Sidebar')) {
            window.localStorage.removeItem(k);
        }
    });
    // Forsiraj expanded klikom na collapse dugme ako je zatvoreno
    function expandSidebar() {
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        const collapsed = document.querySelector('[data-testid="collapsedControl"]');
        if (collapsed) collapsed.click();
    }
    setTimeout(expandSidebar, 300);
})();
</script>
""", unsafe_allow_html=True)

# ── Rainbow color palette for charts ─────────────────────────────────────────
RAINBOW = [
    "#e040fb", "#7c4dff", "#448aff", "#00b0ff",
    "#00e5ff", "#69f0ae", "#eeff41", "#ffab40", "#ff5252",
]

PLOT_LAYOUT = dict(
    paper_bgcolor="#050505",
    plot_bgcolor="#050505",
    font_color="#888",
    margin=dict(l=10, r=10, t=30, b=10),
)

# ── Session state for selected sheet ─────────────────────────────────────────
if "selected_sheet" not in st.session_state:
    st.session_state.selected_sheet = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="brand-wrap">'
        '<div class="brand-logo">cuhvet</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    sheet_names = get_sheet_names()

    if not sheet_names:
        st.warning("No sheets found.")
        st.stop()

    if st.session_state.selected_sheet not in sheet_names:
        st.session_state.selected_sheet = sheet_names[0]

    for name in sheet_names:
        is_active = name == st.session_state.selected_sheet
        wrap_class = "nav-active" if is_active else ""
        st.markdown(f'<div class="{wrap_class}">', unsafe_allow_html=True)
        if st.button(name, key=f"nav_{name}"):
            st.session_state.selected_sheet = name
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
    st.markdown('<div class="refresh-wrap">', unsafe_allow_html=True)
    if st.button("↺  Refresh Data", key="refresh"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
selected_sheet = st.session_state.selected_sheet
with st.spinner(""):
    df = fetch_sheet_data(selected_sheet)

# ── Page header ───────────────────────────────────────────────────────────────
total_orders = len(df)
st.markdown(
    f'<div class="page-title">{selected_sheet}</div>'
    f'<div class="page-sub">{total_orders} orders</div>',
    unsafe_allow_html=True,
)

if df.empty:
    st.markdown('<div class="empty-state">No data in this sheet.</div>', unsafe_allow_html=True)
    st.stop()

# ── KPI metrics ───────────────────────────────────────────────────────────────
total_revenue = df["AMOUNT"].sum()
total_fans = df["Username"].nunique()
avg_order = df["AMOUNT"].mean() if total_orders > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${total_revenue:,.2f}")
col2.metric("Unique Fans", total_fans)
col3.metric("Total Orders", total_orders)
col4.metric("Avg Order Value", f"${avg_order:,.2f}")

# ── Top Custom Fans chart ─────────────────────────────────────────────────────
st.markdown('<div class="section-header">Top Custom Fans</div>', unsafe_allow_html=True)

top_fans = (
    df.groupby("Username", dropna=False)["AMOUNT"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)
top_fans.columns = ["Username", "Total"]

# Assign rainbow colors per bar
bar_colors = [RAINBOW[i % len(RAINBOW)] for i in range(len(top_fans))]

fig_bar = go.Figure(go.Bar(
    x=top_fans["Username"],
    y=top_fans["Total"],
    marker_color=bar_colors,
    text=[f"${v:,.0f}" for v in top_fans["Total"]],
    textposition="outside",
    textfont=dict(color="#fff", size=11),
))
fig_bar.update_layout(
    **PLOT_LAYOUT,
    xaxis=dict(tickangle=-30, gridcolor="#111", color="#444", tickfont=dict(color="#555")),
    yaxis=dict(gridcolor="#111", color="#444", tickfont=dict(color="#555")),
    showlegend=False,
)
st.plotly_chart(fig_bar, use_container_width=True)

# ── Pending Orders ────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Pending Orders</div>', unsafe_allow_html=True)


def is_truthy(val):
    return str(val).strip().upper() in ("TRUE", "1", "YES")


pending = df[
    ~df["Delivered By Cuhvet"].apply(is_truthy) & ~df["Received"].apply(is_truthy)
].copy()

if pending.empty:
    st.markdown('<div class="empty-state">All orders delivered ✓</div>', unsafe_allow_html=True)
else:
    pending["Date"] = pending["Date"].dt.strftime("%d/%m/%Y").fillna("")

    rows_html = ""
    for _, row in pending.iterrows():
        paid_str = str(row["Paid"]).strip().upper()
        badge = (
            f'<span class="badge badge-paid">PAID</span>'
            if paid_str == "PAID"
            else f'<span class="badge badge-unpaid">{row["Paid"] or "—"}</span>'
        )
        amt = f"${row['AMOUNT']:,.2f}" if isinstance(row["AMOUNT"], float) else str(row["AMOUNT"])
        rows_html += (
            f"<tr>"
            f"<td>{row['Fan Name']}</td>"
            f"<td style='color:#555'>{row['Username']}</td>"
            f"<td style='color:#555'>{row['Custom price']}</td>"
            f"<td><span class='amt'>{amt}</span></td>"
            f"<td style='color:#444'>{row['Date']}</td>"
            f"<td>{badge}</td>"
            f"<td style='color:#333'>{row['Notes']}</td>"
            f"</tr>"
        )

    st.markdown(
        '<div style="border:1px solid #111;border-radius:12px;overflow:hidden">'
        '<table class="dark-table"><thead><tr>'
        "<th>Fan Name</th><th>Username</th><th>Custom Price</th>"
        "<th>Amount</th><th>Date</th><th>Paid</th><th>Notes</th>"
        f"</tr></thead><tbody>{rows_html}</tbody></table></div>",
        unsafe_allow_html=True,
    )
