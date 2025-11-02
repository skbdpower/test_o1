import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- 1. CONFIGURATION AND LIGHT THEME ---
st.set_page_config(page_title='Loan KPI & Prediction Dashboard', layout='wide')

# --- THEME COLORS ---
PRIMARY_COLOR = "#1d4ed8"     # Deep Indigo Blue
SECONDARY_COLOR = "#f8fafc"   # Light Gray Background
TEXT_COLOR = "#1f2937"        # Dark Gray Text
CARD_BG = "#ffffff"           # White Cards
SHADOW = "0 4px 12px rgba(0, 0, 0, 0.08)"  # Soft Shadow

# --- APPLY LIGHT THEME CSS ---
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {SECONDARY_COLOR};
        color: {TEXT_COLOR};
    }}

    /* Main title styling */
    h1 {{
        color: {PRIMARY_COLOR};
        font-weight: 800;
        text-shadow: none;
    }}

    h2, h3, h4 {{
        color: {TEXT_COLOR};
        font-weight: 700;
    }}

    /* KPI and Chart Card Containers */
    .shadow-card {{
        background-color: {CARD_BG};
        border-radius: 12px;
        padding: 1em;
        box-shadow: {SHADOW};
        border: 1px solid #e5e7eb;
        margin-bottom: 1em;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {CARD_BG};
        border-right: 1px solid #e5e7eb;
    }}

    /* Plot titles */
    .plotly .main-svg .infolayer .g-title {{
        fill: {TEXT_COLOR} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# --- 2. PAGE TITLE ---
st.markdown(f"<h1>Loan Disbursement & Risk Dashboard (Light Theme) 🌤️</h1>", unsafe_allow_html=True)

# --- 3. DATA LOADING ---
@st.cache_data
def load_data(file_name):
    try:
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
        df['Age_Group'] = pd.cut(df['Borrower_Age'], bins=bins, labels=labels, include_lowest=True)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

file_name = "loan_disburse_report_Oct_2025.xlsx"
df = load_data(file_name)
if df.empty:
    st.stop()

# --- 4. HELPER FUNCTION ---
def fullint(val):
    if pd.isnull(val) or val == 0:
        return "0"
    val = float(val)
    return "{:,}".format(int(val)) if val.is_integer() else "{:,.2f}".format(val)

# --- 5. KPI SECTION ---
kpi_values = [
    ("Total Loan Disbursed", fullint(df['Loan_Amount'].sum())),
    ("Number of Loans", fullint(len(df))),
    ("Avg Loan Amount", fullint(df['Loan_Amount'].mean())),
    ("Total Insurance", fullint(df['Insurance_Amount'].sum())),
    ("Outstanding Principal", fullint(df['Outstanding_Pr'].sum())),
    ("Total Due Principal", fullint(df['Due_Amount_Pr'].sum())),
]

st.markdown(f'<h3 style="color:{PRIMARY_COLOR};">Key Performance Indicators</h3>', unsafe_allow_html=True)
k_cols = st.columns(len(kpi_values))
for idx, (label, value) in enumerate(kpi_values):
    k_cols[idx].markdown(
        f"""
        <div class='shadow-card' style='text-align:center;'>
            <div style='font-size:1em; color:{TEXT_COLOR}; font-weight:600;'>{label}</div>
            <div style='font-size:1.8em; font-weight:700; color:{PRIMARY_COLOR}; margin-top:0.2em;'>{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- 6. PLOTTING HELPERS ---
def plot_base_config(fig):
    fig.update_layout(
        plot_bgcolor=CARD_BG,
        paper_bgcolor=CARD_BG,
        font_color=TEXT_COLOR,
        title_font_size=18,
        margin=dict(l=20, r=20, t=50, b=30),
        title_x=0.05,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#f1f5f9")
    return fig

def plot_bar(df_, x, y, title, color=PRIMARY_COLOR, n_top=None, show_labels=False):
    df_ = df_.sort_values(y, ascending=False).head(n_top) if n_top else df_
    fig = px.bar(df_, x=x, y=y, title=title, color_discrete_sequence=[color])
    if show_labels:
        fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
    fig = plot_base_config(fig)
    fig.update_layout(showlegend=False)
    return fig

def plot_pie(df_, names, values, title):
    fig = px.pie(df_, names=names, values=values, title=title,
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig = plot_base_config(fig)
    return fig

def plot_line(df_, x, y, title, color=PRIMARY_COLOR):
    fig = px.line(df_, x=x, y=y, title=title)
    fig.update_traces(line=dict(width=3, color=color))
    return plot_base_config(fig)

def display_card_plot(fig, col):
    with col:
        st.markdown("<div class='shadow-card'>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. DASHBOARD CHARTS ---
st.markdown(f"<h3 style='color:{PRIMARY_COLOR};'>Loan Disbursement Analysis</h3>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
display_card_plot(plot_bar(df.groupby('Frequency')['Loan_Amount'].sum().reset_index(),
                           "Frequency", "Loan_Amount", "Loan Amount by Frequency"), col1)
display_card_plot(plot_bar(df.groupby('Divisional_Office')['Outstanding_Pr'].sum().reset_index(),
                           "Divisional_Office", "Outstanding_Pr", "Outstanding Principal by Division", color="#ef4444"), col2)
display_card_plot(plot_bar(df.groupby('Divisional_Office')['Insurance_Amount'].sum().reset_index(),
                           "Divisional_Office", "Insurance_Amount", "Insurance by Division", color="#10b981"), col3)

col4, col5 = st.columns(2)
display_card_plot(plot_bar(df.groupby('Divisional_Office')['Loan_Amount'].sum().reset_index(),
                           "Divisional_Office", "Loan_Amount", "Total Loan Amount by Division", color="#f59e0b"), col4)
display_card_plot(plot_bar(df.groupby('Zone_Office')['Loan_Amount'].sum().reset_index(),
                           "Zone_Office", "Loan_Amount", "Top 10 Zone Offices", color="#8b5cf6", n_top=10), col5)

col6, col7 = st.columns(2)
display_card_plot(plot_pie(df.groupby('Gender')['Loan_Amount'].sum().reset_index(),
                           'Gender', 'Loan_Amount', 'Loan Amount by Gender'), col6)
admit_count = df.groupby(df['Admission_Date'].dt.to_period('M')).agg({'BorrowerCode': 'nunique'}).reset_index()
admit_count['Admission_Date'] = admit_count['Admission_Date'].astype(str)
display_card_plot(plot_line(admit_count, "Admission_Date", "BorrowerCode", "New Borrowers Over Time", color="#059669"), col7)

col8, col9 = st.columns(2)
disburse_sum = df.groupby(df['Disbursment_Date'].dt.to_period('D'))['Loan_Amount'].sum().reset_index()
disburse_sum['Disbursment_Date'] = disburse_sum['Disbursment_Date'].astype(str)
display_card_plot(plot_line(disburse_sum, "Disbursment_Date", "Loan_Amount", "Daily Loan Disbursement"), col8)
display_card_plot(plot_bar(df.groupby('Age_Group')['Loan_Amount'].mean().reset_index(),
                           'Age_Group', 'Loan_Amount', "Avg Loan Amount by Age Group", color="#f97316"), col9)

# --- 8. PREDICTION SECTION ---
st.markdown(f"<h3 style='color:{PRIMARY_COLOR};'>Next Month Loan Disbursement Prediction 🔮</h3>", unsafe_allow_html=True)

oct_loan_amount = df['Loan_Amount'].sum()
min_date = df['Disbursment_Date'].min()
max_date = df['Disbursment_Date'].max()
disbursing_days = (max_date - min_date).days + 1 if pd.notna(min_date) and pd.notna(max_date) else 27
avg_daily_disbursement = oct_loan_amount / disbursing_days
predicted_nov_amount = avg_daily_disbursement * 30
change = 'increase' if predicted_nov_amount > oct_loan_amount else 'decrease'
change_color = '#059669' if predicted_nov_amount > oct_loan_amount else '#ef4444'

col_pred1, col_pred2 = st.columns([1, 2])
with col_pred1:
    st.markdown(
        f"""
        <div class='shadow-card' style='text-align:center;'>
            <h4 style='color:{PRIMARY_COLOR};'>Predicted Change:</h4>
            <div style='font-size:2em; font-weight:800; color:{change_color}; text-transform:uppercase;'>
                {change}
            </div>
            <p style='color:{TEXT_COLOR};'>Predicted November value based on average October daily disbursement.</p>
        </div>
        """, unsafe_allow_html=True
    )

with col_pred2:
    st.markdown(
        f"""
        <div class='shadow-card'>
            <h4 style='color:{PRIMARY_COLOR};'>Prediction Details:</h4>
            <ul style='list-style:none; padding-left:0; font-size:1.05em;'>
                <li><strong>Total Loan (Oct 2025):</strong> <span style='float:right;'>{fullint(oct_loan_amount)}</span></li>
                <li><strong>Disbursing Days:</strong> <span style='float:right;'>{disbursing_days}</span></li>
                <li><strong>Avg Daily Disbursement:</strong> <span style='float:right;'>{fullint(avg_daily_disbursement)}</span></li>
                <li style='border-top:1px solid #e5e7eb; padding-top:5px;'><strong>Predicted Nov Total (30 days):</strong> 
                    <span style='float:right; color:{PRIMARY_COLOR}; font-weight:700;'>{fullint(predicted_nov_amount)}</span>
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True
    )

st.markdown("<div style='text-align:center; color:#9ca3af; padding-top:2em;'>Dashboard Complete — Light Theme ☀️</div>", unsafe_allow_html=True)
