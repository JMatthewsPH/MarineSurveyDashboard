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
This page allows you to explore and visualize the new live survey data format.
Upload CSV files from different survey types to analyze and test the data before
integrating it into the main dashboard.
""")

# Function to analyze substrate survey data
def analyze_substrate_data(df):
    """
    Process and analyze substrate survey data
    
    Args:
        df: Pandas DataFrame containing substrate survey data
    """
    # Display basic info
    st.subheader("Dataset Overview")
    
    # Basic statistics
    num_surveys = df['Survey_ID'].nunique()
    num_sites = df['Site'].nunique()
    date_range = f"{df['Date'].min()} to {df['Date'].max()}"
    
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
        filtered_df = filtered_df[filtered_df['Date'].str.startswith(selected_date)]
    
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
                st.plotly_chart(fig, use_container_width=True)
                
            # Show detailed coral types breakdown for the selected survey
            st.subheader("Hard Coral Type Breakdown")
            
            # Only proceed if we have hard coral data
            if hard_coral_data is not None and len(hard_coral_data) > 0:
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

# Function to process fish survey data (placeholder for now)
def analyze_fish_data(df):
    """
    Process and analyze fish survey data
    
    Args:
        df: Pandas DataFrame containing fish survey data
    """
    st.info("Fish survey analysis will be implemented in the future")
    st.dataframe(df.head(20), use_container_width=True)

# Function to detect survey type from CSV
def detect_survey_type(df):
    """
    Detect survey type from CSV columns
    
    Args:
        df: Pandas DataFrame to analyze
        
    Returns:
        str: Detected survey type
    """
    # Check column patterns
    columns = set(df.columns)
    
    if {'Observer_name_1', 'Group', 'Status', 'Total'}.issubset(columns):
        return "substrate"
    elif {'Observer_name_1', 'Species', 'Size'}.issubset(columns):
        return "fish"
    elif {'Observer_name_1', 'Predator'}.issubset(columns):
        return "predation"
    elif {'Observer_name_1', 'Invertebrate_type'}.issubset(columns):
        return "invertebrate"
    else:
        return "unknown"

# File uploader
uploaded_file = st.file_uploader("Upload Survey CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Load data
        df = pd.read_csv(uploaded_file)
        
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
            st.info("Predation survey analysis will be implemented in the future")
        elif survey_type == "invertebrate":
            st.success("Detected Invertebrate Survey Data")
            st.info("Invertebrate survey analysis will be implemented in the future")
        else:
            st.warning("Unknown survey type. Please check the file format.")
            
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
else:
    # Show example data structure when no file is uploaded
    st.info("Upload a CSV file to begin exploring the data.")
    
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