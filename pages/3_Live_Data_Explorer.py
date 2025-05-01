"""
Live Data Explorer - Marine Conservation Platform

This page provides exploration capabilities for the new live survey data format,
allowing testing and visualization without affecting the main dashboard pages.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
import numpy as np

# Import branding utilities
from utils.branding import display_logo, add_favicon

# Page configuration
st.set_page_config(
    page_title="Live Data Explorer | Marine Conservation Platform",
    page_icon="🌊",
    layout="wide"
)

# Add favicon
add_favicon()

# Display small logo at the top
display_logo(size="small")

# Page title
st.title("Live Survey Data Explorer")

st.markdown("""
## MCP's Ecological Monitoring Program

This page allows you to explore data collected through Marine Conservation Philippines' volunteer-based scientific diving program, 
which focuses on collecting and analyzing biophysical data on locally-managed MPAs effectiveness and resilience.

### Key Focus Areas:
- Assess locally managed Protected Areas' effectiveness at providing food security for the community
- Assess regional reef health and resilience
- Assess threats and sustainability of local MPAs at continuing to provide desired goods for the community

### Methodology Overview
MCP uses stratified random sampling with 30-meter transects across three depth ranges (3-7m, 9-13m, 15-19m):

- **Substrate Surveys**: Point intercept transect method with identification every 25cm (120 points per transect)
- **Fish Surveys**: Visual census on 5m wide belt transects (2.5m on each side of the line), with fish identified and measured in 5cm increments
- **Invertebrate Surveys**: Belt transect method covering 150m² per transect (5m×30m), with specimens measured in centimeter increments
- **Predation Surveys**: Tracking coral predators and assessing their impact on reef health

Data is collected on a seasonal basis to track changes in MPA ecosystems over time.

Use the tools below to explore the different survey types and understand the ecological health of the monitored areas.
""")

# Function to analyze invertebrate survey data
def analyze_invertebrate_data(df):
    """
    Process and analyze invertebrate survey data
    
    Args:
        df: Pandas DataFrame containing invertebrate survey data
    """
    # Pre-process the data if needed
    # Convert date strings to datetime if they're not already
    if 'Date' in df.columns and not pd.api.types.is_datetime64_dtype(df['Date']):
        try:
            df['Date'] = pd.to_datetime(df['Date'])
        except Exception as e:
            st.warning(f"Could not convert dates to datetime format: {str(e)}")
    
    # Clean up site names (remove MPA suffixes if present)
    if 'Site' in df.columns:
        df['Site'] = df['Site'].str.replace(' MPA', '').str.strip()
    
    # Display basic info
    st.subheader("Dataset Overview")
    
    # Basic statistics
    num_surveys = df['Survey_ID'].nunique()
    num_sites = df['Site'].nunique()
    # For invertebrate surveys, use Species instead of Invertebrate_type
    num_types = df['Species'].nunique() if 'Species' in df.columns else 0
    date_range = f"{df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}"
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Number of Surveys", num_surveys)
    col2.metric("Number of Sites", num_sites)
    col3.metric("Number of Species Types", num_types)
    col4.metric("Date Range", date_range)
    
    # Show sites
    st.subheader("Sites in Dataset")
    sites = df['Site'].unique()
    st.write(", ".join(sites))
    
    # Filter options
    st.subheader("Filter Data")
    col1, col2 = st.columns(2)
    
    with col1:
        selected_site = st.selectbox("Select Site", ["All Sites"] + list(df['Site'].unique()), key="invertebrate_site")
    
    with col2:
        # Extract dates and format them
        dates = pd.to_datetime(df['Date']).dt.date.unique()
        dates = sorted(dates)
        selected_date = st.selectbox("Select Survey Date", ["All Dates"] + [str(d) for d in dates], key="invertebrate_date")
    
    # Apply filters
    filtered_df = df.copy()
    if selected_site != "All Sites":
        filtered_df = filtered_df[filtered_df['Site'] == selected_site]
    
    if selected_date != "All Dates":
        # Convert selected_date to datetime for comparison
        selected_date_obj = pd.to_datetime(selected_date).date()
        filtered_df = filtered_df[pd.to_datetime(filtered_df['Date']).dt.date == selected_date_obj]
    
    # Display filtered dataframe
    if len(filtered_df) > 0:
        st.subheader("Filtered Data Sample")
        st.dataframe(filtered_df.head(20), use_container_width=True)
        
        # Calculate metrics
        st.subheader("Invertebrate Counts by Species")
        
        if 'Species' in filtered_df.columns and 'Total' in filtered_df.columns:
            # Group by invertebrate species
            type_counts = filtered_df.groupby('Species')['Total'].sum().reset_index()
            type_counts = type_counts.sort_values('Total', ascending=False)
            
            # Create bar chart
            fig = px.bar(
                type_counts,
                x='Species',
                y='Total',
                title='Invertebrate Counts by Species',
                labels={'Total': 'Count', 'Species': 'Species'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Create pie chart for distribution
            fig = px.pie(
                type_counts,
                values='Total',
                names='Species',
                title='Invertebrate Species Distribution',
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Required columns for analysis not found in the dataset.")
    else:
        st.warning("No data available for the selected filters.")

# Function to analyze predation survey data
def analyze_predation_data(df):
    """
    Process and analyze predation survey data
    
    Args:
        df: Pandas DataFrame containing predation survey data
    """
    # Pre-process the data if needed
    # Convert date strings to datetime if they're not already
    if 'Date' in df.columns and not pd.api.types.is_datetime64_dtype(df['Date']):
        try:
            df['Date'] = pd.to_datetime(df['Date'])
        except Exception as e:
            st.warning(f"Could not convert dates to datetime format: {str(e)}")
    
    # Clean up site names (remove MPA suffixes if present)
    if 'Site' in df.columns:
        df['Site'] = df['Site'].str.replace(' MPA', '').str.strip()
    
    # Display basic info
    st.subheader("Dataset Overview")
    
    # Basic statistics
    num_surveys = df['Survey_ID'].nunique()
    num_sites = df['Site'].nunique()
    # In predation data, the Group column contains predator types
    predator_col = 'Group' if 'Group' in df.columns else 'Predator'
    num_predators = df[predator_col].nunique() if predator_col in df.columns else 0
    date_range = f"{df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}"
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Number of Surveys", num_surveys)
    col2.metric("Number of Sites", num_sites)
    col3.metric("Number of Predator Types", num_predators)
    col4.metric("Date Range", date_range)
    
    # Show sites
    st.subheader("Sites in Dataset")
    sites = df['Site'].unique()
    st.write(", ".join(sites))
    
    # Filter options
    st.subheader("Filter Data")
    col1, col2 = st.columns(2)
    
    with col1:
        selected_site = st.selectbox("Select Site", ["All Sites"] + list(df['Site'].unique()), key="predation_site")
    
    with col2:
        # Extract dates and format them
        dates = pd.to_datetime(df['Date']).dt.date.unique()
        dates = sorted(dates)
        selected_date = st.selectbox("Select Survey Date", ["All Dates"] + [str(d) for d in dates], key="predation_date")
    
    # Apply filters
    filtered_df = df.copy()
    if selected_site != "All Sites":
        filtered_df = filtered_df[filtered_df['Site'] == selected_site]
    
    if selected_date != "All Dates":
        # Convert selected_date to datetime for comparison
        selected_date_obj = pd.to_datetime(selected_date).date()
        filtered_df = filtered_df[pd.to_datetime(filtered_df['Date']).dt.date == selected_date_obj]
    
    # Display filtered dataframe
    if len(filtered_df) > 0:
        st.subheader("Filtered Data Sample")
        st.dataframe(filtered_df.head(20), use_container_width=True)
        
        # Calculate metrics
        st.subheader("Predation Analysis")
        
        # The predation data has Group column for predator types and Total for counts
        if predator_col in filtered_df.columns and 'Total' in filtered_df.columns:
            # Group by predator type
            predator_counts = filtered_df.groupby(predator_col)['Total'].sum().reset_index()
            predator_counts = predator_counts.sort_values('Total', ascending=False)
            
            # Create bar chart
            fig = px.bar(
                predator_counts,
                x=predator_col,
                y='Total',
                title='Predator Counts by Type',
                labels={'Total': 'Count', predator_col: 'Predator Type'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Create pie chart for distribution
            fig = px.pie(
                predator_counts,
                values='Total',
                names=predator_col,
                title='Predator Type Distribution',
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # If size data is available, show size distribution
            if 'Size' in filtered_df.columns:
                # Group by predator type and size
                size_distribution = filtered_df.groupby([predator_col, 'Size'])['Total'].sum().reset_index()
                
                # Create grouped bar chart
                fig = px.bar(
                    size_distribution,
                    x=predator_col,
                    y='Total',
                    color='Size',
                    title='Predator Counts by Type and Size',
                    labels={'Total': 'Count', predator_col: 'Predator Type', 'Size': 'Size Range'}
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Required columns for analysis not found in the dataset.")
    else:
        st.warning("No data available for the selected filters.")

# Function to analyze substrate survey data
def analyze_substrate_data(df):
    """
    Process and analyze substrate survey data
    
    Args:
        df: Pandas DataFrame containing substrate survey data
    """
    # Pre-process the data if needed
    # Convert date strings to datetime if they're not already
    if 'Date' in df.columns and not pd.api.types.is_datetime64_dtype(df['Date']):
        try:
            df['Date'] = pd.to_datetime(df['Date'])
        except Exception as e:
            st.warning(f"Could not convert dates to datetime format: {str(e)}")
    
    # Clean up site names (remove MPA suffixes if present)
    if 'Site' in df.columns:
        df['Site'] = df['Site'].str.replace(' MPA', '').str.strip()
    
    # Display basic info
    st.subheader("Dataset Overview")
    
    # Basic statistics
    num_surveys = df['Survey_ID'].nunique()
    num_sites = df['Site'].nunique()
    date_range = f"{df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}"
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Number of Surveys", num_surveys)
    col2.metric("Number of Sites", num_sites)
    col3.metric("Date Range", date_range)
    
    # Show sites
    st.subheader("Sites in Dataset")
    sites = df['Site'].unique()
    st.write(", ".join(sites))
    
    # Filter options
    st.subheader("Filter Data")
    col1, col2 = st.columns(2)
    
    with col1:
        selected_site = st.selectbox("Select Site", ["All Sites"] + list(df['Site'].unique()))
    
    with col2:
        # Extract dates and format them
        dates = pd.to_datetime(df['Date']).dt.date.unique()
        dates = sorted(dates)
        selected_date = st.selectbox("Select Survey Date", ["All Dates"] + [str(d) for d in dates])
    
    # Apply filters
    filtered_df = df.copy()
    if selected_site != "All Sites":
        filtered_df = filtered_df[filtered_df['Site'] == selected_site]
    
    if selected_date != "All Dates":
        # Convert selected_date to datetime for comparison
        selected_date_obj = pd.to_datetime(selected_date).date()
        filtered_df = filtered_df[pd.to_datetime(filtered_df['Date']).dt.date == selected_date_obj]
    
    # Display filtered dataframe
    if len(filtered_df) > 0:
        st.subheader("Filtered Data Sample")
        st.dataframe(filtered_df.head(20), use_container_width=True)
        
        # Calculate hard coral cover
        st.subheader("Calculated Metrics")
        
        # Group by survey ID to analyze each survey separately
        survey_groups = filtered_df.groupby('Survey_ID')
        
        survey_metrics = []
        for survey_id, survey_data in survey_groups:
            # Get survey metadata from first row
            first_row = survey_data.iloc[0]
            site = first_row['Site']
            date = first_row['Date']
            depth = first_row['Depth']
            
            # Calculate totals
            total_points = survey_data['Total'].sum()
            
            # Hard coral calculations
            hard_coral_data = survey_data[survey_data['Group'].str.startswith('Hard Coral')]
            hard_coral_total = hard_coral_data['Total'].sum()
            hard_coral_cover = (hard_coral_total / total_points) * 100 if total_points > 0 else 0
            
            # Algae calculations
            algae_data = survey_data[survey_data['Group'].str.startswith('Algae')]
            algae_total = algae_data['Total'].sum()
            algae_cover = (algae_total / total_points) * 100 if total_points > 0 else 0
            
            # Fleshy macro algae
            fleshy_algae_data = survey_data[survey_data['Group'] == 'Algae Macro']
            fleshy_algae_total = fleshy_algae_data['Total'].sum()
            fleshy_algae_cover = (fleshy_algae_total / total_points) * 100 if total_points > 0 else 0
            
            # Rubble calculations
            rubble_data = survey_data[survey_data['Group'] == 'Substrate Rubble']
            rubble_total = rubble_data['Total'].sum() 
            rubble_cover = (rubble_total / total_points) * 100 if total_points > 0 else 0
            
            # Add to metrics list
            survey_metrics.append({
                'Survey_ID': survey_id,
                'Site': site,
                'Date': date,
                'Depth': depth,
                'Total_Points': total_points,
                'Hard_Coral_Cover': hard_coral_cover,
                'Algae_Cover': algae_cover,
                'Fleshy_Algae_Cover': fleshy_algae_cover,
                'Rubble_Cover': rubble_cover
            })
        
        # Convert to DataFrame
        metrics_df = pd.DataFrame(survey_metrics)
        
        # Display metrics
        st.dataframe(metrics_df, use_container_width=True)
        
        # Visualize
        st.subheader("Visualization")
        
        viz_tabs = st.tabs(["Basic Metrics", "Time Series", "Coral Health", "Site Dashboard Style"])
        
        with viz_tabs[0]:
            # Select metric to visualize
            metric_options = {
                'Hard_Coral_Cover': 'Hard Coral Cover (%)',
                'Algae_Cover': 'Algae Cover (%)',
                'Fleshy_Algae_Cover': 'Fleshy Algae Cover (%)',
                'Rubble_Cover': 'Rubble Cover (%)'
            }
            
            selected_metric = st.selectbox(
                "Select Metric to Visualize",
                list(metric_options.keys()),
                format_func=lambda x: metric_options[x]
            )
            
            # Create visualization based on grouping
            if len(metrics_df) > 1:
                if 'Depth' in metrics_df.columns and metrics_df['Depth'].nunique() > 1:
                    # Group by depth if multiple depths exist
                    fig = px.bar(
                        metrics_df, 
                        x='Depth', 
                        y=selected_metric,
                        color='Site',
                        barmode='group',
                        title=f"{metric_options[selected_metric]} by Depth",
                        labels={selected_metric: metric_options[selected_metric], 'Depth': 'Depth'}
                    )
                    
                    # Set y-axis range based on metric
                    if selected_metric in ['Hard_Coral_Cover', 'Algae_Cover', 'Fleshy_Algae_Cover', 'Rubble_Cover']:
                        fig.update_yaxes(range=[0, 100])
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Group by site visualization
                if metrics_df['Site'].nunique() > 1:
                    fig = px.bar(
                        metrics_df, 
                        x='Site', 
                        y=selected_metric,
                        color='Depth',
                        barmode='group',
                        title=f"{metric_options[selected_metric]} by Site",
                        labels={selected_metric: metric_options[selected_metric], 'Site': 'Site'}
                    )
                    
                    # Set y-axis range based on metric
                    if selected_metric in ['Hard_Coral_Cover', 'Algae_Cover', 'Fleshy_Algae_Cover', 'Rubble_Cover']:
                        fig.update_yaxes(range=[0, 100])
                        
                    st.plotly_chart(fig, use_container_width=True)
        
        with viz_tabs[1]:
            st.subheader("Time Series Analysis")
            
            if 'Date' in metrics_df.columns:
                # Convert to datetime and sort
                metrics_df['Date'] = pd.to_datetime(metrics_df['Date'])
                time_metrics_df = metrics_df.sort_values('Date')
                
                # Group by site and date
                if metrics_df['Site'].nunique() > 1:
                    # If multiple sites, add a site selector
                    time_site = st.selectbox("Select Site for Time Series", 
                                            ["All Sites"] + list(metrics_df['Site'].unique()),
                                            key="time_site")
                    
                    if time_site != "All Sites":
                        time_metrics_df = time_metrics_df[time_metrics_df['Site'] == time_site]
                
                # Select time series metric
                time_metric = st.selectbox(
                    "Select Metric for Time Series",
                    list(metric_options.keys()),
                    format_func=lambda x: metric_options[x],
                    key="time_metric"
                )
                
                # Create time series chart
                if not time_metrics_df.empty:
                    fig = px.line(
                        time_metrics_df,
                        x='Date',
                        y=time_metric,
                        color='Site' if 'time_site' in locals() and time_site == "All Sites" and metrics_df['Site'].nunique() > 1 else None,
                        markers=True,
                        title=f"{metric_options[time_metric]} Over Time",
                        labels={time_metric: metric_options[time_metric], 'Date': 'Survey Date'}
                    )
                    
                    # Set y-axis range based on metric
                    if time_metric in ['Hard_Coral_Cover', 'Algae_Cover', 'Fleshy_Algae_Cover', 'Rubble_Cover']:
                        fig.update_yaxes(range=[0, 100])
                        
                    # Add fixed reference bands for different condition categories (for coral cover)
                    if time_metric == 'Hard_Coral_Cover':
                        fig.add_hrect(y0=0, y1=25, line_width=0, fillcolor="red", opacity=0.1)
                        fig.add_hrect(y0=25, y1=50, line_width=0, fillcolor="orange", opacity=0.1)
                        fig.add_hrect(y0=50, y1=75, line_width=0, fillcolor="yellow", opacity=0.1)
                        fig.add_hrect(y0=75, y1=100, line_width=0, fillcolor="green", opacity=0.1)
                        
                        fig.add_annotation(x=time_metrics_df['Date'].min(), y=12.5, text="Poor", showarrow=False, 
                                        xanchor="left", yanchor="middle", font=dict(color="red"))
                        fig.add_annotation(x=time_metrics_df['Date'].min(), y=37.5, text="Fair", showarrow=False, 
                                        xanchor="left", yanchor="middle", font=dict(color="orange"))
                        fig.add_annotation(x=time_metrics_df['Date'].min(), y=62.5, text="Good", showarrow=False, 
                                        xanchor="left", yanchor="middle", font=dict(color="darkgreen"))
                        fig.add_annotation(x=time_metrics_df['Date'].min(), y=87.5, text="Excellent", showarrow=False, 
                                        xanchor="left", yanchor="middle", font=dict(color="green"))
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Add interpretation guidance
                    if time_metric == 'Hard_Coral_Cover':
                        st.info("""
                        **Hard Coral Cover Interpretation:**
                        - **0-25%**: Poor condition - Significant coral loss
                        - **25-50%**: Fair condition - Moderate coral coverage
                        - **50-75%**: Good condition - Healthy coral coverage
                        - **75-100%**: Excellent condition - Very high coral coverage
                        """)
                else:
                    st.warning("Not enough time series data available.")
        
        with viz_tabs[2]:
            st.subheader("Coral Health Analysis")
            
            # Filter to only coral data
            hard_coral_data_all = filtered_df[filtered_df['Group'].str.startswith('Hard Coral')]
            
            if not hard_coral_data_all.empty and 'Status' in hard_coral_data_all.columns:
                # Group by coral type and status
                health_data = hard_coral_data_all.groupby(['Group', 'Status'])['Total'].sum().reset_index()
                
                # Create health status chart
                fig = px.bar(
                    health_data,
                    x='Group',
                    y='Total',
                    color='Status',
                    title='Coral Health Status by Type',
                    labels={'Total': 'Count', 'Group': 'Coral Type', 'Status': 'Health Status'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Calculate overall health percentages
                status_totals = hard_coral_data_all.groupby('Status')['Total'].sum().reset_index()
                total_coral = status_totals['Total'].sum()
                status_totals['Percentage'] = (status_totals['Total'] / total_coral * 100).round(1)
                
                # Create pie chart for health distribution
                fig = px.pie(
                    status_totals,
                    values='Percentage',
                    names='Status',
                    title='Overall Coral Health Distribution',
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No coral health data available or 'Status' column missing.")
        
        with viz_tabs[3]:
            st.subheader("Site Dashboard Style Visualization")
            
            st.markdown("""
            This view replicates the style of visualization used in the main Site Dashboard.
            """)
            
            # Select metric for dashboard-style viz
            dashboard_metric = st.selectbox(
                "Select Metric for Dashboard Visualization",
                ['Hard_Coral_Cover'],  # For now, just focus on coral cover
                format_func=lambda x: metric_options[x],
                key="dashboard_metric"
            )
            
            if not metrics_df.empty:
                # Add confidence interval toggle
                show_ci = st.checkbox("Show Confidence Interval", value=True)
                
                # Create a styled line chart
                fig = go.Figure()
                
                # Calculate mean and confidence interval per date
                ci_df = metrics_df.groupby('Date')[dashboard_metric].agg(['mean', 'count', 'std']).reset_index()
                ci_df['sem'] = ci_df['std'] / np.sqrt(ci_df['count'])
                ci_df['ci_lower'] = ci_df['mean'] - 1.96 * ci_df['sem']
                ci_df['ci_upper'] = ci_df['mean'] + 1.96 * ci_df['sem']
                
                # Ensure confidence intervals don't go below 0 or above 100 for percentage values
                if dashboard_metric in ['Hard_Coral_Cover', 'Algae_Cover', 'Fleshy_Algae_Cover', 'Rubble_Cover']:
                    ci_df['ci_lower'] = ci_df['ci_lower'].clip(0)
                    ci_df['ci_upper'] = ci_df['ci_upper'].clip(upper=100)
                
                # Add the main line
                fig.add_trace(go.Scatter(
                    x=ci_df['Date'],
                    y=ci_df['mean'],
                    mode='lines+markers',
                    name=metric_options[dashboard_metric],
                    line=dict(width=2, color='rgba(31, 119, 180, 1)'),
                    marker=dict(size=8)
                ))
                
                # Add confidence interval as a shaded area
                if show_ci:
                    fig.add_trace(go.Scatter(
                        x=pd.concat([ci_df['Date'], ci_df['Date'].iloc[::-1]]),
                        y=pd.concat([ci_df['ci_upper'], ci_df['ci_lower'].iloc[::-1]]),
                        fill='toself',
                        fillcolor='rgba(31, 119, 180, 0.2)',
                        line=dict(color='rgba(255,255,255,0)'),
                        hoverinfo='skip',
                        showlegend=False
                    ))
                
                # Customize layout
                fig.update_layout(
                    title=f"{metric_options[dashboard_metric]} Over Time (Dashboard Style)",
                    xaxis_title="Survey Date",
                    yaxis_title=metric_options[dashboard_metric],
                    legend_title="Metric",
                    yaxis=dict(range=[0, 100]),
                    margin=dict(l=40, r=20, t=60, b=40),
                    plot_bgcolor='white'
                )
                
                # Add reference bands
                if dashboard_metric == 'Hard_Coral_Cover':
                    fig.add_hrect(y0=0, y1=25, line_width=0, fillcolor="red", opacity=0.1)
                    fig.add_hrect(y0=25, y1=50, line_width=0, fillcolor="orange", opacity=0.1)
                    fig.add_hrect(y0=50, y1=75, line_width=0, fillcolor="yellow", opacity=0.1)
                    fig.add_hrect(y0=75, y1=100, line_width=0, fillcolor="green", opacity=0.1)
                    
                    fig.add_annotation(x=ci_df['Date'].min(), y=12.5, text="Poor", showarrow=False, 
                                    xanchor="left", yanchor="middle", font=dict(color="red"))
                    fig.add_annotation(x=ci_df['Date'].min(), y=37.5, text="Fair", showarrow=False, 
                                    xanchor="left", yanchor="middle", font=dict(color="orange"))
                    fig.add_annotation(x=ci_df['Date'].min(), y=62.5, text="Good", showarrow=False, 
                                    xanchor="left", yanchor="middle", font=dict(color="darkgreen"))
                    fig.add_annotation(x=ci_df['Date'].min(), y=87.5, text="Excellent", showarrow=False, 
                                    xanchor="left", yanchor="middle", font=dict(color="green"))
                
                # Add grid lines
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
                
                # Custom buttons for zoom control
                fig.update_layout(
                    updatemenus=[
                        dict(
                            type="buttons",
                            direction="right",
                            x=0.1,
                            y=1.1,
                            showactive=False,
                            buttons=[
                                dict(
                                    label="Reset View",
                                    method="relayout",
                                    args=[{"xaxis.range": [ci_df['Date'].min(), ci_df['Date'].max()],
                                          "yaxis.range": [0, 100]}]
                                ),
                                dict(
                                    label="Zoom In Y",
                                    method="relayout",
                                    args=[{"yaxis.range": [25, 75]}]
                                ),
                                dict(
                                    label="Zoom Out Y",
                                    method="relayout",
                                    args=[{"yaxis.range": [0, 100]}]
                                )
                            ]
                        )
                    ]
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            # Show detailed coral types breakdown for the selected survey
            st.subheader("Hard Coral Type Breakdown")
            
            # Only proceed if we have hard coral data
            if len(hard_coral_data) > 0:
                # Group by coral type
                coral_types = hard_coral_data.groupby('Group')['Total'].sum().reset_index()
                coral_types['Percentage'] = coral_types['Total'] / coral_types['Total'].sum() * 100
                
                # Create pie chart
                fig = px.pie(
                    coral_types, 
                    values='Percentage', 
                    names='Group',
                    title='Hard Coral Types Distribution',
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")

# Function to process fish survey data
def analyze_fish_data(df):
    """
    Process and analyze fish survey data
    
    Args:
        df: Pandas DataFrame containing fish survey data
    """
    # Pre-process the data if needed
    # Convert date strings to datetime if they're not already
    if 'Date' in df.columns and not pd.api.types.is_datetime64_dtype(df['Date']):
        try:
            df['Date'] = pd.to_datetime(df['Date'])
        except Exception as e:
            st.warning(f"Could not convert dates to datetime format: {str(e)}")
    
    # Clean up site names (remove MPA suffixes if present)
    if 'Site' in df.columns:
        df['Site'] = df['Site'].str.replace(' MPA', '').str.strip()
    
    # Display basic info
    st.subheader("Dataset Overview")
    
    # Basic statistics
    num_surveys = df['Survey_ID'].nunique()
    num_sites = df['Site'].nunique()
    num_species = df['Species'].nunique() if 'Species' in df.columns else 0
    date_range = f"{df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}"
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Number of Surveys", num_surveys)
    col2.metric("Number of Sites", num_sites)
    col3.metric("Number of Species", num_species)
    col4.metric("Date Range", date_range)
    
    # Show sites
    st.subheader("Sites in Dataset")
    sites = df['Site'].unique()
    st.write(", ".join(sites))
    
    # Filter options
    st.subheader("Filter Data")
    col1, col2 = st.columns(2)
    
    with col1:
        selected_site = st.selectbox("Select Site", ["All Sites"] + list(df['Site'].unique()), key="fish_site")
    
    with col2:
        # Extract dates and format them
        dates = pd.to_datetime(df['Date']).dt.date.unique()
        dates = sorted(dates)
        selected_date = st.selectbox("Select Survey Date", ["All Dates"] + [str(d) for d in dates], key="fish_date")
    
    # Apply filters
    filtered_df = df.copy()
    if selected_site != "All Sites":
        filtered_df = filtered_df[filtered_df['Site'] == selected_site]
    
    if selected_date != "All Dates":
        # Convert selected_date to datetime for comparison
        selected_date_obj = pd.to_datetime(selected_date).date()
        filtered_df = filtered_df[pd.to_datetime(filtered_df['Date']).dt.date == selected_date_obj]
    
    # Display filtered dataframe
    if len(filtered_df) > 0:
        st.subheader("Filtered Data Sample")
        st.dataframe(filtered_df.head(20), use_container_width=True)
        
        # Calculate fish metrics
        st.subheader("Calculated Metrics")
        
        # Group by survey ID to analyze each survey separately
        survey_groups = filtered_df.groupby('Survey_ID')
        
        survey_metrics = []
        for survey_id, survey_data in survey_groups:
            # Get survey metadata from first row
            first_row = survey_data.iloc[0]
            site = first_row['Site']
            date = first_row['Date']
            
            # Get basic counts
            total_fish = len(survey_data)
            
            # Fish biomass calculation (if size data is available)
            if 'Size' in survey_data.columns and 'Total' in survey_data.columns:
                try:
                    # Convert size ranges to numeric estimates
                    # Extract the average size from ranges like "5-10"
                    def get_average_size(size_range):
                        if isinstance(size_range, str) and '-' in size_range:
                            parts = size_range.split('-')
                            try:
                                min_size = float(parts[0])
                                max_size = float(parts[1])
                                return (min_size + max_size) / 2
                            except (ValueError, IndexError):
                                return None
                        return size_range
                    
                    survey_data['Average_Size'] = survey_data['Size'].apply(get_average_size)
                    
                    # Basic formula: biomass ∝ length^3
                    # This is a simplification - real calculations would use species-specific coefficients
                    survey_data['Estimated_Weight'] = (survey_data['Average_Size'] ** 3) * 0.01  # Simple cubic relationship
                    survey_data['Total_Biomass'] = survey_data['Estimated_Weight'] * survey_data['Total']
                    total_biomass = survey_data['Total_Biomass'].sum()
                except Exception as e:
                    total_biomass = None
                    st.warning(f"Could not calculate biomass: {str(e)}")
            else:
                total_biomass = None
            
            # Add to metrics list
            survey_metrics.append({
                'Survey_ID': survey_id,
                'Site': site,
                'Date': date,
                'Total_Fish': total_fish,
                'Total_Biomass': total_biomass
            })
        
        # Convert to DataFrame
        metrics_df = pd.DataFrame(survey_metrics)
        
        # Display metrics
        st.dataframe(metrics_df, use_container_width=True)
        
        # Visualize
        st.subheader("Species Breakdown")
        
        # Species count
        if 'Species' in filtered_df.columns:
            species_counts = filtered_df.groupby('Species')['Total'].sum().reset_index() if 'Total' in filtered_df.columns else filtered_df.groupby('Species').size().reset_index(name='Total')
            species_counts = species_counts.sort_values('Total', ascending=False).head(15)  # Top 15 species
            
            fig = px.bar(
                species_counts,
                x='Species',
                y='Total',
                title='Top 15 Species by Count',
                labels={'Total': 'Count', 'Species': 'Species'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
        # Size distribution
        if 'Size' in filtered_df.columns:
            st.subheader("Size Distribution")
            
            # Count of fish by size category
            size_counts = filtered_df.groupby('Size')['Total'].sum().reset_index()
            
            fig = px.bar(
                size_counts,
                x='Size',
                y='Total',
                title='Fish Counts by Size Range',
                labels={'Size': 'Size Range (cm)', 'Total': 'Number of Fish'}
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")

# Function to detect survey type from CSV
def detect_survey_type(df):
    """
    Detect survey type from CSV columns and content
    
    Args:
        df: Pandas DataFrame to analyze
        
    Returns:
        str: Detected survey type
    """
    # Check column patterns and file name
    columns = set(df.columns)
    
    # For substrate surveys
    if {'Observer_name_1', 'Group', 'Status', 'Total'}.issubset(columns) or 'DBMCP_Substrates' in st.session_state.get('selected_file', ''):
        return "substrate"
    
    # For fish surveys
    elif {'Observer_name_1', 'Species', 'Size', 'Total'}.issubset(columns) or 'DBMCP_Fish' in st.session_state.get('selected_file', ''):
        return "fish"
    
    # For predation surveys - these have Group column with predator species like "Drupella"
    elif 'DBMCP_Predation' in st.session_state.get('selected_file', ''):
        return "predation"
    
    # For invertebrate surveys
    elif 'DBMCP_Inverts' in st.session_state.get('selected_file', ''):
        return "invertebrate"
    
    # Try to auto-detect based on column content if filename matching didn't work
    elif {'Observer_name_1', 'Group', 'Total'}.issubset(columns):
        # Check if this is predation data by looking at Group values
        if 'Group' in df.columns and len(df) > 0:
            sample_groups = df['Group'].unique()
            predation_indicators = ['Drupella', 'COTS', 'Coralliophila']
            for indicator in predation_indicators:
                if any(indicator in str(group) for group in sample_groups):
                    return "predation"
        return "substrate"  # Default to substrate if no predation indicators found
    
    # Check for invertebrate surveys by looking for invertebrate species
    elif {'Observer_name_1', 'Species', 'Total'}.issubset(columns):
        if 'Species' in df.columns and len(df) > 0:
            sample_species = df['Species'].unique()
            invert_indicators = ['Gastropod', 'Bivalve', 'Urchin', 'Sea Cucumber', 'Crab', 'Lobster']
            for indicator in invert_indicators:
                if any(indicator in str(species) for species in sample_species):
                    return "invertebrate"
        return "fish"  # Default to fish if no invertebrate indicators found
    
    # If nothing matches
    else:
        return "unknown"

# Check for available data files in the attached_assets directory
data_dir = "attached_assets"
available_files = []

if os.path.exists(data_dir):
    for filename in os.listdir(data_dir):
        if filename.endswith('.csv') and "DBMCP" in filename:
            available_files.append(filename)

# Data source selection
data_source = st.radio(
    "Select Data Source",
    ["Use Sample Files", "Upload File (currently disabled)"],
    index=0
)

if data_source == "Use Sample Files":
    if available_files:
        selected_file = st.selectbox(
            "Select a sample data file to analyze",
            available_files
        )
        
        # Store selected file in session state for detection logic
        st.session_state['selected_file'] = selected_file
        
        if selected_file:
            try:
                # Load data
                file_path = os.path.join(data_dir, selected_file)
                df = pd.read_csv(file_path)
                
                # Display raw data sample
                st.subheader("Raw Data Sample")
                st.dataframe(df.head(5), use_container_width=True)
                
                # Detect survey type
                survey_type = detect_survey_type(df)
                
                if survey_type == "substrate":
                    st.success("Detected Substrate Survey Data")
                    analyze_substrate_data(df)
                elif survey_type == "fish":
                    st.success("Detected Fish Survey Data")
                    analyze_fish_data(df)
                elif survey_type == "predation":
                    st.success("Detected Predation Survey Data")
                    analyze_predation_data(df)
                elif survey_type == "invertebrate":
                    st.success("Detected Invertebrate Survey Data")
                    analyze_invertebrate_data(df)
                else:
                    st.warning("Unknown survey type. Please check the file format.")
                    
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
    else:
        st.warning("No sample data files found in the attached_assets directory.")
else:
    # Disabling upload for now due to permission issues
    st.warning("Direct file upload is currently disabled due to permission issues. Please use the sample files option.")
    
    # Disabled file uploader (kept for future reference)
    uploaded_file = st.file_uploader("Upload Survey CSV (Disabled)", type=["csv"], disabled=True)
    
    # Explain expected format
    st.subheader("Expected Data Format")
    
    tabs = st.tabs(["Substrate Survey", "Fish Survey", "Other Surveys"])
    
    with tabs[0]:
        st.markdown("""
        **Substrate Survey Data** should include columns:
        - Observer_name_1, Observer_name_2: Names of divers
        - Date: Survey date
        - Site: Location name
        - Zone, Depth: Survey zone and depth category
        - Group: Category of substrate (e.g., "Hard Coral Branching")
        - Status: Health status
        - Diver_1_count, Diver_2_count: Individual counts
        - Total: Combined count
        - Survey_ID: Unique identifier for the survey
        """)
    
    with tabs[1]:
        st.markdown("""
        **Fish Survey Data** should include columns:
        - Observer details
        - Species information
        - Size and count data
        - Survey metadata
        """)
    
    with tabs[2]:
        st.markdown("""
        **Other survey types** (Predation, Invertebrate, Touristic value) will be supported in future updates.
        """)

# Footer
st.markdown("---")
st.markdown("This is a temporary page for exploring and testing the new live survey data format.")