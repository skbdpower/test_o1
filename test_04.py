import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- 1. CONFIGURATION AND THEME ---
st.set_page_config(
    page_title="Loan KPI & Prediction Dashboard",
    layout="wide",
    page_icon="📊",
)

# === THEME COLORS ===
PRIMARY_COLOR = "#0284c7"           # Modern blue-teal
SECONDARY_COLOR = "#0d9488"         # Greenish accent
BACKGROUND_COLOR = "#f8fafc"        # Light background
CARD_BACKGROUND = "#ffffff"
TEXT_COLOR = "#1e293b"              # Dark slate text
SUBTEXT_COLOR = "#475569"           # Muted gray text

# --- 2. CUSTOM CSS FOR GLOBAL STYLING ---
st.markdown(f"""
<style>
/* Global background and text */
html, body, [class*="css"] {{
    color: {TEXT_COLOR};
    background-color: {BACKGROUND_COLOR};
    font-family: "Inter", sans-serif;
}}

/* Headings */
h1, h2, h3, h4, h5 {{
    color: {PRIMARY_COLOR};
    font-weight: 700;
}}

/* KPI Cards */
.kpi-card {{
    background: linear-gradient(135deg, {CARD_BACKGROUND} 60%, #e0f2fe 100%);
    border-radius: 14px;
    padding: 1.2em;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    border-left: 6px solid {PRIMARY_COLOR};
    text-align: center;
}}
.kpi-label {{
    color: {SUBTEXT_COLOR};
    font-weight: 600;
    font-size: 1em;
}}
.kpi-value {{
    color: {SECONDARY_COLOR};
    font-weight: 800;
    font-size: 1.8em;
    letter-spacing: 0.03em;
}}

/* Chart Cards */
.chart-card {{
    background-color: {CARD_BACKGROUND};
    border-radius: 14px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    padding: 1em;
    margin-bottom: 20px;
}}

/* Section Titles */
.section-title {{
    color: {PRIMARY_COLOR};
    font-size: 1.4em;
    font-weight: 700;
    margin-top: 30px;
    margin-bottom: 10px;
}}

/* Prediction Cards */
.pred-card {{
    background-color: {CARD_BACKGROUND};
    border-radius: 14px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    padding: 1.5em;
}}
</style>
""", unsafe_allow_html=True)

# --- 3. TITLE ---
st.markdown(f"<h1>💠 Loan Disbursement & Risk Dashboard</h1>", unsafe_allow_html=True)
st.write("Modern visual analytics with clean theme and prediction insights.")

# --- 4. DATA LOADING ---
@st.cache_data
def load_data(file_name):
    df = pd.read_excel(file_name)
    df.columns = df.columns.str.strip()

    df['Disbursment_Date'] = pd.to_datetime(df['Disbursment_Date'], errors='coerce')
    df['Admission_Date'] = pd.to_datetime(df['Admission_Date'], errors='coerce')

    df.rename(columns={'Cycle': 'Loan_Cycle', 'Loan Amount': 'Loan_Amount', 'Age': 'Borrower_Age'}, inplace=True)
    numeric_cols = ['Loan_Amount', 'Insurance_Amount', 'Outstanding_Pr', 'Due_Amount_Pr', 'Borrower_Age']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    bins = [18, 25, 35, 45, 55, 100]
    labels = ['18-25', '26-35', '36-45', '46-55', '56+']
    df['Age_Group'] = pd.cut(df['Borrower_Age'], bins=bins, labels=labels, right=True, include_lowest=True)
    return df

file_name = "loan_disburse_report_Oct_2025.xlsx"
df = load_data(file_name)
if df.empty:
    st.error("Error loading data.")
    st.stop()

# --- 5. UTILITIES ---
def fullint(val):
    if pd.isnull(val) or val == 0:
        return "0"
    val = float(val)
    return "{:,}".format(int(val)) if val.is_integer() else "{:,.2f}".format(val)

# --- 6. KPI SECTION ---
st.markdown(f"<div class='section-title'>Key Performance Indicators</div>", unsafe_allow_html=True)

kpi_values = [
    ("Total Loan Disbursed", fullint(df['Loan_Amount'].sum())),
    ("Number of Loans", fullint(len(df))),
    ("Avg Loan Amount", fullint(df['Loan_Amount'].mean())),
    ("Total Insurance", fullint(df['Insurance_Amount'].sum())),
    ("Outstanding Principal", fullint(df['Outstanding_Pr'].sum())),
    ("Total Due Principal", fullint(df['Due_Amount_Pr'].sum())),
]

cols = st.columns(len(kpi_values))
for i, (label, value) in enumerate(kpi_values):
    cols[i].markdown(
        f"<div class='kpi-card'>"
        f"<div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value'>{value}</div>"
        f"</div>", unsafe_allow_html=True
    )

# --- 7. COMMON PLOT STYLING ---
def plot_base(fig):
    fig.update_layout(
        plot_bgcolor=CARD_BACKGROUND,
        paper_bgcolor=CARD_BACKGROUND,
        font=dict(family="Inter", color=TEXT_COLOR),
        title_font=dict(size=18, color=PRIMARY_COLOR),
        margin=dict(l=20, r=20, t=50, b=30),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e2e8f0")
    return fig

def card_plot(fig, col):
    with col:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

# --- 8. VISUALS ---
st.markdown(f"<div class='section-title'>Loan Disbursement Analysis</div>", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

# 1. Loan by Frequency
freq_sum = df.groupby('Frequency')['Loan_Amount'].sum().reset_index()
fig1 = px.bar(freq_sum, x='Frequency', y='Loan_Amount', color_discrete_sequence=[PRIMARY_COLOR], title="Loan by Frequency")
card_plot(plot_base(fig1), c1)

# 2. Outstanding by Division
div_out = df.groupby('Divisional_Office')['Outstanding_Pr'].sum().reset_index()
fig2 = px.bar(div_out, x='Divisional_Office', y='Outstanding_Pr', color_discrete_sequence=[SECONDARY_COLOR], title="Outstanding by Division")
card_plot(plot_base(fig2), c2)

# 3. Insurance by Division
div_ins = df.groupby('Divisional_Office')['Insurance_Amount'].sum().reset_index()
fig3 = px.bar(div_ins, x='Divisional_Office', y='Insurance_Amount', color_discrete_sequence=["#f59e0b"], title="Insurance by Division")
card_plot(plot_base(fig3), c3)

# --- 9. PREDICTION ---
st.markdown(f"<div class='section-title'>📈 Next Month Loan Prediction</div>", unsafe_allow_html=True)

oct_loan_amount = df['Loan_Amount'].sum()
min_date, max_date = df['Disbursment_Date'].min(), df['Disbursment_Date'].max()
disbursing_days = (max_date - min_date).days + 1 if pd.notna(min_date) and pd.notna(max_date) else 27
avg_daily = oct_loan_amount / disbursing_days
pred_nov = avg_daily * 30
change = "increase" if pred_nov > oct_loan_amount else "decrease"
color = "#16a34a" if change == "increase" else "#dc2626"

p1, p2 = st.columns([1, 2])
with p1:
    st.markdown(f"""
    <div class='pred-card'>
        <h4 style='color:{PRIMARY_COLOR};'>Predicted Change</h4>
        <div style='text-align:center; font-size:2.2em; font-weight:800; color:{color};'>{change.upper()}</div>
        <p style='text-align:center; color:{SUBTEXT_COLOR};'>(Based on Oct daily avg x 30 days)</p>
    </div>
    """, unsafe_allow_html=True)

with p2:
    st.markdown(f"""
    <div class='pred-card'>
        <h4 style='color:{PRIMARY_COLOR};'>Prediction Details</h4>
        <ul style='list-style:none; padding-left:0; font-size:1.1em; color:{TEXT_COLOR};'>
            <li><b>Total Loan (Oct):</b> <span style='float:right;'>${fullint(oct_loan_amount)}</span></li>
            <li><b>Active Days:</b> <span style='float:right;'>{disbursing_days}</span></li>
            <li><b>Avg Daily:</b> <span style='float:right;'>${fullint(avg_daily)}</span></li>
            <li style='border-top:1px solid #e2e8f0; margin-top:0.5em; padding-top:0.5em;'><b>Predicted (Nov):</b> <span style='float:right; color:{PRIMARY_COLOR}; font-weight:700;'>${fullint(pred_nov)}</span></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='text-align:center; color:#94a3b8; margin-top:30px;'>Dashboard theme updated successfully ✅</div>", unsafe_allow_html=True)
