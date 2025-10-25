import streamlit as st
import pandas as pd
import altair as alt
from datetime import date, timedelta
from streamlit_extras.metric_cards import style_metric_cards
import numpy as np
import warnings



# Suppress warnings
warnings.filterwarnings("ignore")


# --- Helper Function for Styled Plots ---

def render_styled_chart(header_text, chart_obj):
    """Wraps subheader and Altair chart in a div with a clean box-shadow style.
    Ensures the chart is STATIC and auto-scaled."""
    st.subheader(header_text)
    # Custom CSS style for the plot box
    st.markdown(f"""
        <div style="border-radius: 10px; box-shadow: 5px 5px 15px rgba(0, 0, 0, 0.08); padding: 15px; background-color: #FFFFFF; margin-bottom: 20px;">
    """, unsafe_allow_html=True)
    
    # 🚨 CRITICAL: interactive(False) ensures zoom/pan is OFF for a static dashboard,
    # preventing mouse wheel zooming and dragging.
    st.altair_chart(chart_obj.interactive(False), use_container_width=True, theme=None)
    
    st.markdown("</div>", unsafe_allow_html=True)
    # Removed the extra horizontal rule inside the render function


# --- Configuration and Data Loading (WITH CACHING) ---

# Page layout
st.set_page_config(page_title="Loan Analytics", page_icon="🌎", layout="wide")

# Define a professional, new-style color palette (NEW STYLE)
PALETTE = {
    'loan_primary': '#185ADB',   # Teal Accent
    'outstanding': '#00B894',    # Green
    'due': '#D63031',            # Red
    'insurance': '#FFC947',      # Gold Accent
    'demographic': '#6C5CE7',    # Purple
    'text_dark': '#FFFFFF',      # KPI TEXT COLOR (White)
    'card_bg': '#0A1931',        # Dark Navy Blue for KPIs
    'shadow': '0 6px 15px rgba(0, 0, 0, 0.08)' 
}


# **Caching the data loading and initial cleaning to solve slow load times**
@st.cache_data
def load_data():
    try:
        # 🚨 FIX: Using pd.read_excel as requested by the file name in the user's code
        df = pd.read_excel("loandisbursereport-sep_2025.xlsx") 
        
        # Clean and prepare columns
        df['Disbursment_Date'] = pd.to_datetime(df['Disbursment_Date'])
        df['First_Repayment_Date'] = pd.to_datetime(df['First_Repayment_Date'], errors='coerce') 
        
        df['Loan_Amount'] = pd.to_numeric(df['Loan_Amount'], errors='coerce').fillna(0)
        df['Outstanding_Pr'] = pd.to_numeric(df['Outstanding_Pr'], errors='coerce').fillna(0)
        df['Insurance_Amount'] = pd.to_numeric(df['Insurance_Amount'], errors='coerce').fillna(0)
        df['Due_Amount_Pr'] = pd.to_numeric(df['Due_Amount_Pr'], errors='coerce').fillna(0)
        
        # NEW CLEANING FOR NEW PLOTS
        df['Sc_Rate'] = df['Sc_Rate'].astype(str).str.replace('%', '').str.strip()
        df['Sc_Rate'] = pd.to_numeric(df['Sc_Rate'], errors='coerce').fillna(0)
        df['No_Of_Installment'] = pd.to_numeric(df['No_Of_Installment'], errors='coerce').fillna(0)
        df['Borrower_Age'] = pd.to_numeric(df['Borrower_Age'], errors='coerce').fillna(0)
        df['Loan_Cycle'] = pd.to_numeric(df['Loan_Cycle'], errors='coerce').fillna(0) 
        
        # Create Age Bins for Loan Amount by Age Group 
        bins = [18, 25, 35, 45, 55, 100]
        labels = ['18-24', '25-34', '35-44', '45-54', '55+']
        df['Age_Group'] = pd.cut(df['Borrower_Age'], bins=bins, labels=labels, right=False)
        return df
        
    except FileNotFoundError:
        st.error("🚨 Error: The data file 'loandisbursereport-sep_2025.xlsx' was not found. Please ensure it is in the same directory.")
        st.stop()
    except Exception as e:
        st.error(f"🚨 An error occurred during data loading or preparation: {e}")
        st.stop()

df = load_data()


# --- Title and Image ---
st.title("Loan Disbursement SEP-2025 Portfolio Analytics Dashboard")

# load CSS Style (Custom CSS to force KPI text white on Dark Navy card background)
st.markdown(f"""
    <style>
        /* Change metric labels to white */
        [data-testid="stMetricLabel"] > div {{
            color: {PALETTE['text_dark']} !important;
        }}
        /* Change metric values to white */
        [data-testid="stMetricValue"] {{
            color: {PALETTE['text_dark']} !important;
            font-size: 1.8em; /* Slightly larger value font */
        }}
        /* General page background for new style */
        .stApp {{
            background-color: #F7F9FC; /* Light gray background */
        }}
    </style>
""", unsafe_allow_html = True)


# --- Sidebar: Image and Filters (REMOVED) ---

# Apply a global filter for the entire dashboard (e.g., all time)
df_selection = df.copy() # Use the full loaded data since filters are off


# --- Metrics (KPIs) ---

st.header('Key Performance Indicators (KPIs)')

# Mapped Loan Metrics to Sales KPI Structure
total_loans = df_selection.shape[0]
sum_loan_amount = df_selection.Loan_Amount.sum()
max_loan_amount = df_selection.Loan_Amount.max()
min_loan_amount = df_selection.Loan_Amount.min()
median_loan_amount = df_selection.Loan_Amount.median()

col1, col2, col3, col4 = st.columns(4)

# ************************ KPI LABELS UPDATED HERE ************************
# 1. Total Amount Sum (New Primary KPI)
col1.metric(label="💰 Total Loan Amount Disbursed", value=f"{sum_loan_amount:,.0f}", delta="Total Sum") 

# 2. Number of Disbursed Loans
col2.metric(label="✅ Number of Disbursed Loans", value=total_loans)

# 3. Highest Disbursement (Max)
col3.metric(label="📈 Highest Disbursement", value=f"{max_loan_amount:,.0f}", delta=f"Median: {median_loan_amount:,.0f}")

# 4. Lowest Disbursement (Min)
col4.metric(label="📉 Lowest Disbursement", value=f"{min_loan_amount:,.0f}")
# ************************ END KPI LABELS UPDATE ************************

# Apply custom metric card style with the new Dark Navy background and Gold/Orange accent
style_metric_cards(
    background_color=PALETTE['card_bg'], 
    border_left_color=PALETTE['insurance'], 
    border_color="#1f66bd", 
    box_shadow=PALETTE['shadow']
)

st.markdown("---")


# --- Visualizations & Analysis ---

# FORMAT STRING FOR AMOUNT
AMOUNT_FORMAT = ',.0f'
AMOUNT_AXIS_TITLE_LONG = 'Total Amount'
AMOUNT_AXIS_TITLE_SHORT = 'Sum of Loan Amount'
AMOUNT_AXIS_TITLE_INSURANCE = 'Sum of Insurance Amount'
AMOUNT_AXIS_TITLE_LOAN = 'Loan Amount'

# DEFAULT HEIGHT FOR PLOTS TO PREVENT INTERFERENCE
DEFAULT_PLOT_HEIGHT = 350 # Slightly taller plots for better look


# ==================================
## 📈 Financial Health Overview
# ==================================
col_s1_1, col_s1_2 = st.columns(2)

with col_s1_1:
    # 1. Loan_Amount vs Outstanding_Pr by Divisional_Office (Normalized Stacked Bar Chart - Style Bar Chart)
    office_summary = df_selection.groupby('Divisional_Office')[['Loan_Amount', 'Outstanding_Pr']].sum().reset_index()
    chart_data_comparison = office_summary.melt(
        'Divisional_Office', var_name='Metric', value_name='Amount'
    ).replace(
        {'Loan_Amount': 'Total Loan Amount', 'Outstanding_Pr': 'Outstanding Principal'}
    )
    
    comparison_chart = alt.Chart(chart_data_comparison).mark_bar().encode(
        # Use stack='normalize' on the X-axis for a 100% stacked bar chart
        x=alt.X('Amount:Q', stack='normalize', title='Proportion of Total Principal Metrics', axis=alt.Axis(format='%')), 
        y=alt.Y('Divisional_Office:N', title='Divisional Office', sort=alt.EncodingSortField(field="Amount", op="sum", order='descending')),
        color=alt.Color('Metric:N', scale=alt.Scale(range=[PALETTE['loan_primary'], PALETTE['outstanding']])),
        order=alt.Order('Metric:N', sort='ascending'), # Ensure consistent stacking order
        tooltip=[
            'Divisional_Office', 
            alt.Tooltip('Metric:N', title='Metric'),
            alt.Tooltip('Amount:Q', format=',.0f', title='Total Amount'),
            alt.Tooltip('Amount:Q', format='.1%', title='Proportion') 
        ]
    ).properties(title='Proportion of Principal Metrics (Loan vs. Outstanding) by Office', height=DEFAULT_PLOT_HEIGHT, width='container')
    
    render_styled_chart("Proportion of Principal Metrics (Loan vs. Outstanding)", comparison_chart)

with col_s1_2:
    # 2. Divisional_Office by Due_Amount_Pr, Loan_Amount (Faceted Bar Chart)
    due_vs_loan_summary = df_selection.groupby('Divisional_Office')[['Loan_Amount', 'Due_Amount_Pr']].sum().reset_index()
    chart_data_due_vs_loan = due_vs_loan_summary.melt(
        'Divisional_Office', var_name='Metric', value_name='Amount'
    ).replace(
        {'Loan_Amount': 'Total Loan Amount', 'Due_Amount_Pr': 'Total Due Principal'}
    )

    due_vs_loan_chart = alt.Chart(chart_data_due_vs_loan).mark_bar().encode(
        x=alt.X('Amount:Q', title=AMOUNT_AXIS_TITLE_LONG, axis=alt.Axis(format=AMOUNT_FORMAT)),
        y=alt.Y('Divisional_Office:N', title='Divisional Office', sort=alt.EncodingSortField(field="Amount", op="sum", order='descending')),
        color=alt.Color('Metric:N', scale=alt.Scale(range=[PALETTE['loan_primary'], PALETTE['due']])),
        tooltip=['Divisional_Office', 'Metric', alt.Tooltip('Amount:Q', format=AMOUNT_FORMAT)]
    ).properties(title='Loan Amount vs Due Principal', height=DEFAULT_PLOT_HEIGHT, width='container')
    
    render_styled_chart("Loan Amount vs. Due Principal by Office", due_vs_loan_chart)


# ---
## 🗓️ Time Series Analysis
# ---
col_s2_1, col_s2_2 = st.columns(2)

with col_s2_1:
    # 3. Altair Line Chart (Disbursement Trend by Date)
    daily_data = df_selection.groupby(df_selection['Disbursment_Date'].dt.date)['Loan_Amount'].sum().reset_index()
    daily_data.columns = ['Disbursement Date', 'Loan Amount']
    
    line_chart = alt.Chart(daily_data).mark_line(point=True, color=PALETTE['loan_primary']).encode(
        x=alt.X('Disbursement Date:T', title='Disbursement Date'),
        y=alt.Y('Loan Amount:Q', title=AMOUNT_AXIS_TITLE_SHORT, axis=alt.Axis(format=AMOUNT_FORMAT)),
        tooltip=[
            alt.Tooltip('Disbursement Date:T', format='%Y-%m-%d'),
            alt.Tooltip('Loan Amount:Q', format=AMOUNT_FORMAT)
        ]
    ).properties(title="Daily Loan Disbursement Trend", height=DEFAULT_PLOT_HEIGHT, width='container')
    
    render_styled_chart("Disbursement Trend (Loan Amount by Date)", line_chart)
    
with col_s2_2:
    # 4. Admission_Date by BorrowerCode (Time Series Count)
    borrower_trend = df_selection.groupby('Admission_Date')['BorrowerCode'].nunique().reset_index()
    borrower_trend.columns = ['Admission Date', 'New Borrower Count']
    
    chart_borrower_trend = alt.Chart(borrower_trend).mark_line(point=True, color=PALETTE['demographic']).encode(
        x=alt.X('Admission Date:T', title='Admission Date'),
        y=alt.Y('New Borrower Count:Q', title='New Borrower Count'),
        tooltip=[
            alt.Tooltip('Admission Date:T', format='%Y-%m-%d'),
            'New Borrower Count:Q'
        ]
    ).properties(title="New Borrower Count Over Time", height=DEFAULT_PLOT_HEIGHT, width='container')
    
    render_styled_chart("New Borrower Trend (Count by Admission Date)", chart_borrower_trend)


# ---
## 🧑‍🤝‍🧑 Borrower Deep Dive & Demographics
# ---

# Full Width Plot for Stacked Bar (Plot 5)
# 5. Top BorrowerCode Divisional_Office-wise loan amount (Stacked Bar Chart)
top_borrowers_overall = df_selection.groupby(['BorrowerCode', 'Divisional_Office'])['Loan_Amount'].sum().reset_index()

# Get the top 25 BorrowerCodes by their total Loan Amount across all offices
top_25_codes = top_borrowers_overall.groupby('BorrowerCode')['Loan_Amount'].sum().nlargest(25).index.tolist()
df_top_25_office = top_borrowers_overall[top_borrowers_overall['BorrowerCode'].isin(top_25_codes)]

# Set a slightly larger height for the full-width borrower chart
chart_top_borrower_office = alt.Chart(df_top_25_office).mark_bar().encode(
    x=alt.X('Loan_Amount:Q', title=AMOUNT_AXIS_TITLE_SHORT, axis=alt.Axis(format=AMOUNT_FORMAT)),
    y=alt.Y('BorrowerCode:N', sort=top_25_codes, title='Borrower Code'), 
    color=alt.Color('Divisional_Office:N', title='Divisional Office', scale=alt.Scale(range=[PALETTE['loan_primary'], PALETTE['outstanding'], PALETTE['demographic'], PALETTE['insurance']])),
    tooltip=['BorrowerCode', 'Divisional_Office', alt.Tooltip('Loan_Amount:Q', format=AMOUNT_FORMAT, title='Loan Amount')]
).properties(title="Top 25 Borrower Codes: Loan Amount by Divisional Office", height=450, width='container')

render_styled_chart("Top 25 Borrower Codes: Loan Amount by Divisional Office", chart_top_borrower_office)


col_s3_1, col_s3_2 = st.columns(2)

with col_s3_1:
    # 6. Top 25 Borrower Codes by Loan Amount and their Age
    top_members = df_selection.groupby(['BorrowerCode', 'Borrower_Age']).agg(
        Total_Loan_Amount=('Loan_Amount', 'sum')
    ).reset_index().nlargest(25, 'Total_Loan_Amount')
    
    top_members['Borrower_Code_Info'] = top_members['BorrowerCode'] + ' (' + top_members['Borrower_Age'].round(0).astype(int).astype(str) + ')'
    
    # Use a sequential color scale for age
    age_color_scale = alt.Scale(domain=[top_members['Borrower_Age'].min(), top_members['Borrower_Age'].max()], range=['#FFC947', '#D63031'])

    chart_top_members = alt.Chart(top_members).mark_bar().encode(
        x=alt.X('Total_Loan_Amount:Q', title=AMOUNT_AXIS_TITLE_SHORT, axis=alt.Axis(format=AMOUNT_FORMAT)),
        y=alt.Y('Borrower_Code_Info:N', title='Borrower Code (Age)', sort=alt.EncodingSortField(field="Total_Loan_Amount", op="sum", order='descending')),
        color=alt.Color('Borrower_Age:Q', title='Age', scale=age_color_scale),
        tooltip=[
            alt.Tooltip('BorrowerCode', title='Borrower Code'),
            alt.Tooltip('Total_Loan_Amount:Q', format=AMOUNT_FORMAT, title='Loan Amount'),
            alt.Tooltip('Borrower_Age:Q', format='.1f', title='Age')
        ]
    ).properties(title="Top 25 Borrower Codes by Total Loan Amount (Colored by Age)", height=DEFAULT_PLOT_HEIGHT + 100, width='container') # Slightly taller
    
    render_styled_chart("Top 25 Borrower Codes by Total Loan Amount", chart_top_members)

with col_s3_2:
    # 7. Borrower_Age by Loan_Amount (Binned Bar Chart - VERTICAL STYLE)
    age_summary = df_selection.groupby('Age_Group')['Loan_Amount'].sum().reset_index()
    age_sort_order = ['18-24', '25-34', '35-44', '45-54', '55+']
    
    chart_age = alt.Chart(age_summary).mark_bar(color=PALETTE['demographic']).encode(
        x=alt.X('Age_Group:N', title='Age Group', sort=age_sort_order),
        y=alt.Y('Loan_Amount:Q', title=AMOUNT_AXIS_TITLE_SHORT, axis=alt.Axis(format=AMOUNT_FORMAT)),
        tooltip=['Age_Group', alt.Tooltip('Loan_Amount:Q', format=AMOUNT_FORMAT, title='Loan Amount')]
    ).properties(title="Total Loan Amount by Age Group", height=DEFAULT_PLOT_HEIGHT + 100, width='container') # Slightly taller
    
    render_styled_chart("Loan Amount by Borrower Age Group", chart_age)


# ---
## 📊 Categorical Distribution Analysis
# ---
col_s4_1, col_s4_2 = st.columns(2)

with col_s4_1:
    # 8. Purpose by Loan Amount (Horizontal Bar Chart) - NOW TOP 15
    purpose_summary = df_selection.groupby('Purpose')['Loan_Amount'].sum().reset_index().nlargest(15, 'Loan_Amount')
    purpose_summary.columns = ["Purpose", "Loan_Amount_Sum"]

    source_purpose = pd.DataFrame({
        "Loan Amount": purpose_summary["Loan_Amount_Sum"],
        "Purpose": purpose_summary["Purpose"]
    })
    
    chart_purpose = alt.Chart(source_purpose).mark_bar(color=PALETTE['loan_primary']).encode(
        x=alt.X("Loan Amount:Q", title=AMOUNT_AXIS_TITLE_SHORT, axis=alt.Axis(format=AMOUNT_FORMAT)),
        y=alt.Y("Purpose:N", sort="-x", title="Loan Purpose"), 
        tooltip=["Purpose", alt.Tooltip("Loan Amount:Q", format=AMOUNT_FORMAT)]
    ).properties(title="Top 15 Loan Amount by Purpose", height=DEFAULT_PLOT_HEIGHT, width='container')
    
    render_styled_chart("Top 15 Loan Amount by Purpose", chart_purpose)

    # 9. TOP 25 Zone_Office by Loan_Amount (Bar Chart)
    zone_summary = df_selection.groupby('Zone_Office')['Loan_Amount'].sum().reset_index().nlargest(25, 'Loan_Amount')
    
    chart_zone = alt.Chart(zone_summary).mark_bar(color=PALETTE['outstanding']).encode(
        x=alt.X('Loan_Amount:Q', title=AMOUNT_AXIS_TITLE_SHORT, axis=alt.Axis(format=AMOUNT_FORMAT)),
        y=alt.Y('Zone_Office:N', sort='-x', title='Zone Office'),
        tooltip=['Zone_Office', alt.Tooltip('Loan_Amount:Q', format=AMOUNT_FORMAT, title='Loan Amount')]
    ).properties(title="Top 25 Zones by Loan Amount", height=DEFAULT_PLOT_HEIGHT, width='container')
    
    render_styled_chart("TOP 25 Zone Office by Loan Amount", chart_zone)

with col_s4_2:
    # 10. Altair Bar Chart (Loan Amount by Loan Product) - NOW TOP 15
    product_summary = df_selection.groupby('Current_Loan_Product')['Loan_Amount'].sum().reset_index().nlargest(15, 'Loan_Amount')
    product_summary.columns = ["Current_Loan_Product", "Loan_Amount_Sum"]

    source_product = pd.DataFrame({
        "Loan Amount": product_summary["Loan_Amount_Sum"],
        "Product": product_summary["Current_Loan_Product"]
    })
    
    bar_chart_product = alt.Chart(source_product).mark_bar(color=PALETTE['loan_primary']).encode(
        x=alt.X("Loan Amount:Q", title=AMOUNT_AXIS_TITLE_SHORT, axis=alt.Axis(format=AMOUNT_FORMAT)),
        y=alt.Y("Product:N", sort="-x", title="Loan Product"),
        tooltip=["Product", alt.Tooltip("Loan Amount:Q", format=AMOUNT_FORMAT)]
    ).properties(title="Top 15 Loan Amount by Product", height=DEFAULT_PLOT_HEIGHT, width='container')
    
    render_styled_chart("Top 15 Loan Amount by Loan Product", bar_chart_product)
    
    # 11. Disbursement_Type by Loan_Amount (Bar Chart)
    type_summary = df_selection.groupby('Disbursement_Type')['Loan_Amount'].sum().reset_index()
    
    chart_type = alt.Chart(type_summary).mark_bar(color=PALETTE['demographic']).encode(
        x=alt.X('Disbursement_Type:N', title='Disbursement Type'),
        y=alt.Y('Loan_Amount:Q', title=AMOUNT_AXIS_TITLE_SHORT, axis=alt.Axis(format=AMOUNT_FORMAT)),
        tooltip=['Disbursement_Type', alt.Tooltip('Loan_Amount:Q', format=AMOUNT_FORMAT, title='Loan Amount')]
    ).properties(title="Total Loan Amount by Disbursement Type", height=DEFAULT_PLOT_HEIGHT, width='container')
    
    render_styled_chart("Loan Amount by Disbursement Type", chart_type)


# ---
## 🛡️ Loan Details & Ancillary Metrics
# ---
col_s5_1, col_s5_2 = st.columns(2)

with col_s5_1:
    # 12. Loan_Cycle by Loan_Amount (Vertical Bar Chart)
    cycle_summary = df_selection.groupby('Loan_Cycle')['Loan_Amount'].sum().reset_index()
    
    chart_cycle = alt.Chart(cycle_summary).mark_bar(color=PALETTE['loan_primary']).encode(
        # Sorting by the numeric Loan_Cycle field
        x=alt.X('Loan_Cycle:O', title='Loan Cycle', sort='ascending'), 
        y=alt.Y('Loan_Amount:Q', title=AMOUNT_AXIS_TITLE_SHORT, axis=alt.Axis(format=AMOUNT_FORMAT)), 
        tooltip=['Loan_Cycle', alt.Tooltip('Loan_Amount:Q', format=AMOUNT_FORMAT, title='Loan Amount')]
    ).properties(title="Total Loan Amount by Loan Cycle (Sorted Numerically)", height=DEFAULT_PLOT_HEIGHT, width='container')
    
    render_styled_chart("Loan Amount by Loan Cycle", chart_cycle)

    # 13. ALTAIR DONUT CHART (Loan Amount by Frequency)
    frequency_summary = df_selection.groupby('Frequency')['Loan_Amount'].sum().reset_index()
    frequency_summary.columns = ["Frequency", "Loan_Amount_Sum"]

    source_freq = pd.DataFrame({
        "Loan Amount": frequency_summary["Loan_Amount_Sum"],
        "Frequency": frequency_summary["Frequency"]
    })
    
    base = alt.Chart(source_freq).encode(theta=alt.Theta("Loan Amount:Q", stack=True))

    pie = base.mark_arc(outerRadius=120, innerRadius=80).encode(
        color=alt.Color("Frequency:N", title="Frequency", scale=alt.Scale(range=[PALETTE['demographic'], PALETTE['insurance'], PALETTE['loan_primary']])),
        order=alt.Order("Loan Amount:Q", sort="descending"),
        tooltip=[
            "Frequency", 
            alt.Tooltip("Loan Amount:Q", format=AMOUNT_FORMAT),
            alt.Tooltip("Loan Amount:Q", aggregate="sum", title="Proportion", format=".1%") 
        ]
    )

    text = base.mark_text(radius=140).encode(
        text=alt.Text("Loan Amount:Q", format=AMOUNT_FORMAT), 
        order=alt.Order("Loan Amount:Q", sort="descending"),
        color=alt.value("black")
    )

    donut_chart = ((pie + text).properties(title="Proportion of Loan Amount by Repayment Frequency"))
    
    render_styled_chart("Loan Amount by Frequency (Proportion)", donut_chart)

with col_s5_2:
    # 14. No_Of_Installment by Loan_Amount (Horizontal Bar Chart)
    installment_summary = df_selection.groupby('No_Of_Installment')['Loan_Amount'].sum().reset_index()
    
    chart_installment = alt.Chart(installment_summary).mark_bar(color=PALETTE['loan_primary']).encode(
        x=alt.X('Loan_Amount:Q', title=AMOUNT_AXIS_TITLE_SHORT, axis=alt.Axis(format=AMOUNT_FORMAT)),
        y=alt.Y('No_Of_Installment:O', title='Number of Installments', sort='-x'),
        tooltip=['No_Of_Installment', alt.Tooltip('Loan_Amount:Q', format=AMOUNT_FORMAT, title='Loan Amount')]
    ).properties(title="Total Loan Amount by No. of Installments", height=DEFAULT_PLOT_HEIGHT, width='container')
    
    render_styled_chart("Loan Amount by No. of Installments", chart_installment)

    # 15. Sc_Rate by Loan_Amount (Bar Chart)
    rate_summary = df_selection[df_selection['Sc_Rate'] > 0].groupby('Sc_Rate')['Loan_Amount'].sum().reset_index()
    
    chart_rate = alt.Chart(rate_summary).mark_bar(color=PALETTE['insurance']).encode(
        x=alt.X('Loan_Amount:Q', title=AMOUNT_AXIS_TITLE_SHORT, axis=alt.Axis(format=AMOUNT_FORMAT)),
        y=alt.Y('Sc_Rate:O', title='Service Charge Rate (%)', sort='-x'),
        tooltip=[alt.Tooltip('Sc_Rate:O', title='Rate (%)'), alt.Tooltip('Loan_Amount:Q', format=AMOUNT_FORMAT, title='Loan Amount')]
    ).properties(title="Total Loan Amount by SC Rate", height=DEFAULT_PLOT_HEIGHT, width='container')
    
    render_styled_chart("Loan Amount by Service Charge Rate", chart_rate)

# ---
## 🎁 Ancillary Metrics
# ---
col_s6_1, col_s6_2 = st.columns(2)

with col_s6_1:
    # 16. Insurance_Amount by Divisional_Office (Bar Chart)
    insurance_summary = df_selection.groupby('Divisional_Office')['Insurance_Amount'].sum().reset_index()
    insurance_summary.columns = ["Divisional_Office", "Insurance_Amount_Sum"]

    source_insurance = pd.DataFrame({
        "Insurance Amount": insurance_summary["Insurance_Amount_Sum"],
        "Office": insurance_summary["Divisional_Office"]
    })
    
    bar_chart_insurance = alt.Chart(source_insurance).mark_bar(color=PALETTE['insurance']).encode(
        x=alt.X("Insurance Amount:Q", title=AMOUNT_AXIS_TITLE_INSURANCE, axis=alt.Axis(format=AMOUNT_FORMAT)),
        y=alt.Y("Office:N", sort="-x", title="Divisional Office"),
        tooltip=["Office", alt.Tooltip("Insurance Amount:Q", format=AMOUNT_FORMAT)]
    ).properties(title="Total Insurance Amount by Office", height=DEFAULT_PLOT_HEIGHT, width='container')
    
    render_styled_chart("Insurance Amount by Divisional Office", bar_chart_insurance)

with col_s6_2:
    # 17. TOP 25 Branch_Name by Loan_Amount (Horizontal Bar Chart)
    branch_summary = df_selection.groupby('Branch_Name')['Loan_Amount'].sum().reset_index().nlargest(25, 'Loan_Amount')
    
    chart_branch = alt.Chart(branch_summary).mark_bar(color=PALETTE['outstanding']).encode(
        x=alt.X('Loan_Amount:Q', title=AMOUNT_AXIS_TITLE_SHORT, axis=alt.Axis(format=AMOUNT_FORMAT)),
        y=alt.Y('Branch_Name:N', sort='-x', title='Branch Name'),
        tooltip=['Branch_Name', alt.Tooltip('Loan_Amount:Q', format=AMOUNT_FORMAT, title='Loan Amount')]
    ).properties(title="Top 25 Branch Name by Loan Amount", height=DEFAULT_PLOT_HEIGHT, width='container')

    render_styled_chart("Top 25 Branch Name by Loan Amount", chart_branch)


# ==================================
# FOOTER
# ==================================
st.markdown("---")
