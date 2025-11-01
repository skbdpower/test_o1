import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- 1. CONFIGURATION AND STYLING (WITH CUSTOM CSS FIX) ---
st.set_page_config(page_title='Shadowed Loan KPI & Prediction Dashboard', layout='wide')
PRIMARY_COLOR = "#2563eb" # Primary theme color
SECONDARY_TEXT_COLOR = "#4a4a4a" # Darker gray for general text

# FIX: Inject custom CSS to ensure proper text colors and background
st.markdown(
    """
    <style>
    /* Change the color of all default markdown text */
    div.stText p {
        color: """ + SECONDARY_TEXT_COLOR + """;
    }

    /* Change the color of unstyled h2/h3/h4 in markdown, typically used by Plotly titles in Streamlit */
    h2, h3, h4 {
        color: """ + SECONDARY_TEXT_COLOR + """; 
    }
    
    /* Ensure the main title is always visible and colored */
    h1 {
        color: """ + PRIMARY_COLOR + """;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Ensure all plot titles (set via Plotly) are clearly visible */
    .plot-container .plotly .js-plotly-plot .main-svg .infolayer .g-title {
        color: """ + SECONDARY_TEXT_COLOR + """ !important;
    }

    /* Target the text color inside shadowed containers if needed (general text fallback) */
    .stText {
        color: """ + SECONDARY_TEXT_COLOR + """;
    }
    </style>
    """, unsafe_allow_html=True
)

# FIX: Use custom HTML for the main title to ensure color is applied
st.markdown(f'<h1>Loan Disbursement & Risk Dashboard (Card Style & Prediction) 📊</h1>', unsafe_allow_html=True)

# --- 2. DATA LOADING AND CLEANING ---
@st.cache_data
def load_data(file_name):
    """Loads and preprocesses the loan data."""
    try:
        df = pd.read_excel(file_name)
        df.columns = df.columns.str.strip()
        
        # Type Conversion and Cleaning
        df['Disbursment_Date'] = pd.to_datetime(df['Disbursment_Date'], errors='coerce')
        df['Admission_Date'] = pd.to_datetime(df['Admission_Date'], errors='coerce')
        
        # Rename and standardize column names
        df.rename(columns={'Cycle': 'Loan_Cycle', 'Loan Amount': 'Loan_Amount', 'Age': 'Borrower_Age'}, inplace=True)
        
        numeric_cols = ['Loan_Amount', 'Insurance_Amount', 'Outstanding_Pr', 'Due_Amount_Pr', 'Borrower_Age']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Create Age Group for analysis
        bins = [18, 25, 35, 45, 55, 100]
        labels = ['18-25', '26-35', '36-45', '46-55', '56+']
        df['Age_Group'] = pd.cut(df['Borrower_Age'], bins=bins, labels=labels, right=True, include_lowest=True)
        
        return df
    except Exception as e:
        # In a deployment scenario, this might need adjustment if the file path is relative
        st.error(f"Error loading or processing data: {e}")
        return pd.DataFrame()

file_name = "loan_disburse_report_Oct_2025.xlsx"
df = load_data(file_name)

if df.empty:
    # Attempt to load the file again if it failed, or stop. We'll stop here since the file was previously loaded.
    st.stop()

# --- 3. FORMATTING FUNCTION ---
def fullint(val):
    """Formats large numbers with commas, handling NaN/None."""
    if pd.isnull(val) or val == 0:
        return "0"
    val = float(val)
    return "{:,}".format(int(val)) if val.is_integer() else "{:,.2f}".format(val)

# --- 4. KPI CALCULATION AND DISPLAY (New Shadowed Style) ---
kpi_values = [
    ("Total Loan Disbursed", fullint(df['Loan_Amount'].sum())),
    ("Number of Loans", fullint(len(df))),
    ("Avg Loan Amount", fullint(df['Loan_Amount'].mean())),
    ("Total Insurance", fullint(df['Insurance_Amount'].sum())),
    ("Outstanding Principal", fullint(df['Outstanding_Pr'].sum())),
    ("Total Due Principal", fullint(df['Due_Amount_Pr'].sum())),
]

# FIX: Use custom HTML for the KPI section title
st.markdown(f'<h3 style="color: {PRIMARY_COLOR};">Key Performance Indicators</h3>', unsafe_allow_html=True)
with st.container():
    num_cols = len(kpi_values)
    k_cols = st.columns(num_cols)
    for idx, (label, value) in enumerate(kpi_values):
        k_cols[idx].markdown(
            f"""
            <div style='
                background-color: #ffffff; 
                border-radius: 12px;
                border-left: 6px solid {PRIMARY_COLOR}; 
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2); 
                padding: 1.2em 0.5em 1.2em 0.5em; 
                margin-bottom: 20px; 
                min-width: 100px;
                display:flex; 
                flex-direction:column; 
                align-items:center; 
                justify-content:center;
            '>
                <span style='font-size:1.0em; color:#4a4a4a; font-weight:600; margin-bottom:0.2em;'>{label}</span>
                <span style='font-size:1.7em; font-weight:700; color:#1e40af; letter-spacing:0.02em;'>{value}</span>
            </div>
            """, unsafe_allow_html=True
        )

# --- 5. PLOTTING FUNCTIONS ---

def plot_base_config(fig, y_format=','):
    """Applies common clean styling to all Plotly charts."""
    fig.update_layout(
        plot_bgcolor="#ffffff", 
        paper_bgcolor="#ffffff",
        font_family="Arial", 
        font_color=SECONDARY_TEXT_COLOR, # Ensure plot text is visible
        margin=dict(l=20, r=20, t=50, b=30),
        title_font_size=18,
        title_x=0.05, 
        dragmode=False,
        hovermode="x unified",
        uirevision="static"
    )
    fig.update_xaxes(showgrid=False, rangeslider_visible=False, automargin=True, title_font_size=12)
    fig.update_yaxes(gridcolor="#f0f0f0", tickformat=y_format, title_font_size=12)
    return fig

def plot_bar(df_, x, y, title, color=PRIMARY_COLOR, orientation='v', n_top=None, **kwargs):
    """Styled Bar Chart with optional data labels."""
    if df_[y].dtype not in ['int64', 'float64']:
        df_[y] = pd.to_numeric(df_[y], errors='coerce').fillna(0)
        
    df_sorted = df_.sort_values(y, ascending=False).head(n_top) if n_top else df_.sort_values(y, ascending=False)
    
    fig = px.bar(df_sorted, x=x, y=y, title=title, color_discrete_sequence=[color], orientation=orientation,
                 labels={x: x.replace('_', ' ').title(), y: y.replace('_', ' ').title()})
    
    fig.update_traces(
        opacity=0.9, 
        marker_line_width=0,
        width=0.7, 
        hovertemplate=f"<b>%{{x}}</b><br>{y.replace('_', ' ')}: <b>%{{y:,.0f}}</b><extra></extra>"
    )
    
    if kwargs.get('show_labels'):
        fig.update_traces(
            text=df_sorted[y].apply(lambda v: f'{v:,.0f}'),
            textposition='outside',
            cliponaxis=False, 
            textfont=dict(color="#333333", size=11, family="Arial")
        )
        max_y = df_sorted[y].max()
        if max_y > 0:
            fig.update_yaxes(range=[0, max_y * 1.15])
    
    fig = plot_base_config(fig)
    fig.update_layout(bargap=0.3, showlegend=False)
    return fig

def plot_pie(df_, names, values, title, color_sequence=px.colors.qualitative.D3):
    """Styled Pie Chart."""
    fig = px.pie(df_, names=names, values=values, title=title, 
                 color_discrete_sequence=color_sequence,
                 labels={names: names.replace('_', ' ').title(), values: values.replace('_', ' ').title()})
    
    fig.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#ffffff', width=2)),
                      hovertemplate=f"<b>%{{label}}</b><br>{values.replace('_', ' ')}: <b>%{{value:,.0f}}</b> (%{{percent}})<extra></extra>")
    
    fig = plot_base_config(fig)
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide', showlegend=True,
                      legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
    return fig

def plot_line(df_, x, y, title, color=PRIMARY_COLOR):
    """Styled Line Chart for time series data."""
    fig = px.line(df_, x=x, y=y, title=title, 
                  labels={x: x.replace('_', ' ').title(), y: y.replace('_', ' ').title()})
    
    fig.update_traces(line=dict(width=3, color=color), mode='lines+markers', marker=dict(size=6))
    fig.update_layout(hovermode="x unified", showlegend=False)
    fig = plot_base_config(fig)
    return fig

def display_card_plot(fig, container, chart_title):
    """Wraps a Plotly figure in a shadowed HTML container."""
    with container:
        # Custom HTML to create a shadowed card around the plot
        st.markdown(
            f"""
            <div style='
                background-color: #ffffff; 
                border-radius: 12px;
                padding: 10px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); 
                margin-bottom: 20px;
                height: 100%;
            '>
            """, unsafe_allow_html=True
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)


# --- 6. DASHBOARD LAYOUT AND PLOT GENERATION (All Shadowed) ---

st.markdown("<hr style='border: 1px solid #f0f0f0;'>", unsafe_allow_html=True)
st.markdown(f'<h3 style="color: {PRIMARY_COLOR};">Loan Disbursement Analysis</h3>', unsafe_allow_html=True)

# Row 1: Frequency, Outstanding/Loan, Insurance
col1, col2, col3 = st.columns(3)

# 1. Loan Amount by Frequency
freq_sum = df.groupby('Frequency')['Loan_Amount'].sum().reset_index()
fig1 = plot_bar(freq_sum, "Frequency", "Loan_Amount", "1. Loan Amount by Frequency")
display_card_plot(fig1, col1, "1. Loan Amount by Frequency")

# 2. Outstanding by Divisional Office
div_out = df.groupby('Divisional_Office')['Outstanding_Pr'].sum().reset_index()
fig2 = plot_bar(div_out, "Divisional_Office", "Outstanding_Pr", "2. Outstanding Principal by Divisional Office", color="#ef4444")
display_card_plot(fig2, col2, "2. Outstanding Principal by Divisional Office")

# 3. Insurance Amount by Divisional Office
div_ins = df.groupby('Divisional_Office')['Insurance_Amount'].sum().reset_index()
fig3 = plot_bar(div_ins, "Divisional_Office", "Insurance_Amount", "3. Insurance Amount by Division", color="#10b981")
display_card_plot(fig3, col3, "3. Insurance Amount by Division")

st.markdown("<hr style='border: 1px solid #f0f0f0;'>", unsafe_allow_html=True)

# Row 2: Divisional Metrics, Top Zone Office, Gender
col4, col5 = st.columns(2)

# 4. Total Loan Amount by Divisional Office
div_loan = df.groupby('Divisional_Office')['Loan_Amount'].sum().reset_index()
fig4 = plot_bar(div_loan, "Divisional_Office", "Loan_Amount", "4. Total Loan Amount by Divisional Office", color="#f59e0b")
display_card_plot(fig4, col4, "4. Total Loan Amount by Divisional Office")

# 5. Top Zone Office by Loan Amount
zone_sum = df.groupby('Zone_Office')['Loan_Amount'].sum().reset_index()
fig5 = plot_bar(zone_sum, "Zone_Office", "Loan_Amount", "5. Top 10 Zone Offices by Loan Amount", color="#8b5cf6", n_top=10)
display_card_plot(fig5, col5, "5. Top 10 Zone Offices by Loan Amount")

st.markdown("<hr style='border: 1px solid #f0f0f0;'>", unsafe_allow_html=True)

col6, col7 = st.columns(2)

# 6. Loan Amount Distribution by Gender
gender_sum = df.groupby('Gender')['Loan_Amount'].sum().reset_index()
fig6 = plot_pie(gender_sum, 'Gender', 'Loan_Amount', '6. Loan Amount by Gender', color_sequence=['#2563eb', '#ef4444'])
display_card_plot(fig6, col6, "6. Loan Amount Distribution by Gender")

# 7. New Borrower Count Over Time
admit_count = df.groupby(df['Admission_Date'].dt.to_period('M')).agg({'BorrowerCode': 'nunique'}).reset_index()
admit_count['Admission_Date'] = admit_count['Admission_Date'].astype(str)
fig7 = plot_line(admit_count, "Admission_Date", "BorrowerCode", "7. New Borrowers (Count) Over Time", color="#059669")
display_card_plot(fig7, col7, "7. New Borrower Count Over Time")

st.markdown("<hr style='border: 1px solid #f0f0f0;'>", unsafe_allow_html=True)

# Row 4: Time Series, Age, Purpose
col8, col9 = st.columns(2)

# 8. Loan Disbursement Trend
disburse_sum = df.groupby(df['Disbursment_Date'].dt.to_period('D'))['Loan_Amount'].sum().reset_index()
disburse_sum['Disbursment_Date'] = disburse_sum['Disbursment_Date'].astype(str)
fig8 = plot_line(disburse_sum, "Disbursment_Date", "Loan_Amount", "8. Daily Loan Disbursement Amount", color="#2563eb")
display_card_plot(fig8, col8, "8. Loan Disbursement Trend")

# 9. Average Loan Amount by Borrower Age Group
age_loan_mean = df.groupby('Age_Group')['Loan_Amount'].mean().reset_index()
age_loan_mean['Loan_Amount'] = age_loan_mean['Loan_Amount'].fillna(0)
fig9 = plot_bar(age_loan_mean, 'Age_Group', 'Loan_Amount', "9. Average Loan Amount by Borrower Age Group", color="#f97316")
display_card_plot(fig9, col9, "9. Average Loan Amount by Borrower Age Group")

st.markdown("<hr style='border: 1px solid #f0f0f0;'>", unsafe_allow_html=True)

col10, col11 = st.columns(2)

# 10. Top Loan Purposes by Loan Amount
purpose_sum = df.groupby('Purpose')['Loan_Amount'].sum().reset_index()
fig10 = plot_bar(purpose_sum, "Purpose", "Loan_Amount", "10. Top 10 Loan Purposes", color="#ca8a04", n_top=10)
display_card_plot(fig10, col10, "10. Top Loan Purposes by Loan Amount")

# 11. Loan Cycle by Loan Amount (Enhanced)
cycle_sum = df.groupby('Loan_Cycle')['Loan_Amount'].sum().reset_index()
cycle_sum['Loan_Cycle'] = cycle_sum['Loan_Cycle'].astype(str)
fig11 = plot_bar(cycle_sum, "Loan_Cycle", "Loan_Amount", "11. Loan Amount by Loan Cycle", color="#be185d", show_labels=True)
display_card_plot(fig11, col11, "11. Loan Cycle by Loan Amount")

st.markdown("<hr style='border: 1px solid #f0f0f0;'>", unsafe_allow_html=True)

# Row 6: Loan Product, Sc Rate, Installment, Disbursement Type
col12, col13 = st.columns(2)

# 12. Loan Product by Loan Amount
product_sum = df.groupby('Current_Loan_Product')['Loan_Amount'].sum().reset_index()
fig12 = plot_bar(product_sum, "Current_Loan_Product", "Loan_Amount", "12. Loan Amount by Current Loan Product", color="#06b6d4")
display_card_plot(fig12, col12, "12. Loan Product by Loan Amount")

# 13. Service Charge Rate (Sc_Rate) by Loan Amount (Enhanced)
sc_sum = df.groupby('Sc_Rate')['Loan_Amount'].sum().reset_index()
fig13 = plot_bar(sc_sum, "Sc_Rate", "Loan_Amount", "13. Loan Amount by Service Charge Rate", color="#f472b6", show_labels=True)
display_card_plot(fig13, col13, "13. Service Charge Rate by Loan Amount")

st.markdown("<hr style='border: 1px solid #f0f0f0;'>", unsafe_allow_html=True)

col14, col15 = st.columns(2)

# 14. Loan Count by Number of Installments (Enhanced)
install_count = df.groupby('No_Of_Installment').size().reset_index(name='Loan_Count')
install_count['No_Of_Installment'] = install_count['No_Of_Installment'].astype(str)
fig14 = plot_bar(install_count, "No_Of_Installment", "Loan_Count", "14. Loan Count by Number of Installments", color="#4f46e5", show_labels=True)
display_card_plot(fig14, col14, "14. Loan Count by Number of Installments")

# 15. Loan Count by Disbursement Type
disburse_type_count = df.groupby('Disbursement_Type').size().reset_index(name='Loan_Count')
fig15 = plot_bar(disburse_type_count, "Disbursement_Type", "Loan_Count", "15. Loan Count by Disbursement Type", color="#dc2626")
display_card_plot(fig15, col15, "15. Loan Count by Disbursement Type")


# --- 7. LOAN AMOUNT PREDICTION MODEL ---

st.markdown("<hr style='border: 1px solid #f0f0f0;'>", unsafe_allow_html=True)
st.markdown(f'<h3 style="color: {PRIMARY_COLOR};">Next Month Loan Disbursement Prediction 🔮</h3>', unsafe_allow_html=True)

# Calculate prediction values
oct_loan_amount = df['Loan_Amount'].sum()
min_date = df['Disbursment_Date'].min()
max_date = df['Disbursment_Date'].max()

if pd.notna(min_date) and pd.notna(max_date):
    disbursing_days = (max_date - min_date).days + 1
else:
    disbursing_days = 27 
    
avg_daily_disbursement = oct_loan_amount / disbursing_days
days_in_november = 30
predicted_nov_amount = avg_daily_disbursement * days_in_november
change = 'an **increase**' if predicted_nov_amount > oct_loan_amount else 'a **decrease**'
change_color = '#059669' if predicted_nov_amount > oct_loan_amount else '#ef4444'

col_pred1, col_pred2 = st.columns([1, 2])

with col_pred1:
    st.markdown(
        f"""
        <div style='
            background-color: #ffffff; 
            border-radius: 12px;
            padding: 1.5em;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); 
            min-height: 200px;
        '>
            <h4 style='color: {PRIMARY_COLOR}; margin-top:0;'>Predicted Change:</h4>
            <div style='text-align:center; padding: 10px 0;'>
                <span style='font-size: 2.2em; font-weight: 800; color: {change_color};'>
                    {change.upper()}
                </span>
            </div>
            <p style='font-size: 1.0em; color:#4a4a4a; font-weight:600; text-align:center;'>
                (Predicted value for Nov is 30 days of average October daily disbursement.)
            </p>
        </div>
        """, unsafe_allow_html=True
    )

with col_pred2:
    st.markdown(
        f"""
        <div style='
            background-color: #ffffff; 
            border-radius: 12px;
            padding: 1.5em;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); 
            min-height: 200px;
        '>
            <h4 style='color: {PRIMARY_COLOR}; margin-top:0;'>Prediction Details:</h4>
            <ul style='list-style-type: none; padding-left: 0; font-size: 1.1em; color:{SECONDARY_TEXT_COLOR};'>
                <li style='margin-bottom: 0.5em;'>
                    <strong>Total Loan Disbursed (Oct 2025):</strong> 
                    <span style='float: right;'>${fullint(oct_loan_amount)}</span>
                </li>
                <li style='margin-bottom: 0.5em;'>
                    <strong>Active Disbursing Days:</strong> 
                    <span style='float: right;'>{disbursing_days} days</span>
                </li>
                <li style='margin-bottom: 0.5em;'>
                    <strong>Avg Daily Disbursement (ADD):</strong> 
                    <span style='float: right;'>${fullint(avg_daily_disbursement)}</span>
                </li>
                <li style='margin-bottom: 0.5em; padding-top: 5px; border-top: 1px solid #eee;'>
                    <strong>Predicted Nov Total (30 days):</strong> 
                    <span style='float: right; font-weight: 700; color: {PRIMARY_COLOR};'>${fullint(predicted_nov_amount)}</span>
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True
    )
    
st.markdown("<div style='text-align:center; color: #999; padding-top:2em;'>"
    "Dashboard Complete | All charts and KPIs are displayed in modern, shadowed card containers."
    "</div>", unsafe_allow_html=True)
