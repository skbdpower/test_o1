import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

# --- NEW COLOR PALETTE ---
# Primary Accent (Deep Teal/Slate) - For main titles, general figures, and primary chart lines
TEAL_DEEP = "#164A4A" 
# Positive/Savings Accent (Vibrant Gold) - For high-value metrics, savings, and positive scheme segments
GOLD_VIBRANT = "#FFB703" 
# Neutral/General Metric Accent (Muted Green-Gray) - For member count, borrower count, and supporting metrics
MUTE_GREEN = "#6B8A7A" 
# Risk/Warning (Deep Red) - For Overdue and high-risk ratios
RED_DEEP = "#D90429" 

# --- 1. Custom CSS for Modern Dashboard Styling (Deep Teal & Gold Theme) ---
def inject_css():
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            
            html, body, [class*="st-Emotion-cache"] {{
                font-family: 'Inter', sans-serif;
            }}
            
            /* Main header styling */
            h1 {{
                font-size: 2.5rem;
                font-weight: 700;
                color: {TEAL_DEEP}; 
                margin-bottom: 0.5rem;
            }}
            
            /* Custom Card Styling for KPIs */
            .metric-card {{
                padding: 15px;
                border-radius: 12px;
                background-color: #ffffff;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                margin-bottom: 15px;
                border-left: 5px solid {TEAL_DEEP}; /* Deep Teal Accent */
                transition: transform 0.2s;
            }}
            .metric-card:hover {{
                transform: translateY(-3px);
                box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
            }}
            .metric-card h3 {{
                font-size: 1rem;
                color: #7f8c8d;
                margin-bottom: 0px;
            }}
            .metric-card p {{
                font-size: 1.8rem;
                font-weight: 600;
                color: #2c3e50;
            }}
            
            /* Section headers */
            h2, h3 {{
                color: {TEAL_DEEP}; /* Deep Teal Section Titles */
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 5px;
                margin-top: 1.5rem;
            }}
            
            /* Overriding default Streamlit Metric/Plotly style for consistency */
            div[data-testid="stMetric"] > div[data-testid="stRealValue"] {{
                font-size: 1.8rem;
            }}

            /* Container for charts */
            .chart-container {{
                padding: 20px;
                border-radius: 12px;
                background-color: #ffffff;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                margin-bottom: 20px;
            }}
        </style>
    """, unsafe_allow_html=True)

# Set page configuration
st.set_page_config(page_title="Microfinance Performance Dashboard", layout="wide", initial_sidebar_state="expanded")
inject_css()

# --- 2. Data Loading (Updated for CSV) ---
@st.cache_data
def load_data():
    # Use the known accessible file name
    file_path = "1025.csv"
    try:
        # The file is accessible in the context
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        
        # Ensure required numerical columns are present and numeric
        for col in ['Loan_Service_Charge', 'Overdue_Service_Charge', 'Overdue_Principal', 
                     'No_of_Samity', 'No_of_Members', 'No_of_Borrower',
                     'Total_Outstanding', 'Total_Overdue', 'Total_Savings_Balance', 
                     'SEP_2025_ Month_Loan', 'Loan_Outstanding_Principal', 'GS', 'SS', 'TSS', 'TDMB']:
            if col in df.columns:
                # Attempt to convert to numeric, coerce errors to NaN
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                # If column is missing, create it filled with zeros
                df[col] = 0
        
        return df
    except FileNotFoundError:
        st.error(f"Error: The file '{file_path}' was not found. Please ensure it is uploaded.")
        return None
    except Exception as e:
        st.error(f"Error loading the dataset: {str(e)}")
        return None

df = load_data()

if df is None:
    st.stop()

# Required columns check (Ensuring all are present for stability)
required_columns = [
    "Domain", "Zone", "Region", "Branch Name", "No_of_Samity", "No_of_Members",
    "No_of_Borrower", "SEP_2025_ Month_Loan", "Loan_Outstanding_Principal",
    "Total_Overdue", "Total_Outstanding", "Total_Savings_Balance",
    "GS", "SS", "TSS", "TDMB", "Loan_Service_Charge", "Overdue_Service_Charge",
    "Overdue_Principal"
]

missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    st.error(f"Error: The following required columns are missing: {', '.join(missing_columns)}")
    st.write("Available columns in the dataset:")
    st.write(df.columns.tolist())
    st.stop()

# --- 3. KPI Calculations ---
total_members = df["No_of_Members"].sum()
total_borrowers = df["No_of_Borrower"].sum()
total_loan_month = df["SEP_2025_ Month_Loan"].sum()
total_outstanding = df["Total_Outstanding"].sum()
total_overdue = df["Total_Overdue"].sum()
avg_loan_per_member = total_loan_month / total_members if total_members > 0 else 0
avg_overdue_ratio = (total_overdue / total_outstanding) * 100 if total_outstanding > 0 else 0
total_savings = df["Total_Savings_Balance"].sum()

# New Scheme Metrics
total_gs = df["GS"].sum()
total_ss = df["SS"].sum()
total_tss = df["TSS"].sum()
total_tdmb = df["TDMB"].sum()

# New Service Charge Metrics
total_loan_sc = df["Loan_Service_Charge"].sum()
total_overdue_sc = df["Overdue_Service_Charge"].sum()

# High-risk zone calculation
zone_risk = df.groupby("Zone").agg({"Total_Overdue": "sum", "Total_Outstanding": "sum"})
zone_risk["Overdue_Ratio"] = zone_risk.apply(lambda row: (row["Total_Overdue"] / row["Total_Outstanding"]) * 100 if row["Total_Outstanding"] > 0 else 0, axis=1)
high_risk_zones = len(zone_risk[zone_risk["Overdue_Ratio"] > 10]) # Zones with Overdue Ratio > 10%
top_zone_loan = df.groupby("Zone")["SEP_2025_ Month_Loan"].sum().idxmax()

# --- 4. Dashboard Title and Sidebar Filters ---
st.title("Consolitidated Balancing Domain - Zone Performance Dashboard")
st.markdown("A deep dive into key financial, operational, and scheme-specific metrics across domains and zones.")

# Sidebar Filters
st.sidebar.header("Filter Data")
selected_domain = st.sidebar.multiselect("Select Domain", options=df["Domain"].unique(), default=df["Domain"].unique())
selected_zone = st.sidebar.multiselect("Select Zone", options=df["Zone"].unique(), default=df["Zone"].unique())

# Filter Data
filtered_df = df[
    (df["Domain"].isin(selected_domain)) &
    (df["Zone"].isin(selected_zone))
]

# Recalculate KPIs based on filtered data for accurate display
if not filtered_df.empty:
    total_members = filtered_df["No_of_Members"].sum()
    total_borrowers = filtered_df["No_of_Borrower"].sum()
    total_loan_month = filtered_df["SEP_2025_ Month_Loan"].sum()
    total_outstanding = filtered_df["Total_Outstanding"].sum()
    total_overdue = filtered_df["Total_Overdue"].sum()
    total_savings = filtered_df["Total_Savings_Balance"].sum()
    total_gs = filtered_df["GS"].sum()
    total_ss = filtered_df["SS"].sum()
    total_tss = filtered_df["TSS"].sum()
    total_tdmb = filtered_df["TDMB"].sum()
    
    avg_loan_per_member = total_loan_month / total_members if total_members > 0 else 0
    avg_overdue_ratio = (total_overdue / total_outstanding) * 100 if total_outstanding > 0 else 0
    
    zone_risk_filtered = filtered_df.groupby("Zone").agg({"Total_Overdue": "sum", "Total_Outstanding": "sum"})
    zone_risk_filtered["Overdue_Ratio"] = zone_risk_filtered.apply(lambda row: (row["Total_Overdue"] / row["Total_Outstanding"]) * 100 if row["Total_Outstanding"] > 0 else 0, axis=1)
    high_risk_zones = len(zone_risk_filtered[zone_risk_filtered["Overdue_Ratio"] > 10])
    top_zone_loan = filtered_df.groupby("Zone")["SEP_2025_ Month_Loan"].sum().idxmax()
else:
    # Set to zero if filtered data is empty
    total_members = total_borrowers = total_loan_month = total_outstanding = 0
    total_overdue = total_savings = total_gs = total_ss = total_tss = total_tdmb = 0
    avg_loan_per_member = avg_overdue_ratio = 0
    high_risk_zones = 0
    top_zone_loan = "N/A"


# --- 5. Custom Metric Function (Updated Colors) ---
def custom_metric(label, value, icon, color=TEAL_DEEP):
    # Fix: Explicitly handle the string metric (Top Zone by Loan) to avoid formatting errors
    if label == "Top Zone by Loan":
        formatted_value = str(value)
    # Formatting for currency values (Displaying full amount without k/M/B suffixes)
    elif label.startswith(("Total Loan", "Total Savings", "Total GS", "Total SS", "Total TSS", "Total TDMB", "Avg Loan", "Total Service Charge", "Total Outstanding", "Total Overdue")):
        formatted_value = f"{value:,.0f}" 
    # General numeric formatting (for members, borrowers, etc.)
    else:
        formatted_value = f"{value:,}"
        
    # Overwrite if it's a ratio (with two decimal places and a percent sign)
    if "Ratio" in label and label != "Top Zone by Loan":
        formatted_value = f"{value:,.2f}%"

    st.markdown(f"""
        <div class="metric-card" style="border-left: 5px solid {color};">
            <h3>{label}</h3>
            <p><span style='font-size: 1.5rem; margin-right: 10px;'>{icon}</span>{formatted_value}</p>
        </div>
    """, unsafe_allow_html=True)


# --- 6. KPIs Display (New Color Map) ---
st.header("Financial & Operational Key Performance Indicators")

# Row 1: Core Totals
col1, col2, col3, col4 = st.columns(4)
with col1:
    custom_metric("Total Members Sum", total_members, "👥", MUTE_GREEN)
with col2:
    custom_metric("Total Borrowers Sum", total_borrowers, "👤", MUTE_GREEN)
with col3:
    custom_metric("Total Loan (SEP '25)", total_loan_month, "💸", TEAL_DEEP)
with col4:
    custom_metric("Total Savings Balance", total_savings, "💰", GOLD_VIBRANT) # Key positive metric

# Row 2: Performance Metrics & Service Charges
col5, col6, col7, col8 = st.columns(4)
with col5:
    custom_metric("Total Outstanding", total_outstanding, "🏦", TEAL_DEEP)
with col6:
    custom_metric("Total Overdue", total_overdue, "🔻", RED_DEEP)
with col7:
    custom_metric("Avg Loan / Member", avg_loan_per_member, "📈", TEAL_DEEP)
with col8:
    custom_metric("Total Overdue Ratio", avg_overdue_ratio, "🚨", RED_DEEP)
    
# Row 3: Scheme Metrics & Risk
st.markdown("---")
st.header("Saving Scheme-Specific Metrics (Total Balance)")
col9, col10, col11, col12 = st.columns(4)
with col9:
    custom_metric("Total GS", total_gs, "✅", GOLD_VIBRANT)
with col10:
    custom_metric("Total SS", total_ss, "✅", MUTE_GREEN)
with col11:
    custom_metric("Total TSS", total_tss, "✅", MUTE_GREEN)
with col12:
    custom_metric("Total TDMB", total_tdmb, "✅", MUTE_GREEN)
st.markdown("---")
st.header("Operational Risk")
col13, col14 = st.columns(2)
with col13:
    custom_metric("High-Risk Zones (>10%)", high_risk_zones, "⚠️", RED_DEEP)
with col14:
    custom_metric("Top Zone by Loan", top_zone_loan, "🏆", TEAL_DEEP)


# --- 7. Main Visualizations (Domain Focus) ---
st.header("Domain-Level Performance Analysis")

main_chart_col1, main_chart_col2 = st.columns([0.5, 0.5])

# Column 1 (0.5 width) - Total Loan by Domain BAR Chart (Vertical)
with main_chart_col1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("Total Monthly Loan Amount by Domain")
    domain_loan = filtered_df.groupby("Domain")["SEP_2025_ Month_Loan"].sum().reset_index().sort_values("SEP_2025_ Month_Loan", ascending=False)
    
    # Vertical Bar Chart using a deep teal sequential scale
    fig_loan_bar = px.bar(
        domain_loan, 
        x="Domain", # X-axis is Domain
        y="SEP_2025_ Month_Loan", # Y-axis is Amount
        title="Total Loan Amount Disbursed (SEP '25)",
        color="SEP_2025_ Month_Loan",
        color_continuous_scale=px.colors.sequential.Teal, # Keep a deep teal color
    )
    
    fig_loan_bar.update_layout(
        xaxis_title="Domain", 
        yaxis_title="Total Loan Amount", 
        template="plotly_white",
        margin=dict(t=40, b=40, l=0, r=0),
        uniformtext_minsize=8, 
        uniformtext_mode='hide',
        yaxis=dict(tickformat=","), # Ensure Y-axis ticks show full numbers
    )
    
    # Ensure full number formatting for hover and text labels
    fig_loan_bar.update_traces(
        marker_line_width=0, 
        hovertemplate="Domain: %{x}<br>Amount: %{y:,.0f}<extra></extra>",
        # Add text labels on the bars showing full amount
        text=domain_loan["SEP_2025_ Month_Loan"].apply(lambda x: f"{x:,.0f}"),
        textposition='outside'
    )
    
    st.plotly_chart(fig_loan_bar, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Column 2 (0.5 width) - Member vs. Borrower Count by Domain (Horizontal Grouped Bar Chart)
with main_chart_col2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("Member vs. Borrower Count by Domain")
    
    domain_member_borrower = filtered_df.groupby("Domain").agg({
        "No_of_Members": "sum",
        "No_of_Borrower": "sum"
    }).reset_index().sort_values("No_of_Members", ascending=False)
    
    domain_melted = domain_member_borrower.melt(
        id_vars="Domain", 
        value_vars=["No_of_Members", "No_of_Borrower"], 
        var_name="Metric", 
        value_name="Count"
    )

    fig_grouped_bar = px.bar(
        domain_melted, 
        x="Count", 
        y="Domain", 
        color="Metric",
        orientation='h',
        barmode='group',
        title="Comparative Member and Borrower Counts",
        color_discrete_map={
            'No_of_Members': TEAL_DEEP, # Deep Teal
            'No_of_Borrower': MUTE_GREEN # Muted Green
        }
    )
    
    fig_grouped_bar.update_layout(
        xaxis_title="Count of People", 
        yaxis_title="Domain",
        template="plotly_white",
        legend_title_text='Category',
        margin=dict(t=40, b=40, l=0, r=0),
        legend=dict(orientation="h", y=-0.1, x=0.5, xanchor='center')
    )
    fig_grouped_bar.update_traces(marker_line_width=0, hovertemplate="Count: %{x:,}<extra></extra>")
    
    st.plotly_chart(fig_grouped_bar, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
# --- 8. Operational Reach Analysis (Samity, Member, Borrower) ---
st.markdown("---")
st.header("Operational Reach Analysis")
st.markdown("Visualizing the organizational structure and penetration: Number of Samity, total Members, and total Borrowers per Domain.")

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.subheader("Samity, Member, and Borrower Count by Domain")

# 1. Aggregate Samity/Member/Borrower data by domain
domain_reach_agg = filtered_df.groupby("Domain").agg({
    "No_of_Samity": "sum",
    "No_of_Members": "sum",
    "No_of_Borrower": "sum"
}).reset_index().sort_values("No_of_Members", ascending=False)

# 2. Melt the DataFrame for grouped bar chart
domain_reach_melted = domain_reach_agg.melt(
    id_vars="Domain", 
    value_vars=["No_of_Samity", "No_of_Members", "No_of_Borrower"], 
    var_name="Operational Metric", 
    value_name="Count"
)

# 3. Create the Grouped Bar Chart
fig_reach_grouped = px.bar(
    domain_reach_melted, 
    x="Domain", 
    y="Count", 
    color="Operational Metric",
    barmode='group',
    title="Comparative Operational Reach (Samity, Member, Borrower)",
    color_discrete_map={
        'No_of_Samity': TEAL_DEEP,    
        'No_of_Members': GOLD_VIBRANT,   # Gold for highlighting members
        'No_of_Borrower': MUTE_GREEN   
    }
)

# 4. Update layout and formatting
fig_reach_grouped.update_layout(
    xaxis_title="Domain", 
    yaxis_title="Count", 
    template="plotly_white",
    margin=dict(t=40, b=40, l=0, r=0),
    yaxis=dict(tickformat=","),
    legend=dict(orientation="h", y=-0.2, x=0.5, xanchor='center')
)

fig_reach_grouped.update_traces(
    # Full number formatting: {y:,.0f}
    hovertemplate="Domain: %{x}<br>Metric: %{fullData.name}<br>Count: %{y:,.0f}<extra></extra>"
)

st.plotly_chart(fig_reach_grouped, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)
# --- End Operational Reach Analysis Section ---


# --- 9. Total Scheme Distribution ---

st.header("Aggregate Financial Scheme Distribution")
st.markdown("This chart shows the overall contribution of each scheme type (`GS`, `SS`, `TSS`, `TDMB`) to the total scheme portfolio.")

st.markdown('<div class="chart-container">', unsafe_allow_html=True)

scheme_totals = pd.DataFrame({
    'Scheme Type': ['GS', 'SS', 'TSS', 'TDMB'],
    'Total Amount': [total_gs, total_ss, total_tss, total_tdmb]
})

# Use a qualitative palette that includes the Gold and Teal accents
scheme_colors = [GOLD_VIBRANT, TEAL_DEEP, MUTE_GREEN, RED_DEEP]

fig_scheme_total = px.pie(
    scheme_totals, names='Scheme Type', values='Total Amount',
    title="Overall Distribution of Scheme Balances (GS, SS, TSS, TDMB)",
    color='Scheme Type',
    color_discrete_map={
        'GS': GOLD_VIBRANT, 
        'SS': TEAL_DEEP, 
        'TSS': MUTE_GREEN, 
        'TDMB': RED_DEEP
    }, 
    hole=0.5
)

fig_scheme_total.update_traces(
    textinfo='label+percent', 
    marker=dict(line=dict(color='#FAFAFA', width=2)),
    pull=[0.02] * len(scheme_totals),
    # Full number formatting: {value:,}
    hovertemplate="Scheme: %{label}<br>Amount: %{value:,.0f}<br>Percentage: %{percent}<extra></extra>"
)

fig_scheme_total.update_layout(
    title_font_size=18,
    legend=dict(orientation="h", y=-0.1, x=0.5, xanchor='center'), 
    margin=dict(t=40, b=40, l=0, r=0),
    template="plotly_white"
)

st.plotly_chart(fig_scheme_total, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


# --- 10. Branch Savings Performance (NEW SECTION) ---
st.markdown("---")
st.header("Branch Savings Performance")
st.markdown("Branches ranked by the total accumulated savings balance.")

st.markdown('<div class="chart-container">', unsafe_allow_html=True)

# 1. Aggregate and rank data
branch_savings_ranking = filtered_df.groupby("Branch Name")["Total_Savings_Balance"].sum().reset_index()
# Take top 25 and sort ascending for the horizontal chart to display largest at the top
top_25_savings_branches = branch_savings_ranking.nlargest(25, "Total_Savings_Balance").sort_values("Total_Savings_Balance", ascending=True) 

# 2. Create Horizontal Bar Chart (Using a Gold Sequential Scale)
fig_top_25_savings = px.bar(
    top_25_savings_branches,
    x="Total_Savings_Balance", 
    y="Branch Name", 
    orientation='h', # Horizontal chart
    title="Top 25 Branches by Total Savings Balance",
    color="Total_Savings_Balance",
    color_continuous_scale=px.colors.sequential.YlOrBr # A rich gold/brown scale
)

# 3. Update layout and formatting (full numbers)
fig_top_25_savings.update_layout(
    xaxis_title='Total Savings Balance', 
    yaxis_title='Branch Name',
    template="plotly_white",
    margin=dict(t=40, b=40, l=0, r=0),
    yaxis={'categoryorder':'total ascending'}, 
    xaxis=dict(tickformat=","),
    coloraxis_showscale=False
)

fig_top_25_savings.update_traces(
    # Add text labels on the bars showing full amount
    text=top_25_savings_branches["Total_Savings_Balance"].apply(lambda x: f"{x:,.0f}"),
    textposition='outside',
    hovertemplate="Branch: %{y}<br>Amount: %{x:,.0f}<extra></extra>"
)

st.plotly_chart(fig_top_25_savings, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)
# --- End Branch Savings Performance ---


# --- 11. Financial Stability & Scheme Analysis ---
st.header("In-Depth Financial and Scheme Analysis by Domain")

# --- Plot 1: Outstanding vs. Savings Grouped Bar Chart (Financial Health) ---
st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.subheader("Comparative Loan Outstanding vs. Savings Balance by Domain")

# 1. Aggregate data 
domain_agg_financial = filtered_df.groupby('Domain').agg({
    'Loan_Outstanding_Principal': 'sum',
    'Total_Savings_Balance': 'sum',
}).reset_index()

# 2. Melt the DataFrame for grouped bar chart
domain_melted_bar = domain_agg_financial.melt(
    id_vars='Domain', 
    value_vars=['Loan_Outstanding_Principal', 'Total_Savings_Balance'], 
    var_name='Financial Metric', 
    value_name='Amount'
)

# 3. Create the Grouped Bar Chart
fig_grouped_financial = px.bar(
    domain_melted_bar,
    x='Domain', 
    y='Amount', 
    color='Financial Metric',
    barmode='group', # Key change for side-by-side bars
    title='Comparative Financial Health: Outstanding Debt vs. Member Savings',
    color_discrete_map={
        'Loan_Outstanding_Principal': TEAL_DEEP,         # Deep Teal
        'Total_Savings_Balance': GOLD_VIBRANT           # Gold for Health
    }
)

# 4. Update layout and formatting (full numbers)
fig_grouped_financial.update_layout(
    xaxis_title='Domain', 
    yaxis_title='Total Amount',
    template="plotly_white",
    margin=dict(t=40, b=40, l=0, r=0),
    yaxis=dict(tickformat=","), # Ensure Y-axis ticks show full numbers
    legend=dict(orientation="h", y=-0.2, x=0.5, xanchor='center')
)

fig_grouped_financial.update_traces(
    # Full number formatting: {y:,.0f}
    hovertemplate="Domain: %{x}<br>Metric: %{fullData.name}<br>Amount: %{y:,.0f}<extra></extra>"
)

st.plotly_chart(fig_grouped_financial, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- Plot 2: Scheme Distribution by Domain (Stacked Bar Chart) ---
st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.subheader("Scheme Portfolio Distribution by Domain")

# Aggregate scheme data by domain
scheme_domain_agg = filtered_df.groupby('Domain')[['GS', 'SS', 'TSS', 'TDMB']].sum().reset_index()

# Melt the DataFrame for Plotly stacked bar chart
scheme_domain_melted = scheme_domain_agg.melt(
    id_vars='Domain', 
    value_vars=['GS', 'SS', 'TSS', 'TDMB'],
    var_name='Scheme Type',
    value_name='Amount'
)

# Use the new color map for the stacked chart
fig_scheme_stacked = px.bar(
    scheme_domain_melted, 
    x='Domain', 
    y='Amount', 
    color='Scheme Type',
    title='Scheme Balances (GS, SS, TSS, TDMB) by Domain',
    barmode='stack',
    color_discrete_map={
        'GS': GOLD_VIBRANT, 
        'SS': TEAL_DEEP, 
        'TSS': MUTE_GREEN, 
        'TDMB': RED_DEEP
    }
)

fig_scheme_stacked.update_layout(
    xaxis_title='Domain',
    yaxis_title='Total Scheme Amount',
    template="plotly_white",
    margin=dict(t=40, b=40, l=0, r=0),
    legend_title_text='Scheme Type',
    yaxis=dict(tickformat=",") # Ensure Y-axis ticks show full numbers
)
# Full number formatting: {y:,.0f}
fig_scheme_stacked.update_traces(hovertemplate="Domain: %{x}<br>Scheme Type: %{fullData.name}<br>Amount: %{y:,.0f}<extra></extra>")

st.plotly_chart(fig_scheme_stacked, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


# --- 12. Service Charge Analysis ---
st.header("Service Charge Analysis")

st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.subheader("Comparison of Loan vs. Overdue Service Charges by Domain")

# Aggregate Service Charge data by domain
sc_domain_agg = filtered_df.groupby('Domain').agg({
    'Loan_Service_Charge': 'sum',
    'Overdue_Service_Charge': 'sum'
}).reset_index()

# Melt for grouped bar chart
sc_melted = sc_domain_agg.melt(
    id_vars='Domain',
    value_vars=['Loan_Service_Charge', 'Overdue_Service_Charge'],
    var_name='Charge Type',
    value_name='Total Charge Amount'
)

fig_sc_grouped = px.bar(
    sc_melted,
    x='Domain',
    y='Total Charge Amount',
    color='Charge Type',
    barmode='group',
    title='Revenue Quality: Loan Service Charges vs. Overdue Charges',
    color_discrete_map={
        'Loan_Service_Charge': GOLD_VIBRANT, # Gold for healthy revenue
        'Overdue_Service_Charge': RED_DEEP # Red for risky revenue
    }
)

fig_sc_grouped.update_layout(
    xaxis_title='Domain',
    yaxis_title='Total Service Charge',
    template="plotly_white",
    margin=dict(t=40, b=40, l=0, r=0),
    legend_title_text='Charge Type',
    yaxis=dict(tickformat=",") # Ensure Y-axis ticks show full numbers
)
# Full number formatting: {y:,.0f}
fig_sc_grouped.update_traces(hovertemplate="Domain: %{x}<br>Charge Type: %{fullData.name}<br>Amount: %{y:,.0f}<extra></extra>")

st.plotly_chart(fig_sc_grouped, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


# --- 13. Risk Profile: Outstanding and Overdue Analysis ---
st.markdown("---")
st.header("Risk Profile: Outstanding and Overdue Analysis")
risk_col1, risk_col2 = st.columns(2)

# --- Plot 1: Outstanding vs Overdue by Domain (Grouped Bar) ---
with risk_col1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("Total Outstanding vs. Total Overdue by Domain")

    # Aggregate data for Outstanding and Overdue by Domain
    risk_domain_agg = filtered_df.groupby('Domain').agg({
        'Total_Outstanding': 'sum',
        'Total_Overdue': 'sum'
    }).reset_index().sort_values("Total_Outstanding", ascending=False)

    risk_domain_melted = risk_domain_agg.melt(
        id_vars='Domain', 
        value_vars=['Total_Outstanding', 'Total_Overdue'], 
        var_name='Financial Status', 
        value_name='Amount'
    )

    fig_risk_grouped = px.bar(
        risk_domain_melted,
        x='Domain', 
        y='Amount', 
        color='Financial Status',
        barmode='group',
        title='Magnitude of Total Outstanding vs. Total Overdue',
        color_discrete_map={
            'Total_Outstanding': TEAL_DEEP, # Deep Teal
            'Total_Overdue': RED_DEEP      # Deep Red for risk
        }
    )

    fig_risk_grouped.update_layout(
        xaxis_title='Domain', 
        yaxis_title='Total Amount',
        template="plotly_white",
        margin=dict(t=40, b=40, l=0, r=0),
        yaxis=dict(tickformat=","),
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor='center')
    )
    fig_risk_grouped.update_traces(hovertemplate="Domain: %{x}<br>Metric: %{fullData.name}<br>Amount: %{y:,.0f}<extra></extra>")
    
    st.plotly_chart(fig_risk_grouped, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# --- Plot 2: Overdue Ratio by Zone (Horizontal Bar) ---
with risk_col2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("Top 15 Zones by Overdue Ratio")

    # Aggregate data for Overdue Ratio by Zone
    zone_overdue_ratio = filtered_df.groupby('Zone').agg({
        'Total_Outstanding': 'sum',
        'Total_Overdue': 'sum'
    }).reset_index()

    zone_overdue_ratio['Overdue_Ratio'] = zone_overdue_ratio.apply(
        lambda row: (row['Total_Overdue'] / row['Total_Outstanding']) * 100 
        if row['Total_Outstanding'] > 0 else 0, 
        axis=1
    )

    # Select top 15 highest risk zones and sort ascending for visualization
    top_15_risk_zones = zone_overdue_ratio.nlargest(15, 'Overdue_Ratio').sort_values('Overdue_Ratio', ascending=True)

    # Use a Deep Red sequential scale
    fig_risk_zone = px.bar(
        top_15_risk_zones,
        x='Overdue_Ratio', 
        y='Zone', 
        orientation='h',
        title='Zones Ranked by % of Outstanding Loans Overdue',
        color='Overdue_Ratio',
        color_continuous_scale=px.colors.sequential.Reds
    )

    fig_risk_zone.update_layout(
        xaxis_title='Overdue Ratio (%)', 
        yaxis_title='Zone',
        template="plotly_white",
        margin=dict(t=40, b=40, l=0, r=0),
        yaxis={'categoryorder':'total ascending'},
        coloraxis_showscale=False
    )
    fig_risk_zone.update_traces(
        text=top_15_risk_zones['Overdue_Ratio'].apply(lambda x: f"{x:,.2f}%"),
        textposition='outside',
        hovertemplate="Zone: %{y}<br>Ratio: %{x:,.2f}%<extra></extra>"
    )
    
    st.plotly_chart(fig_risk_zone, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
# --- End Risk Profile Analysis ---


# --- 14. Top 25 Branch Loan Performance ---
st.markdown("---")
st.header("Top 25 Branch Loan Performance")
st.markdown("Branches are ranked by their total loan disbursement amount for SEP 2025.")

st.markdown('<div class="chart-container">', unsafe_allow_html=True)

# 1. Aggregate and rank data
branch_loan_ranking = filtered_df.groupby("Branch Name")["SEP_2025_ Month_Loan"].sum().reset_index()
# Take top 25 and sort ascending for the horizontal chart to display largest at the top
top_25_branches = branch_loan_ranking.nlargest(25, "SEP_2025_ Month_Loan").sort_values("SEP_2025_ Month_Loan", ascending=True) 

# 2. Create Horizontal Bar Chart (Using a Deep Teal Sequential Scale)
fig_top_25 = px.bar(
    top_25_branches,
    x="SEP_2025_ Month_Loan", 
    y="Branch Name", 
    orientation='h', # Horizontal chart
    title="Top 25 Branches by SEP '25 Monthly Loan Disbursement",
    color="SEP_2025_ Month_Loan",
    color_continuous_scale=px.colors.sequential.Tealgrn # Deep teal/green scale
)

# 3. Update layout and formatting (full numbers)
fig_top_25.update_layout(
    xaxis_title='Total Loan Amount', 
    yaxis_title='Branch Name',
    template="plotly_white",
    margin=dict(t=40, b=40, l=0, r=0),
    yaxis={'categoryorder':'total ascending'}, # Important for horizontal bar order
    xaxis=dict(tickformat=","),
    coloraxis_showscale=False
)

fig_top_25.update_traces(
    # Add text labels on the bars showing full amount
    text=top_25_branches["SEP_2025_ Month_Loan"].apply(lambda x: f"{x:,.0f}"),
    textposition='outside',
    hovertemplate="Branch: %{y}<br>Amount: %{x:,.0f}<extra></extra>"
)

st.plotly_chart(fig_top_25, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


# --- 15. Risk and Efficiency Ratios ---
st.markdown("---")
st.header("Risk and Efficiency Ratios")
ratio_col1, ratio_col2 = st.columns(2)

# Calculation for ratios
ratio_domain = filtered_df.groupby('Domain').agg({
    'Loan_Outstanding_Principal': 'sum',
    'SEP_2025_ Month_Loan': 'sum'
}).reset_index()
ratio_domain['Ratio'] = ratio_domain.apply(lambda row: row['Loan_Outstanding_Principal'] / row['SEP_2025_ Month_Loan'] if row['SEP_2025_ Month_Loan'] > 0 else 0, axis=1)
ratio_domain = ratio_domain[['Domain','Ratio']].sort_values('Ratio', ascending=False)

ratio_zone = filtered_df.groupby('Zone').agg({
    'Loan_Outstanding_Principal': 'sum',
    'SEP_2025_ Month_Loan': 'sum'
}).reset_index()
ratio_zone['Ratio'] = ratio_zone.apply(lambda row: row['Loan_Outstanding_Principal'] / row['SEP_2025_ Month_Loan'] if row['SEP_2025_ Month_Loan'] > 0 else 0, axis=1)
ratio_zone = ratio_zone[['Zone','Ratio']].sort_values('Ratio', ascending=False).nlargest(15, "Ratio") 

with ratio_col1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("Outstanding / Loan Ratio by Domain")
    # Using 'Teal' scale
    fig_dom = px.bar(
        ratio_domain, 
        x='Ratio', y='Domain', orientation='h',
        text=ratio_domain['Ratio'].apply(lambda x: f"{x:,.2f}"),
        color='Ratio',
        color_continuous_scale=px.colors.sequential.Teal # CORRECTED SCALE
    )
    fig_dom.update_traces(marker_line_width=0, textposition='outside', hovertemplate="Ratio: %{x:,.2f}<extra></extra>")
    fig_dom.update_layout(
        xaxis_title='Outstanding / Monthly Loan Ratio',
        yaxis_title='Domain',
        template="plotly_white",
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_dom, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


with ratio_col2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("Top 15 Zones by Outstanding / Loan Ratio")
    # Using 'Plotly3' scale
    fig_zone = px.bar(
        ratio_zone, 
        x='Ratio', y='Zone', orientation='h',
        text=ratio_zone['Ratio'].apply(lambda x: f"{x:,.2f}"),
        color='Ratio',
        color_continuous_scale=px.colors.sequential.Plotly3
    )
    fig_zone.update_traces(marker_line_width=0, textposition='outside', hovertemplate="Ratio: %{x:,.2f}<extra></extra>")
    fig_zone.update_layout(
        xaxis_title='Outstanding / Monthly Loan Ratio',
        yaxis_title='Zone',
        template="plotly_white",
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_zone, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# --- 16. Detailed Table and Export (COMPLETED SECTION) ---
zone_summary = filtered_df.groupby("Zone").agg({
    "No_of_Samity": "sum",
    "No_of_Members": "sum",
    "No_of_Borrower": "sum",
    "SEP_2025_ Month_Loan": "sum",
    "Total_Savings_Balance": "sum",
    "Total_Overdue": "sum",
    "Total_Outstanding": "sum",
    "GS": "sum", 
    "SS": "sum",
    "TSS": "sum",
    "TDMB": "sum",
    "Loan_Service_Charge": "sum",
    "Overdue_Service_Charge": "sum",
    "Overdue_Principal": "sum",
}).reset_index()

zone_summary["Overdue_Ratio"] = zone_summary.apply(lambda row: (row["Total_Overdue"] / row["Total_Outstanding"]) * 100 if row["Total_Outstanding"] > 0 else 0, axis=1)

st.header("Zone Performance Summary Table")
# Completed formatting dictionary and st.dataframe call
st.dataframe(zone_summary.sort_values("No_of_Members", ascending=False).style.format({
    "SEP_2025_ Month_Loan": "{:,.0f}",
    "Total_Savings_Balance": "{:,.0f}",
    "Total_Overdue": "{:,.0f}",
    "Total_Outstanding": "{:,.0f}",
    "GS": "{:,.0f}",
    "SS": "{:,.0f}",
    "TSS": "{:,.0f}",
    "TDMB": "{:,.0f}",
    "Loan_Service_Charge": "{:,.0f}",
    "Overdue_Service_Charge": "{:,.0f}",
    "Overdue_Principal": "{:,.0f}",
    "Overdue_Ratio": "{:,.2f}%"
}), use_container_width=True)


# Export Button for the summary data
@st.cache_data
def convert_df_to_csv(df):
    # IMPORTANT: Do not include the styling/formatting, just the raw data for export
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df_to_csv(zone_summary)


