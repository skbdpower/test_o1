import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title='Loan KPI & Prediction Dashboard',
    layout='wide',
    initial_sidebar_state='expanded'
)

# --- LIGHT THEME COLORS ---
PRIMARY_COLOR = "#1d4ed8"        # Indigo blue
BACKGROUND_COLOR = "#f9fafb"     # Light gray background
CARD_BG = "#ffffff"              # White card background
TEXT_COLOR = "#111827"           # Dark text (almost black)
BORDER_COLOR = "#e5e7eb"         # Light gray border
SHADOW = "0 4px 12px rgba(0, 0, 0, 0.08)"


# --- CUSTOM CSS OVERRIDES ---
st.markdown(
    f"""
    <style>
    /* Global background and text */
    .stApp {{
        background-color: {BACKGROUND_COLOR};
        color: {TEXT_COLOR};
    }}

    h1, h2, h3, h4, h5, h6, p, span, div {{
        color: {TEXT_COLOR} !important;
        text-shadow: none !important;
    }}

    /* Main title */
    h1 {{
        color: {PRIMARY_COLOR} !important;
        font-weight: 800 !important;
    }}

    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background-color: {CARD_BG} !important;
        border-right: 1px solid {BORDER_COLOR};
    }}
    section[data-testid="stSidebar"] * {{
        color: {TEXT_COLOR} !important;
    }}

    /* Shadow card container */
    .shadow-card {{
        background-color: {CARD_BG};
        border-radius: 14px;
        padding: 1.2em;
        box-shadow: {SHADOW};
        border: 1px solid {BORDER_COLOR};
        color: {TEXT_COLOR};
        margin-bottom: 1.2em;
    }}

    /* Buttons */
    div.stButton > button {{
        background-color: {PRIMARY_COLOR};
        color: white !important;
        border-radius: 8px;
        border: none;
        padding: 0.5em 1em;
        font-weight: 600;
        transition: 0.2s ease;
    }}
    div.stButton > button:hover {{
        background-color: #2563eb;
        color: white !important;
    }}

    /* Metrics */
    [data-testid="stMetricValue"],
    [data-testid="stMetricLabel"] {{
        color: {TEXT_COLOR} !important;
    }}

    /* Inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div {{
        color: {TEXT_COLOR} !important;
    }}

    /* Tables */
    table, th, td {{
        color: {TEXT_COLOR} !important;
        background-color: {CARD_BG} !important;
    }}

    /* Plotly text override */
    .plotly .main-svg,
    .plotly text,
    g.xtick text, g.ytick text, .g-title, .g-legend text {{
        fill: {TEXT_COLOR} !important;
        color: {TEXT_COLOR} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)


# --- SIDEBAR FILTERS ---
st.sidebar.title("⚙️ Dashboard Controls")
region = st.sidebar.selectbox("Select Region", ["All", "North", "South", "East", "West"])
month = st.sidebar.selectbox("Select Month", ["January", "February", "March", "April", "May"])
st.sidebar.button("Apply Filters")


# --- MAIN PAGE TITLE ---
st.title("📊 Loan KPI & Prediction Dashboard")


# --- KPI SECTION ---
st.markdown("<div class='shadow-card'>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Loans", value="12,450")
with col2:
    st.metric(label="Active Clients", value="8,760")
with col3:
    st.metric(label="Portfolio (BDT)", value="৳ 3.4B")
st.markdown("</div>", unsafe_allow_html=True)


# --- SAMPLE DATA FOR CHARTS ---
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
disbursement = np.random.randint(100, 400, size=len(months))
repayment = np.random.randint(80, 350, size=len(months))
par = np.random.uniform(1.2, 4.5, size=len(months))

df = pd.DataFrame({
    "Month": months,
    "Loan Disbursement": disbursement,
    "Loan Repayment": repayment,
    "PAR (%)": par
})


# --- PORTFOLIO OVERVIEW CHART ---
st.markdown("<div class='shadow-card'>", unsafe_allow_html=True)
st.subheader("📈 Portfolio Overview")

fig = go.Figure()
fig.add_trace(go.Bar(
    x=df["Month"],
    y=df["Loan Disbursement"],
    name="Disbursement",
    marker_color=PRIMARY_COLOR
))
fig.add_trace(go.Bar(
    x=df["Month"],
    y=df["Loan Repayment"],
    name="Repayment",
    marker_color="#10b981"
))
fig.update_layout(
    barmode='group',
    title="Monthly Loan Disbursement vs Repayment",
    plot_bgcolor=BACKGROUND_COLOR,
    paper_bgcolor=CARD_BG,
    font=dict(color=TEXT_COLOR),
    legend=dict(
        bgcolor=CARD_BG,
        bordercolor=BORDER_COLOR,
        borderwidth=1
    ),
    margin=dict(t=60, b=40)
)
st.plotly_chart(fig, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)


# --- PAR TREND CHART ---
st.markdown("<div class='shadow-card'>", unsafe_allow_html=True)
st.subheader("📉 Portfolio at Risk (PAR) Trend")

fig_par = go.Figure()
fig_par.add_trace(go.Scatter(
    x=df["Month"],
    y=df["PAR (%)"],
    mode='lines+markers',
    name='PAR %',
    line=dict(color="#ef4444", width=3)
))
fig_par.update_layout(
    title="Monthly PAR Trend",
    plot_bgcolor=BACKGROUND_COLOR,
    paper_bgcolor=CARD_BG,
    font=dict(color=TEXT_COLOR),
    yaxis=dict(title="PAR (%)"),
    legend=dict(
        bgcolor=CARD_BG,
        bordercolor=BORDER_COLOR,
        borderwidth=1
    ),
    margin=dict(t=60, b=40)
)
st.plotly_chart(fig_par, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)


# --- DATA TABLE ---
st.markdown("<div class='shadow-card'>", unsafe_allow_html=True)
st.subheader("📋 Detailed Data View")
st.dataframe(df.style.format({"PAR (%)": "{:.2f}"}))
st.markdown("</div>", unsafe_allow_html=True)
