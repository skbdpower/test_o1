# app.py  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------------- Page Config ----------------------
st.set_page_config(page_title="Loan Adjustment – Nov 2025", layout="wide")

# ---------------------- Load Data ----------------------
@st.cache_data
def load_data():
    df = pd.read_excel("ADJ_NOV_2025.xlsx", sheet_name="Loan_Adjustment_Register_Report")
    
    # Fix column names
    df.columns = [
        'Divisional', 'Zone', 'Regions', 'Branch', 'Number_Of_Member',
        'Adjustment_Principle_Amount', 'Adjustment_Service_Charge', 'Adjustment_Total'
    ]
    
    # Convert to numbers
    num_cols = ['Number_Of_Member', 'Adjustment_Principle_Amount',
                'Adjustment_Service_Charge', 'Adjustment_Total']
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors='coerce')
    df = df.fillna(0)
    return df

df = load_data()

# ---------------------- Accurate Calculations ----------------------
total_branches   = len(df)
total_members     = df['Number_Of_Member'].sum()
total_principal   = df['Adjustment_Principle_Amount'].sum()
total_service     = df['Adjustment_Service_Charge'].sum()
grand_total       = df['Adjustment_Total'].sum()

total_principal_full = f"{total_principal:.0f}"
total_service_full   = f"{total_service:.0f}"
grand_total_full     = f"{grand_total:.0f}"

avg_per_member = grand_total / total_members
avg_per_branch = grand_total / total_branches

# Divisional summary
div_summary = df.groupby('Divisional').agg({
    'Number_Of_Member': 'sum',
    'Adjustment_Principle_Amount': 'sum',
    'Adjustment_Service_Charge': 'sum',
    'Adjustment_Total': 'sum'
}).round(2).reset_index()

div_summary['Avg_per_Member'] = (div_summary['Adjustment_Total'] / div_summary['Number_Of_Member']).round(0)

# ---------------------- Dashboard ----------------------
st.title("Loan Adjustment Register – November 2025")
#st.markdown("### Full & Accurate Values")

# KPI Cards
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Branches", f"{total_branches:,}")
col2.metric("Members Adjusted", f"{total_members:,}")
col3.metric("Principal", total_principal_full)
col4.metric("Service Charge", total_service_full)
col5.metric("Grand Total", grand_total_full, delta="Nov 2025")

st.markdown("---")

# 4 Divisional Charts (UPDATED: Increased spacing, new color scheme, modern style)
st.subheader("Divisional Performance")

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Number of Members",
        "Principal Amount",
        "Service Charge ",
        "Total Adjustment "
    ),
    vertical_spacing=0.25,  # UPDATED: Further increased vertical spacing
    horizontal_spacing=0.20,  # UPDATED: Further increased horizontal spacing
    specs=[[{"type": "bar"}, {"type": "bar"}],
          [{"type": "bar"}, {"type": "bar"}]]
)

# UPDATED: New modern color palette (softer, professional)
colors = ['#4C78A8', '#F58518', '#E45756', '#72B7A1']  # Blue, Orange, Red, Teal

# Members
fig.add_trace(go.Bar(
    x=div_summary['Divisional'],
    y=div_summary['Number_Of_Member'],
    text=div_summary['Number_Of_Member'].apply(lambda x: f"{int(x):,}"),
    textposition='outside',
    marker_color=colors[0],
    marker_line_color='white',
    marker_line_width=2  # UPDATED: Added borders for style
), row=1, col=1)

# Principal
fig.add_trace(go.Bar(
    x=div_summary['Divisional'],
    y=div_summary['Adjustment_Principle_Amount'],
    text=div_summary['Adjustment_Principle_Amount'].apply(lambda x: f"{x:,.2f}"),
    textposition='outside',
    marker_color=colors[1],
    marker_line_color='white',
    marker_line_width=2
), row=1, col=2)

# Service Charge
fig.add_trace(go.Bar(
    x=div_summary['Divisional'],
    y=div_summary['Adjustment_Service_Charge'],
    text=div_summary['Adjustment_Service_Charge'].apply(lambda x: f"{x:,.2f}"),
    textposition='outside',
    marker_color=colors[2],
    marker_line_color='white',
    marker_line_width=2
), row=2, col=1)

# Total
fig.add_trace(go.Bar(
    x=div_summary['Divisional'],
    y=div_summary['Adjustment_Total'],
    text=div_summary['Adjustment_Total'].apply(lambda x: f"{x:,.2f}"),
    textposition='outside',
    marker_color=colors[3],
    marker_line_color='white',
    marker_line_width=2
), row=2, col=2)

# UPDATED: Modern layout style
fig.update_layout(
    height=1000,  # Increased height for better spacing
    showlegend=False,
    plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Arial", size=12)
)
fig.update_xaxes(tickangle=45, gridcolor='lightgray')
fig.update_yaxes(gridcolor='lightgray')
st.plotly_chart(fig, use_container_width=True)

# Treemap (UPDATED: Enhanced style with new colors)
st.subheader("Share of Total Adjustment by Division")
fig_tree = px.treemap(
    div_summary,
    path=['Divisional'],
    values='Adjustment_Total',
    color='Adjustment_Total',
    color_continuous_scale='bluered',  # UPDATED: Changed to bluered scale
    title="Division-wise Contribution"
)
fig_tree.update_traces(
    textinfo="label+value",
    hovertemplate='<b>%{label}</b><br>Total: %{value:,.2f}<extra></extra>',
    marker_line_color='white',
    marker_line_width=2  # UPDATED: Added borders
)
fig_tree.update_layout(
    font=dict(family="Arial", size=12)
)
st.plotly_chart(fig_tree, use_container_width=True)

# Efficiency (UPDATED: New style with lollipop or enhanced bar)
st.subheader("Average Adjustment per Member by Division")
fig_eff = px.bar(
    div_summary.sort_values('Avg_per_Member', ascending=False),
    x='Divisional',
    y='Avg_per_Member',
    text='Avg_per_Member',
    color='Avg_per_Member',
    color_continuous_scale='viridis',  # UPDATED: Kept but can change to 'plasma'
    title="Which Division Gets Highest per Member Adjustment?"
)
fig_eff.update_traces(
    texttemplate='%{text:,.0f}',
    marker_line_color='white',
    marker_line_width=2
)
fig_eff.update_layout(
    xaxis_tickangle=45,
    yaxis_title="Average per Member",
    font=dict(family="Arial", size=12)
)
st.plotly_chart(fig_eff, use_container_width=True)

# Top 20 Branches (UPDATED: Horizontal bar with new colors)
st.subheader("Top 20 Branches – November 2025")
top20 = df.nlargest(20, 'Adjustment_Total').copy()

fig_top = px.bar(
    top20,
    y='Branch',
    x='Adjustment_Total',
    orientation='h',
    text=top20['Adjustment_Total'].apply(lambda x: f"{x:,.2f}"),
    color='Number_Of_Member',
    color_continuous_scale='plasma',  # UPDATED: Changed to plasma
    title="Champion Branches"
)
fig_top.update_traces(
    marker_line_color='white',
    marker_line_width=1
)
fig_top.update_layout(
    height=800,  # Increased height
    yaxis={'categoryorder':'total ascending'},
    font=dict(family="Arial", size=10),
    plot_bgcolor='rgba(0,0,0,0)'
)
st.plotly_chart(fig_top, use_container_width=True)
