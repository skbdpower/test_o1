import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# --- 1. CONFIGURATION AND DATA LOADING ---
DATA_FILE = "Pomis_Summary_Report_Oct_2025.xlsx"
TOP_N_BRANCHES = 25

def load_data():
    """Loads and preprocesses the POMIS summary data, and performs feature engineering."""
    try:
        # NOTE: Using the accessible CSV data provided in the environment for demonstration
        # In a real Streamlit app, this would correctly load the .xlsx file.
        df = pd.read_excel("Pomis_Summary_Report_Oct_2025.xlsx")
    except FileNotFoundError:
        st.error(f"Error: The file '{DATA_FILE}' was not found. Please ensure the CSV is in the same directory as the script.")
        st.stop()
    except Exception as e:
        st.error(f"An unexpected error occurred during data loading: {e}")
        st.stop()


    # Monetary and Count columns to clean
    cols_to_clean = [
        'New_Member_Admission_Oct', 'Member_Cancellation_Oct', 'Loan_Disbursement_Borrower_Oct',
        'Fully_Paid_Borrower_Oct', 'Loan_Recoverable_Oct', 'Loan_Recovered_Regular_Oct',
        'Loan_Recovered_Due_Oct', 'New_Due_Amount_Oct', 'Oct_Total Due', 'Total_Due_Loanee',
        'Bad_Loan_365+', 'Total_Outstanding', 'Overdue_Loan_Outstanding',
        'Cummulative_Loan_Disbursement', 'Cummulative_Loan_Collection'
    ]

    for col in cols_to_clean:
        if col in df.columns:
            # Safely convert and fill NaNs
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            # If a column is missing, create it with zeros to prevent errors in feature engineering
            df[col] = 0

    # --- Feature Engineering ---
    # Net Member Growth is used for ranking/sorting the diverging chart
    df['Net_Member_Growth_Oct'] = df['New_Member_Admission_Oct'] - df['Member_Cancellation_Oct']
    
    df['Overdue_Percent_Branch'] = df['Overdue_Loan_Outstanding'].div(df['Total_Outstanding'].replace(0, np.nan)).fillna(0).clip(upper=1)
    df['Oct_Total_Due_Loanee_Combined'] = df['Oct_Total Due'] + df['Total_Due_Loanee']
    df['Non_Overdue_Outstanding'] = df['Total_Outstanding'] - df['Overdue_Loan_Outstanding']

    # Efficiency and Risk Ratios
    df['Collection_Efficiency_Ratio'] = df['Cummulative_Loan_Collection'].div(
        df['Cummulative_Loan_Disbursement'].replace(0, np.nan)
    ).fillna(0).clip(upper=1)
    
    df['Bad_Loan_Conversion_Rate'] = df['Bad_Loan_365+'].div(
        df['Overdue_Loan_Outstanding'].replace(0, np.nan)
    ).fillna(0).clip(upper=1)
    
    return df

# --- 2. KPI CALCULATION (Retained for Summary) ---
def calculate_kpis(df):
    """Calculates overall Key Performance Indicators from the summarized data."""
    kpi_data = df.sum(numeric_only=True)
    kpi = {}
    total_outstanding = kpi_data['Total_Outstanding']
    total_recoverable = kpi_data['Loan_Recoverable_Oct']
    
    kpi['Total Outstanding (Value)'] = total_outstanding
    kpi['Overall Overdue %'] = (kpi_data['Overdue_Loan_Outstanding'] / total_outstanding) if total_outstanding > 0 else 0
    kpi['Overall Cash Recovery Rate'] = (kpi_data['Loan_Recovered_Regular_Oct'] / total_recoverable) if total_recoverable > 0 else 0
    kpi['Net Member Growth'] = kpi_data['Net_Member_Growth_Oct']
    return kpi

# --- 3. CORE VISUALIZATION FUNCTIONS ---

def create_pie_chart_ratio(df, metric1, metric2, title, overall_sum):
    """Generates a pie chart for two complementary metrics."""
    
    unachieved_value = max(0, overall_sum - df[metric2].sum())
    
    pie_data = pd.DataFrame({
        'Category': [f'Unachieved Portion ({metric1.split("_")[0]})', 
                     metric2.replace('_', ' ').replace('Oct', '').strip()],
        'Value': [unachieved_value, df[metric2].sum()]
    })
    
    ratio = df[metric2].sum() / overall_sum if overall_sum > 0 else 0
    
    fig = px.pie(
        pie_data, names='Category', values='Value', 
        title=f'{title} (Ratio: {ratio:.2%})', hole=.4, 
        color_discrete_sequence=px.colors.sequential.Teal
    )
    # Ensure hover template shows full value
    fig.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)),
                      hovertemplate='%{label}<br>Value: %{value:,.0f}<br>Percentage: %{percent}<extra></extra>')
    return fig

def plot_outstanding_overdue_bar(df, n=TOP_N_BRANCHES):
    """Generates a STACKED bar chart for Total_Outstanding vs Overdue_Loan_Outstanding."""
    
    top_n_df = df.nlargest(n, 'Total_Outstanding').sort_values(by='Total_Outstanding', ascending=False).copy()

    melted_df = top_n_df.melt(
        id_vars=['BranchName'],
        value_vars=['Non_Overdue_Outstanding', 'Overdue_Loan_Outstanding'],
        var_name='Outstanding Type',
        value_name='Amount'
    )
    
    fig = px.bar(
        melted_df, x='BranchName', y='Amount', color='Outstanding Type',
        title=f'1. Top {n} Branches: Portfolio Composition (Outstanding vs. Overdue)',
        labels={'Amount': 'Amount ', 'Outstanding Type': 'Loan Status'},
        color_discrete_map={'Non_Overdue_Outstanding': 'lightgreen', 'Overdue_Loan_Outstanding': 'crimson'},
        height=600,
        # Ensure hover template shows full value
        custom_data=['Amount'] 
    )
    fig.update_traces(hovertemplate='Branch: %{x}<br>Status: %{color}<br>Amount: %{y:,.0f}<extra></extra>')
    
    # --- FIX: Set tickformat for Y-axis to prevent abbreviation ---
    fig.update_layout(
        yaxis={'tickprefix': '', 'tickformat': ',.0f'}, 
        barmode='stack',
        xaxis={'categoryorder': 'total descending'}
    )
    return fig

def plot_total_outstanding_diverging_bar(df, n=TOP_N_BRANCHES):
    """
    ranking the Top N branches by Total Outstanding
    relative to the overall average outstanding.
    """
    # Calculate the mean outstanding across all branches
    mean_outstanding = df['Total_Outstanding'].mean()
    
    # Calculate the deviation from the mean
    plot_df = df.copy()
    plot_df['Deviation_From_Mean'] = plot_df['Total_Outstanding'] - mean_outstanding
    
    # Filter for the top N branches based on Total_Outstanding (to focus on the largest)
    top_n_df = plot_df.nlargest(n, 'Total_Outstanding').sort_values('Deviation_From_Mean', ascending=True).copy()
    
    # Define color based on whether the deviation is positive (Above Mean) or negative (Below Mean)
    top_n_df['Color'] = top_n_df['Deviation_From_Mean'].apply(lambda x: 'Above Mean' if x >= 0 else 'Below Mean')
    
    fig = px.bar(
        top_n_df, 
        x='Deviation_From_Mean', 
        y='BranchName', 
        color='Color',
        orientation='h',
        title=f'2. Ranking: Top {n} Branches by Total Outstanding (Average)',
        labels={'Deviation_From_Mean': 'Deviation from Average Outstanding ', 'BranchName': 'Branch Name'},
        color_discrete_map={'Above Mean': 'darkgreen', 'Below Mean': 'firebrick'},
        height=700
    )

    # Add a vertical line for the zero baseline (the mean)
    fig.add_vline(x=0, line_width=1, line_dash="dash", line_color="gray")
    
    # Add annotations for the mean value (formatted for clarity)
    fig.add_annotation(
        x=0, y=1.05, yref='paper',
        text=f'Average Outstanding: {mean_outstanding:,.0f}', # Already correctly formatted
        showarrow=False,
        xanchor='center',
        font=dict(size=12, color="gray")
    )
    
    fig.update_layout(
        margin=dict(l=50, r=20, t=80, b=20),
        # FIX: Ensure X-axis uses full numbers with comma separators
        xaxis=dict(tickprefix="", showgrid=True, gridcolor='lightgray', tickformat=',.0f'),
        legend_title='Status Relative to Mean',
        yaxis={'categoryorder': 'total ascending'} 
    )
    
    return fig

def plot_member_activity_diverging_bar(df, n=TOP_N_BRANCHES):
    """
    Generates a Diverging Bar Chart showing New Member Admission and Cancellation
    for the Top N most active branches based on Net Member Growth.
    """
    # Filter for top N most active branches (highest absolute net growth)
    plot_df = df.copy()
    plot_df['Abs_Net_Growth'] = plot_df['Net_Member_Growth_Oct'].abs()
    plot_df = plot_df.nlargest(n, 'Abs_Net_Growth')
    plot_df = plot_df.sort_values('Net_Member_Growth_Oct', ascending=True)

    # Prepare data for Plotly
    # Cancellations are converted to negative values for the diverging chart effect
    plot_df['Member_Cancellation_Oct_Negative'] = -plot_df['Member_Cancellation_Oct']

    fig = go.Figure()

    # Admissions (Positive side)
    fig.add_trace(go.Bar(
        y=plot_df['BranchName'],
        x=plot_df['New_Member_Admission_Oct'],
        orientation='h',
        name='New Admissions (Growth)',
        marker_color='teal',
        # FIX: Ensure hover template shows full value
        hovertemplate='Branch: %{y}<br>Admissions: %{x:,.0f}<extra></extra>'
    ))

    # Cancellations (Negative side)
    fig.add_trace(go.Bar(
        y=plot_df['BranchName'],
        x=plot_df['Member_Cancellation_Oct_Negative'],
        orientation='h',
        name='Cancellations (Loss)',
        marker_color='salmon',
        # FIX: Ensure hover template shows full ABSOLUTE value
        hovertemplate='Branch: %{y}<br>Cancellations: %{x|abs:,.0f}<extra></extra>' 
    ))

    # Add Net Growth Annotations (Labels)
    annotations = []
    for index, row in plot_df.iterrows():
        net_growth = row['Net_Member_Growth_Oct']
        text_color = 'darkgreen' if net_growth > 0 else 'darkred'
        
        # Determine position for net growth label (placed near the admission bar end)
        x_pos = row['New_Member_Admission_Oct'] + 5 # Slightly to the right of the admission bar
        if net_growth < 0:
             # If net loss, place label slightly to the left of the center/cancellation bar
             x_pos = row['Member_Cancellation_Oct_Negative'] - 5 

        annotations.append(dict(
            xref='x', yref='y',
            x=x_pos, 
            y=row['BranchName'],
            text=f'Net: {net_growth:+,.0f}',
            font=dict(color=text_color, size=10),
            xanchor='left' if net_growth > 0 else 'right',
            showarrow=False
        ))


    fig.update_layout(
        title_text=f'3. Ranking: Top {n} Branches by Net Member Activity',
        barmode='relative',
        height=700,
        margin=dict(l=50, r=80, t=50, b=20),
        xaxis_title='Member Count (Negative = Cancellations | Positive = Admissions)',
        yaxis_title='Branch Name (Ranked by Net Growth)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        annotations=annotations,
        yaxis={'categoryorder': 'array', 'categoryarray': plot_df['BranchName'].tolist()}
    )
    
    # Custom tick labels logic is already in place to show full positive numbers for both sides
    max_abs = max(plot_df['New_Member_Admission_Oct'].max(), plot_df['Member_Cancellation_Oct'].max())
    if max_abs > 0:
        # Create 5 tick points spanning the total range
        tickvals = np.linspace(-max_abs, max_abs, 5)
    else:
        tickvals = [0]
        
    ticktext = [f'{abs(v):,.0f}' for v in tickvals]
    
    fig.update_xaxes(
        tickmode='array',
        tickvals=tickvals,
        ticktext=ticktext,
        showgrid=True, gridcolor='#DDDDDD',
        # Set tickformat just in case, though ticktext array handles the display
        tickformat=',.0f'
    )
    
    return fig


def plot_risk_composition_3d_pie(df):
    """
    Generates a 3D Pie Chart showing the overall portfolio risk composition
    across Healthy, Overdue (0-365), and Bad Loan (365+) categories.
    """
    # Calculate components
    total_outstanding = df['Total_Outstanding'].sum()
    overdue_sum = df['Overdue_Loan_Outstanding'].sum()
    bad_loan = df['Bad_Loan_365+'].sum()

    healthy_sum = total_outstanding - overdue_sum
    overdue_not_bad = overdue_sum - bad_loan

    # Ensure no negative values if data is inconsistent
    if healthy_sum < 0: healthy_sum = 0 
    if overdue_not_bad < 0: overdue_not_bad = 0
    if bad_loan < 0: bad_loan = 0


    pie_data = pd.DataFrame({
        'Category': ['Healthy Outstanding', 'Overdue (0-365 Days)', 'Bad Loan (365+ Days)'],
        'Amount': [healthy_sum, overdue_not_bad, bad_loan]
    })
    
    fig = go.Figure(data=[go.Pie(
        labels=pie_data['Category'],
        values=pie_data['Amount'],
        hole=.3,
        marker=dict(colors=['#4CAF50', '#FFC107', '#D32F2F']), # Green, Amber, Red
        # FIX: Ensure hover template shows full value
        hovertemplate='%{label}<br>Amount: %{value:,.0f}<br>Percentage: %{percent}<extra></extra>'
    )])

    fig.update_layout(
        title_text='4. Overall Portfolio Risk Composition',
        height=650,
        margin=dict(t=50, b=20, l=20, r=20),
        uniformtext_minsize=12,
        uniformtext_mode='hide'
    )
    
    return fig


def plot_overdue_risk_bullet_chart(df, n=TOP_N_BRANCHES):
    """
    Generates a Bullet Chart style plot comparing Bad Loan (365+) against Total Overdue
    for the top N branches ranked by Bad Loan amount.
    """
    # Rank by Bad Loan to focus on the highest risk branches
    ranking_df = df.nlargest(n, 'Bad_Loan_365+').sort_values('Bad_Loan_365+', ascending=True).copy()
    
    fig = go.Figure()

    # 1. Background Bar (Contextual Value: Total Overdue Loan Outstanding)
    fig.add_trace(go.Bar(
        y=ranking_df['BranchName'],
        x=ranking_df['Overdue_Loan_Outstanding'],
        orientation='h',
        name='Total Overdue (Risk Context)',
        marker_color='orange', 
        opacity=0.6,
        # FIX: Ensure hover template shows full value
        hovertemplate='Branch: %{y}<br>Total Overdue: %{x:,.0f}<extra></extra>'
    ))

    # 2. Foreground Bar (Performance Value: Bad Loan 365+) - The critical measure
    fig.add_trace(go.Bar(
        y=ranking_df['BranchName'],
        x=ranking_df['Bad_Loan_365+'],
        orientation='h',
        name='Bad Loan (365+)',
        marker_color='firebrick', 
        # FIX: Ensure hover template shows full value
        hovertemplate='Branch: %{y}<br>Bad Loan 365+: %{x:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title_text=f'5. Overdue Risk: Bad Loan (365+) vs. Total Overdue (Bullet Chart Style, Top {TOP_N_BRANCHES} Risk Branches)',
        xaxis_title='Amount (Log Scale)',
        yaxis_title='Branch Name (Ranked by Bad Loan)',
        legend_title='Risk Metric',
        height=700,
        margin=dict(l=50, r=20, t=50, b=20),
        barmode='overlay', 
        # --- FIX: Set tickformat for X-axis to prevent abbreviation ---
        # The log type can sometimes force scientific notation, so we explicitly set the format.
        xaxis=dict(tickprefix="", showgrid=True, gridcolor='lightgray', type='log', tickformat=',.0f'), 
        yaxis={'categoryorder': 'total ascending'} 
    )
    
    return fig

def plot_due_ranking_bullet_chart(df, n=TOP_N_BRANCHES):
    """
    Generates rank branches by Oct Total Due against 
    their Combined Total Due.
    """
    ranking_df = df.nlargest(n, 'Oct_Total Due').sort_values('Oct_Total Due', ascending=True).copy()
    
    fig = go.Figure()

    # 1. Background Bar (Target/Contextual Value: Combined Total Due)
    fig.add_trace(go.Bar(
        y=ranking_df['BranchName'],
        x=ranking_df['Oct_Total_Due_Loanee_Combined'],
        orientation='h',
        name='Combined Total Due',
        marker_color='lightblue', 
        opacity=0.5,
        # FIX: Ensure hover template shows full value
        hovertemplate='Branch: %{y}<br>Combined Due: %{x:,.0f}<extra></extra>'
    ))

    # 2. Foreground Bar (Performance Value: Oct Total Due) - The actual ranking bar
    fig.add_trace(go.Bar(
        y=ranking_df['BranchName'],
        x=ranking_df['Oct_Total Due'],
        orientation='h',
        name='Oct Total Due',
        marker_color='darkblue', 
        # FIX: Ensure hover template shows full value
        hovertemplate='Branch: %{y}<br>Oct Due: %{x:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title_text=f'6. Ranking: Top {n} Branches by October Total Due (Bullet Chart Style)',
        xaxis_title='Amount (Log Scale)',
        yaxis_title='Branch Name (Ranked by Oct Due)',
        legend_title='Due Metric',
        height=700,
        margin=dict(l=50, r=20, t=50, b=20),
        barmode='overlay', 
        # --- FIX: Set tickformat for X-axis to prevent abbreviation ---
        xaxis=dict(tickprefix="", showgrid=True, gridcolor='lightgray', type='log', tickformat=',.0f'), 
        yaxis={'categoryorder': 'total ascending'} 
    )
    
    return fig

# --- 4. STREAMLIT APPLICATION LAYOUT ---
def main():
    st.set_page_config(
        page_title="POMIS Advanced Ratio Analysis",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.title("📊 Pomis Summary Report Oct 2025 Analysis 📈")
    st.markdown("This dashboard focuses on key ratios, compositional analysis, efficiency, and high-risk branch identification.")
    st.markdown("---")

    df = load_data()
    kpis = calculate_kpis(df)
    total_sums = df.sum(numeric_only=True)

    # --- Section 1: Overall KPIs (Quick Summary) ---
    st.header("Overall Financial Health Summary")
    col1, col2, col3, col4 = st.columns(4)
    # The formatting here is already correct (e.g., f"{value:,.0f}")
    col1.metric("Total Outstanding", f"{kpis['Total Outstanding (Value)']:,.0f}")
    col2.metric("Overall Overdue %", f"{kpis['Overall Overdue %']:.2%}", delta_color="inverse")
    col3.metric("Regular Cash Recovery Rate", f"{kpis['Overall Cash Recovery Rate']:.2%}", delta_color="normal")
    col4.metric("Net Member Growth", f"{kpis['Net Member Growth']:,.0f}")
    st.markdown("---")

    # --- Section 2: Ratio/Composition Plots (Pie/Bar) ---
    st.header("Organizational Ratio and Composition Analysis")
    st.markdown("Analyzing key activity and recovery ratios using Pie and Bar charts.")

    # Row 1: Membership and Loan Completion
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Membership Activity (Admissions vs. Cancellations)")
        
        melted_member = df[['New_Member_Admission_Oct', 'Member_Cancellation_Oct']].sum().reset_index()
        melted_member.columns = ['Metric', 'Count']

        fig_member_comp = px.bar(
            melted_member, x='Metric', y='Count', color='Metric', title='Total Admissions vs. Total Cancellations',
            color_discrete_map={'New_Member_Admission_Oct': 'teal', 'Member_Cancellation_Oct': 'salmon'}
        )
        # FIX: Set tickformat for Y-axis to prevent abbreviation
        fig_member_comp.update_layout(yaxis={'tickprefix': '', 'tickformat': ',.0f'})
        st.plotly_chart(fig_member_comp, use_container_width=True)

    with col_b:
        st.subheader("Loan Completion Ratio (Count)")
        fig_loan_comp = create_pie_chart_ratio(
            df, 'Loan_Disbursement_Borrower_Oct', 'Fully_Paid_Borrower_Oct', 'Loan Disbursement vs. Fully Paid Loans',
            total_sums['Loan_Disbursement_Borrower_Oct']
        )
        st.plotly_chart(fig_loan_comp, use_container_width=True)

    # Row 2: Recovery and Due Management
    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("Regular Recovery Composition")
        fig_recovery_pie = create_pie_chart_ratio(
            df, 'Loan_Recoverable_Oct', 'Loan_Recovered_Regular_Oct', 'Loan Recovered Regular vs. Unrecovered Portion',
            total_sums['Loan_Recoverable_Oct']
        )
        st.plotly_chart(fig_recovery_pie, use_container_width=True)

    with col_d:
        st.subheader("Due Management Comparison")
        due_df = pd.DataFrame({
            'Metric': ['Loan Recovered Due', 'New Due Amount'],
            'Value': [total_sums['Loan_Recovered_Due_Oct'], total_sums['New_Due_Amount_Oct']]
        })
        fig_due_comp = px.bar(
            due_df, x='Metric', y='Value', color='Metric', title='Recovered Due vs. New Due Amount (Total)',
            color_discrete_map={'Loan Recovered Due': 'darkgreen', 'New Due Amount': 'orange'}
        )
        # FIX: Set tickformat for Y-axis to prevent abbreviation
        fig_due_comp.update_layout(yaxis={'tickprefix': '', 'tickformat': ',.0f'})
        st.plotly_chart(fig_due_comp, use_container_width=True)

    st.markdown("---")

    # --- Section 3: Portfolio Health Composition (Stacked Bar Chart) ---
    st.header(f"Portfolio Health Composition (Top {TOP_N_BRANCHES} Branches by Portfolio Size)")
    st.markdown("Stacked bar chart showing the composition of total outstanding loans for the branches with the largest portfolios.")
    
    fig_outstanding_bar = plot_outstanding_overdue_bar(df, TOP_N_BRANCHES)
    st.plotly_chart(fig_outstanding_bar, use_container_width=True)
    st.info("The crimson portion represents the Overdue Loan Outstanding, showing the relative risk within the branch's total portfolio.")

    st.markdown("---")

    # --- Section 4: RANKING BY TOTAL OUTSTANDING (Diverging Bar Chart) ---
    st.header(f"Ranking: Top {TOP_N_BRANCHES} Branches by Total Outstanding (Average)")
    st.markdown("showing the performance of the largest portfolios relative to the overall average outstanding amount.")
    
    fig_outstanding_diverging = plot_total_outstanding_diverging_bar(df, TOP_N_BRANCHES)
    st.plotly_chart(fig_outstanding_diverging, use_container_width=True)
    st.info("Green bars indicate branches with outstanding portfolios significantly **above** the overall average. Red bars indicate those **below**.")

    st.markdown("---")
    
    # --- Section 5: RANKING BY MEMBER ACTIVITY (Diverging Bar Chart) ---
    st.header(f"Ranking: Top {TOP_N_BRANCHES} Branches by Net Member Activity")
    st.markdown(" New Admissions (Positive) and Cancellations (Negative) for the most active branches.")
    
    fig_member_ranking = plot_member_activity_diverging_bar(df, TOP_N_BRANCHES)
    st.plotly_chart(fig_member_ranking, use_container_width=True)
    st.info("The Net value shows the difference (Growth or Loss). Branches with large positive bars are performing well in member acquisition.")

    st.markdown("---")


    # --- Section 6: ADVANCED EFFICIENCY AND RISK RATIOS (3D PIE) ---
    st.header(f"Advanced Efficiency and Risk Ratios (Overall Portfolio Composition)")
    st.markdown("the entire loan portfolio broken down into risk categories.")
    
    fig_3d_pie = plot_risk_composition_3d_pie(df)
    st.plotly_chart(fig_3d_pie, use_container_width=True)
    st.info("This view highlights the relative size of the 'Bad Loan (365+ Days)' portion of the overall outstanding portfolio.")

    st.markdown("---")

    # --- Section 7: UPDATED - OVERDUE RISK PROFILE (Bullet Chart) ---
    st.header(f"Overdue Risk: Bad Loan (365+) vs. Total Overdue, Top {TOP_N_BRANCHES} Risk Branches)")
    st.markdown(" ranking comparing the critical 'Bad Loan (365+)' amount (Foreground/Red) against the total 'Overdue Loan Outstanding' (Background/Orange) for the riskiest branches.")

    fig_risk_bullet = plot_overdue_risk_bullet_chart(df, TOP_N_BRANCHES)
    st.plotly_chart(fig_risk_bullet, use_container_width=True)
    st.info("The red bar shows the absolute amount of Bad Loans (worst risk) contained within the orange bar (total risk portfolio). The closer the red bar is to the orange bar, the higher the conversion rate from Overdue to Bad Loan.")

    st.markdown("---")

    # --- Section 8: DUE RANKING (Bullet Chart) ---
    st.header(f"Ranking: Top {TOP_N_BRANCHES} Branches by October Total Due")
    st.markdown(" ranking comparing the current month's due amount (`Oct Total Due`) against the overall due amount (`Combined Total Due`).")
    
    fig_bullet = plot_due_ranking_bullet_chart(df, TOP_N_BRANCHES)
    st.plotly_chart(fig_bullet, use_container_width=True)
    st.info("The darker bar (`Oct Total Due`) should ideally be close to or exceed the lighter bar (`Combined Total Due`) if all past dues are being accounted for and collected.")

    # Data Table for the Ranking data
    st.subheader(f"Data Table: Top {TOP_N_BRANCHES} Branches by Oct Total Due")
    top_25_due_display = df.nlargest(TOP_N_BRANCHES, 'Oct_Total Due')[['BranchName', 'Oct_Total Due', 'Total_Due_Loanee', 'Oct_Total_Due_Loanee_Combined']]
    
    top_25_due_display = top_25_due_display.rename(columns={
        'Oct_Total Due': 'Oct Total Due ',
        'Total_Due_Loanee': 'Total Due Loanee ',
        'Oct_Total_Due_Loanee_Combined': 'Combined Total Due '
    })

    # Apply number formatting
    format_mapping = {
        'Oct Total Due ': '{:,.0f}',
        'Total Due Loanee ': '{:,.0f}',
        'Combined Total Due ': '{:,.0f}'
    }

    # The dataframe styling is already correct for full numbers
    st.dataframe(top_25_due_display.style.format(format_mapping), use_container_width=True)


if __name__ == '__main__':
    main()
