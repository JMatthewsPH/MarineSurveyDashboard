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
from datetime import datetime, timedelta
import numpy as np
import math
from plotly.subplots import make_subplots

# Import branding utilities
from utils.branding import display_logo, add_favicon

# Important: This page is intentionally ISOLATED from other parts of the application
# It doesn't use the shared DataProcessor or database connections to avoid
# any interference with the production dashboards

# Helper functions for dashboard-style visualizations

# Metrics calculation functions
def calculate_hard_coral_cover(substrate_df, site_name=None):
    """Calculate hard coral cover percentage from substrate data"""
    if substrate_df.empty:
        return pd.DataFrame(columns=['date', 'value'])

    # Convert date to datetime
    substrate_df['Date'] = pd.to_datetime(substrate_df['Date'])

    # Filter by site if specified
    if site_name:
        substrate_df = substrate_df[substrate_df['Site'].str.strip() == site_name.strip()]

    # Filter for valid surveys
    substrate_df = substrate_df[substrate_df['Survey_Status'] == 1]

    if substrate_df.empty:
        return pd.DataFrame(columns=['date', 'value'])

    # Group by survey ID and date
    coral_data = []

    for survey_id, survey_df in substrate_df.groupby(['Survey_ID', 'Date']):
        date = survey_df['Date'].iloc[0]
        site = survey_df['Site'].iloc[0].replace(' MPA', '').strip()

        # Calculate total points
        total_points = survey_df['Total'].sum()

        # Calculate hard coral cover
        hard_coral_points = survey_df[survey_df['Group'].str.contains('Hard Coral')]['Total'].sum()

        if total_points > 0:
            hard_coral_cover = (hard_coral_points / total_points) * 100
            coral_data.append({
                'date': date,
                'site': site,
                'value': hard_coral_cover
            })

    # Convert to DataFrame
    result_df = pd.DataFrame(coral_data)

    # If multiple surveys on same date for same site, average the values
    if not result_df.empty:
        result_df = result_df.groupby(['date', 'site']).agg({'value': 'mean'}).reset_index()

    return result_df

def calculate_fleshy_algae_cover(substrate_df, site_name=None):
    """Calculate fleshy algae cover percentage from substrate data"""
    if substrate_df.empty:
        return pd.DataFrame(columns=['date', 'value'])

    # Convert date to datetime
    substrate_df['Date'] = pd.to_datetime(substrate_df['Date'])

    # Filter by site if specified
    if site_name:
        substrate_df = substrate_df[substrate_df['Site'].str.strip() == site_name.strip()]

    # Filter for valid surveys
    substrate_df = substrate_df[substrate_df['Survey_Status'] == 1]

    if substrate_df.empty:
        return pd.DataFrame(columns=['date', 'value'])

    # Group by survey ID and date
    algae_data = []

    for survey_id, survey_df in substrate_df.groupby(['Survey_ID', 'Date']):
        date = survey_df['Date'].iloc[0]
        site = survey_df['Site'].iloc[0].replace(' MPA', '').strip()

        # Calculate total points
        total_points = survey_df['Total'].sum()

        # Calculate fleshy algae cover (exclude Coralline and Halimeda)
        fleshy_algae_points = survey_df[
            survey_df['Group'].str.contains('Algae') & 
            ~survey_df['Group'].str.contains('Coralline') & 
            ~survey_df['Group'].str.contains('Halimeda')
        ]['Total'].sum()

        if total_points > 0:
            fleshy_algae_cover = (fleshy_algae_points / total_points) * 100
            algae_data.append({
                'date': date,
                'site': site,
                'value': fleshy_algae_cover
            })

    # Convert to DataFrame
    result_df = pd.DataFrame(algae_data)

    # If multiple surveys on same date for same site, average the values
    if not result_df.empty:
        result_df = result_df.groupby(['date', 'site']).agg({'value': 'mean'}).reset_index()

    return result_df

def calculate_fish_biomass(fish_df, site_name=None):
    """
    Calculate commercial fish biomass from fish survey data

    Args:
        fish_df: Fish survey DataFrame
        site_name: Optional site name to filter

    Returns:
        DataFrame with date and value columns
    """
    if fish_df.empty:
        return pd.DataFrame(columns=['date', 'value'])

    # Convert date to datetime
    fish_df['Date'] = pd.to_datetime(fish_df['Date'])

    # Filter by site if specified
    if site_name:
        fish_df = fish_df[fish_df['Site'].str.strip() == site_name.strip()]

    # Filter for valid surveys
    if 'Survey_Status' in fish_df.columns:
        # Ensure Survey_Status is numeric for comparison
        fish_df['Survey_Status'] = pd.to_numeric(fish_df['Survey_Status'], errors='coerce').fillna(0).astype(int)
        fish_df = fish_df[fish_df['Survey_Status'] == 1]

    if fish_df.empty:
        return pd.DataFrame(columns=['date', 'value'])

    # Commercial fish families
    commercial_species = [
        'Snapper', 'Grouper', 'Sweetlips', 'Trevally', 'Barracuda', 
        'Emperor', 'Parrotfish', 'Rabbitfish', 'Surgeonfish',
        'Goatfish', 'Triggerfish', 'Tuna', 'Mackerel', 'Fusilier',
        'Unicornfish', 'Soldierfish', 'Bream', 'Big Eye', 'Bigeye'
    ]

    # Functions to convert size ranges to average sizes in cm
    def get_average_size(size_range):
        if pd.isna(size_range) or size_range == '':
            return 0
        try:
            # Handle ranges like "0-5" or "20-25"
            if isinstance(size_range, str) and '-' in size_range:
                lower, upper = map(float, size_range.split('-'))
                return (lower + upper) / 2
            # Handle single values
            return float(size_range)
        except (ValueError, TypeError):
            # If we can't convert to float, return 0
            return 0

    # Load species-specific length-weight parameters
    try:
        biomass_params_file = "attached_assets/Fish Data Analysis - Biomass CO.csv"
        if os.path.exists(biomass_params_file):
            biomass_params_df = pd.read_csv(biomass_params_file)
            # Convert to dictionary for faster lookups
            species_params = {}
            for _, row in biomass_params_df.iterrows():
                if pd.notna(row['Species']) and pd.notna(row['Coeff a']) and pd.notna(row['Coeff b']):
                    species_params[row['Species']] = (float(row['Coeff a']), float(row['Coeff b']))
        else:
            species_params = {}
    except Exception as e:
        st.warning(f"Error loading biomass parameters: {str(e)}")
        species_params = {}

    # Calculate biomass for each fish family using length-weight relationships
    # W = a * L^b where W is weight in grams, L is length in cm
    def calculate_weight(length, species=None, a=0.01, b=3.0):
        """
        Calculate weight in kg using length-weight relationship

        Args:
            length: Fish length in cm
            species: Species name to lookup specific parameters
            a, b: Default parameters if species-specific ones aren't found
        """
        # Try to get species-specific parameters
        if species and species in species_params:
            a, b = species_params[species]
        elif species and ' - ' in species:
            # Try family-level parameters
            family = species.split(' - ')[0]
            family_other = f"{family} - Other"

            if family_other in species_params:
                a, b = species_params[family_other]
            elif family in species_params:
                a, b = species_params[family]

        # Calculate weight
        weight_grams = a * (length ** b)
        return weight_grams / 1000  # Convert to kg

    # Calculate biomass for each survey
    biomass_data = []

    for survey_id, survey_df in fish_df.groupby(['Survey_ID', 'Date']):
        date = survey_df['Date'].iloc[0]
        site = survey_df['Site'].iloc[0].replace(' MPA', '').strip()

        # Filter commercial species
        commercial_fish = survey_df[survey_df['Species'].str.contains('|'.join(commercial_species), case=False)]

        if commercial_fish.empty:
            continue

        # Calculate biomass
        total_biomass = 0

        for _, fish in commercial_fish.iterrows():
            avg_size = get_average_size(fish['Size'])
            count = fish['Total']
            species = fish['Species']

            if avg_size > 0 and count > 0:
                # Biomass = number of fish * weight per fish
                fish_weight = calculate_weight(avg_size, species=species)
                biomass = count * fish_weight
                total_biomass += biomass

        # Standard transect area (in square meters)
        transect_area = 150  # 5m width x 30m length

        # Convert to biomass per 100m²
        biomass_per_100sqm = (total_biomass / transect_area) * 100

        biomass_data.append({
            'date': date,
            'site': site,
            'value': biomass_per_100sqm
        })

    # Convert to DataFrame
    result_df = pd.DataFrame(biomass_data)

    # If multiple surveys on same date for same site, average the values
    if not result_df.empty:
        result_df = result_df.groupby(['date', 'site']).agg({'value': 'mean'}).reset_index()

    return result_df

def calculate_fish_density(fish_df, fish_type, site_name=None):
    """
    Calculate fish density by type from fish survey data

    Args:
        fish_df: Fish survey DataFrame
        fish_type: Type of fish ('herbivore', 'carnivore', 'omnivore', 'corallivore')
        site_name: Optional site name to filter

    Returns:
        DataFrame with date and value columns
    """
    if fish_df.empty:
        return pd.DataFrame(columns=['date', 'value'])

    # Convert date to datetime
    fish_df['Date'] = pd.to_datetime(fish_df['Date'])

    # Filter by site if specified
    if site_name:
        fish_df = fish_df[fish_df['Site'].str.strip() == site_name.strip()]

    # Filter for valid surveys
    if 'Survey_Status' in fish_df.columns:
        # Ensure Survey_Status is numeric for comparison
        fish_df['Survey_Status'] = pd.to_numeric(fish_df['Survey_Status'], errors='coerce').fillna(0).astype(int)
        fish_df = fish_df[fish_df['Survey_Status'] == 1]

    if fish_df.empty:
        return pd.DataFrame(columns=['date', 'value'])

    # Fish categorization dictionary
    fish_categories = {
        'herbivore': [
            'Parrotfish', 'Surgeonfish', 'Rabbitfish', 'Damselfish', 
            'Angelfish', 'Butterflyfish'
        ],
        'carnivore': [
            'Snapper', 'Grouper', 'Sweetlips', 'Trevally', 'Barracuda', 
            'Emperor', 'Shark', 'Tuna', 'Mackerel', 'Squirrelfish'
        ],
        'omnivore': [
            'Wrasse', 'Goatfish', 'Triggerfish', 'Bream', 'Basslet', 
            'Dottyback', 'Fusilier', 'Bannerfish', 'Trumpetfish'
        ],
        'corallivore': [
            'Butterflyfish'
        ]
    }

    # Get target fish species
    target_species = fish_categories.get(fish_type.lower(), [])

    if not target_species:
        return pd.DataFrame(columns=['date', 'value'])

    # Calculate fish density for each survey
    density_data = []

    for survey_id, survey_df in fish_df.groupby(['Survey_ID', 'Date']):
        date = survey_df['Date'].iloc[0]
        site = survey_df['Site'].iloc[0].replace(' MPA', '').strip()

        # Filter for target species
        target_fish = survey_df[survey_df['Species'].str.contains('|'.join(target_species), case=False)]

        # Calculate total count
        total_count = target_fish['Total'].sum()

        # Standard transect area (in square meters)
        transect_area = 150  # 5m width x 30m length

        # Convert to density per 100m²
        density = (total_count / transect_area) * 100

        density_data.append({
            'date': date,
            'site': site,
            'value': density
        })

    # Convert to DataFrame
    result_df = pd.DataFrame(density_data)

    # If multiple surveys on same date for same site, average the values
    if not result_df.empty:
        result_df = result_df.groupby(['date', 'site']).agg({'value': 'mean'}).reset_index()

    return result_df
def format_season(date_obj):
    """Convert date to season format, matching the Site Dashboard"""
    month = date_obj.month
    year = date_obj.year

    if 3 <= month <= 5:  # Q1: MAR-MAY
        return f'MAR-MAY {year}'
    elif 6 <= month <= 8:  # Q2: JUN-AUG
        return f'JUN-AUG {year}'
    elif 9 <= month <= 11:  # Q3: SEP-NOV
        return f'SEP-NOV {year}'
    else:  # Q4: DEC-FEB
        # If it's December, it's the start of Q4 for next year
        if month == 12:
            return f'DEC-FEB {year + 1}'
        # If it's January or February, it's end of Q4 for current year
        return f'DEC-FEB {year}'

def get_quarter(date_obj):
    """Get the quarter/season for a date for grouping"""
    month = date_obj.month
    year = date_obj.year

    if 3 <= month <= 5:  # Q1: MAR-MAY
        return (year, 1)
    elif 6 <= month <= 8:  # Q2: JUN-AUG
        return (year, 2)
    elif 9 <= month <= 11:  # Q3: SEP-NOV
        return (year, 3)
    else:  # Q4: DEC-FEB
        # If December, it's the start of Q4 for the next year
        if month == 12:
            return (year + 1, 4)
        # If January or February, it's end of Q4 for current year
        return (year, 4)

def create_dashboard_time_series(data, title, y_label, show_confidence_interval=False):
    """
    Create a time series chart similar to Site Dashboard, with 
    consistent styling and optional confidence intervals

    Args:
        data: DataFrame with 'date' and 'value' columns
        title: Chart title
        y_label: Y-axis label
        show_confidence_interval: Whether to display confidence intervals
    """
    # Create base figure
    fig = go.Figure()

    # Configure chart options for mobile responsiveness
    config = {
        'displaylogo': False,
        'responsive': True,
        'displayModeBar': True,
        # Define the exact buttons to show: zoom in, zoom out, reset view, download
        'modeBarButtons': [['zoomIn2d', 'zoomOut2d', 'resetScale2d', 'toImage']],
        'scrollZoom': False,  # Disable scroll zoom on mobile to prevent accidental zooming
        'doubleClick': 'reset',  # Double tap to reset the view
        'showTips': True,  # Show tips for better usability
        'displayModeBar': 'hover'  # Only show mode bar on hover to save space
    }

    # If no data, return empty figure
    if data.empty:
        return fig, config

    # Sort data by date
    data = data.sort_values('date')

    # Format dates as seasons for labels
    data['season'] = data['date'].apply(format_season)

    # Add the main line
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['value'],
        mode='lines+markers',
        name=y_label,
        line=dict(width=2, color='rgb(0, 123, 255)'),
        marker=dict(size=6, color='rgb(0, 123, 255)')
    ))

    # Add confidence interval if requested
    if show_confidence_interval and len(data) > 1:
        # Calculate 95% confidence interval
        values = data['value'].values
        n = len(values)
        std_err = np.std(values, ddof=1) / np.sqrt(n)
        t_value = 1.96  # Approximately 95% CI
        ci = t_value * std_err

        # Ensure lower bound doesn't go below zero (important for percentages)
        lower_bound = np.maximum(0, data['value'] - ci)
        upper_bound = data['value'] + ci

        # Add confidence interval as a filled area
        fig.add_trace(go.Scatter(
            x=data['date'].tolist() + data['date'].tolist()[::-1],
            y=upper_bound.tolist() + lower_bound.tolist()[::-1],
            fill='toself',
            fillcolor='rgba(0, 123, 255, 0.2)',
            line=dict(color='rgba(255, 255, 255, 0)'),
            hoverinfo="skip",
            showlegend=False
        ))

    # Layout styling to match dashboard
    fig.update_layout(
        title=title,
        xaxis_title='Survey Date',
        yaxis_title=y_label,
        hovermode='closest',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=10, r=10, t=50, b=50),
        height=450,
        plot_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12)
    )

    # Configure axis styling
    fig.update_xaxes(
        tickangle=45,
        tickfont=dict(size=10),
        gridcolor='lightgray',
        showgrid=True
    )

    fig.update_yaxes(
        gridcolor='lightgray',
        showgrid=True,
        zeroline=True,
        zerolinecolor='lightgray',
        zerolinewidth=1
    )

    return fig, config

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

    # Filter for valid rows based on Survey_Status = 1
    if 'Survey_Status' in df.columns:
        valid_count = df[df['Survey_Status'] == 1].shape[0]
        invalid_count = df[df['Survey_Status'] != 1].shape[0]
        total_count = df.shape[0]

        # Filter the DataFrame
        df = df[df['Survey_Status'] == 1]

        # Show notice about filtering
        if invalid_count > 0:
            st.info(f"Filtered data to include only valid surveys (Survey_Status = 1). Removed {invalid_count} of {total_count} rows ({(invalid_count/total_count*100):.1f}%).")
    else:
        st.warning("'Survey_Status' column not found in the dataset. Unable to filter for valid surveys.")

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

    # Hide filtered dataframe (removed as requested)
    if len(filtered_df) > 0:
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

    # Filter for valid rows based on Survey_Status = 1
    if 'Survey_Status' in df.columns:
        valid_count = df[df['Survey_Status'] == 1].shape[0]
        invalid_count = df[df['Survey_Status'] != 1].shape[0]
        total_count = df.shape[0]

        # Filter the DataFrame
        df = df[df['Survey_Status'] == 1]

        # Show notice about filtering
        if invalid_count > 0:
            st.info(f"Filtered data to include only valid surveys (Survey_Status = 1). Removed {invalid_count} of {total_count} rows ({(invalid_count/total_count*100):.1f}%).")
    else:
        st.warning("'Survey_Status' column not found in the dataset. Unable to filter for valid surveys.")

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

    # Hide filtered dataframe (removed as requested)
    if len(filtered_df) > 0:
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

    # Filter for valid rows based on Survey_Status = 1
    if 'Survey_Status' in df.columns:
        valid_count = df[df['Survey_Status'] == 1].shape[0]
        invalid_count = df[df['Survey_Status'] != 1].shape[0]
        total_count = df.shape[0]

        # Filter the DataFrame
        df = df[df['Survey_Status'] == 1]

        # Show notice about filtering
        if invalid_count > 0:
            st.info(f"Filtered data to include only valid surveys (Survey_Status = 1). Removed {invalid_count} of {total_count} rows ({(invalid_count/total_count*100):.1f}%).")
    else:
        st.warning("'Survey_Status' column not foundin the dataset. Unable to filter for valid surveys.")

    # Display basic info
    st.subheader("Dataset Overview")

    # Basic statistics
    num_surveys = df['Survey_ID'].nunique()
    num_sites = df['Site'].unique()
    num_substrate_types = df['Group'].nunique() if 'Group' in df.columns else 0
    date_range = f"{df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Number of Surveys", num_surveys)
    col2.metric("Number of Sites", len(num_sites))
    col3.metric("Number of Substrate Types", num_substrate_types)
    col4.metric("Date Range", date_range)

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

    # Hide filtered dataframe (removed as requested)
    if len(filtered_df) > 0:
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

            # Add dashboard-style analysis options
            dashboard_show_ci = st.checkbox("Show Confidence Interval", value=False, 
                                        help="Display 95% confidence interval bands around the trend lines",
                                        key="dashboard_ci")

            # Initialize site_name_to_use as None, will be updated in the else block if needed
            site_name_to_use = None

            # Check if we're already in the context of a file analysis
            # In that case, use the selected_site from the analysis section if it's not "All Sites"
            if 'selected_site' in locals() and selected_site != "All Sites":
                site_name_to_use = selected_site

            if site_name_to_use:
                st.subheader(f"Ecological Health Indicators for {site_name_to_use}")

                # Calculate metrics using our helper functions
                site_coral_data = calculate_hard_coral_cover(df, site_name_to_use)
                site_algae_data = calculate_fleshy_algae_cover(df, site_name_to_use)
                site_fish_data = calculate_fish_biomass(df, site_name_to_use)

                # Check if we have any fish data
                have_fish_data = not site_fish_data.empty if isinstance(site_fish_data, pd.DataFrame) else False

                # Create two column layout for the charts
                col1, col2 = st.columns(2)

                with col1:
                    # Hard coral cover chart
                    if not site_coral_data.empty:
                        fig, config = create_dashboard_time_series(
                            site_coral_data,
                            f"Hard Coral Cover", 
                            "Hard Coral Cover (%)",
                            dashboard_show_ci
                        )
                        st.plotly_chart(fig, config=config, use_container_width=True)
                    else:
                        st.info("No hard coral cover data available for the selected site.")

                with col2:
                    # Fleshy algae cover chart
                    if not site_algae_data.empty:
                        fig, config = create_dashboard_time_series(
                            site_algae_data,
                            f"Fleshy Algae Cover", 
                            "Fleshy Algae Cover (%)",
                            dashboard_show_ci
                        )
                        st.plotly_chart(fig, config=config, use_container_width=True)
                    else:
                        st.info("No fleshy algae cover data available for the selected site.")

                # Add fish biomass chart if data is available
                if have_fish_data:
                    st.subheader("Fish Biomass & Density")
                    col3, col4 = st.columns(2)

                    with col3:
                        fig, config = create_dashboard_time_series(
                            site_fish_data,
                            f"Commercial Fish Biomass",
                            "Biomass (kg/100m²)",
                            dashboard_show_ci
                        )
                        st.plotly_chart(fig, config=config, use_container_width=True)

                    # Add fish density chart
                    with col4:
                        # Calculate herbivore density for the site
                        herbivore_density = calculate_fish_density(df, 'herbivore', site_name_to_use)
                        if not herbivore_density.empty:
                            fig, config = create_dashboard_time_series(
                                herbivore_density,
                                f"Herbivore Density",
                                "Density (per 100m²)",
                                dashboard_show_ci
                            )
                            st.plotly_chart(fig, config=config, use_container_width=True)
                        else:
                            st.info("No herbivore density data available for the selected site.")

                # Add interpretation guidance
                st.markdown("""
                **Ecological Indicator Interpretation:**

                **Hard Coral Cover:**
                - **0-25%**: Poor condition - Significant coral loss
                - **25-50%**: Fair condition - Moderate coral coverage
                - **50-75%**: Good condition - Healthy coral coverage
                - **75-100%**: Excellent condition - Very high coral coverage

                **Fleshy Algae Cover:**
                - High percentages typically indicate nutrient pollution or lack of herbivores
                - Values over 20% may suggest an ecological phase shift

                **Commercial Fish Biomass:**
                - Higher values indicate healthier reef systems with intact food webs
                - Sudden decreases may indicate overfishing or other disturbances

                **Herbivore Density:**
                - Critical for controlling algae growth and maintaining reef balance
                - Low herbivore density combined with high algae cover indicates ecological imbalance
                """)
            else:
                st.info("Please select a specific site to view dashboard-style charts with our live survey data.")

                # Show available sites with an interactive selector
                if len(df['Site'].unique()) > 0:
                    st.subheader("Available Sites")
                    st.write("Select one of the following sites to view dashboard-style charts:")

                    # Interactive site selector specific for the dashboard tab
                    dashboard_selected_site = st.selectbox(
                        "Select a site",
                        options=list(df['Site'].unique()),
                        key="dashboard_site_selector"
                    )

                    # Update the site_name_to_use variable with the selection
                    site_name_to_use = dashboard_selected_site

            # Keep the legacy visualization code for reference, but hidden
            if False and not metrics_df.empty:
                # Define the dashboard_metric for the legacy code
                dashboard_metric = 'Hard_Coral_Cover'
                # Define show_ci for the legacy code
                show_ci = dashboard_show_ci
                # Add metric_options for the legacy code
                metric_options = {
                    'Hard_Coral_Cover': 'Hard Coral Cover (%)',
                    'Algae_Cover': 'Algae Cover (%)',
                    'Fleshy_Algae_Cover': 'Fleshy Algae Cover (%)',
                    'Rubble_Cover': 'Rubble Cover (%)'
                }

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

                # First, format the dates to quarterly or monthly representation
                # Add a quarter column for better display
                ci_df['Year'] = ci_df['Date'].dt.year
                ci_df['Month'] = ci_df['Date'].dt.month
                ci_df['Quarter'] = ci_df['Date'].dt.quarter
                ci_df['YearQuarter'] = ci_df['Year'].astype(str) + 'Q' + ci_df['Quarter'].astype(str)

                # Group by year-quarter if there are many dates
                if len(ci_df) > 10:
                    # Instead of using individual dates, use quarter midpoints
                    grouped_df = ci_df.groupby('YearQuarter').agg({
                        'Date': 'min',  # Use the first date of each quarter
                        'mean': 'mean',
                        'ci_lower': 'mean',
                        'ci_upper': 'mean'
                    }).reset_index()

                    # Use the grouping for display
                    display_dates = grouped_df['Date']
                    display_means = grouped_df['mean']
                    display_lower = grouped_df['ci_lower'] 
                    display_upper = grouped_df['ci_upper']

                    # Create quarterly date labels
                    date_labels = grouped_df['YearQuarter']
                else:
                    # If few dates, use original data
                    display_dates = ci_df['Date']
                    display_means = ci_df['mean']
                    display_lower = ci_df['ci_lower']
                    display_upper = ci_df['ci_upper']

                    # Format date labels as YYYY-MM
                    date_labels = ci_df['Date'].dt.strftime('%Y-%m')

                # Add the main line
                fig.add_trace(go.Scatter(
                    x=display_dates,
                    y=display_means,
                    mode='lines+markers',
                    name=metric_options[dashboard_metric],
                    line=dict(width=2, color='rgba(31, 119, 180, 1)'),
                    marker=dict(size=8),
                    text=date_labels,  # Add formatted date labels to hover text
                    hovertemplate='%{text}<br>Value: %{y:.1f}%<extra></extra>'
                ))

                # Add confidence interval as a shaded area
                if show_ci:
                    fig.add_trace(go.Scatter(
                        x=pd.concat([display_dates, display_dates.iloc[::-1]]),
                        y=pd.concat([display_upper, display_lower.iloc[::-1]]),
                        fill='toself',
                        fillcolor='rgba(31, 119, 180, 0.2)',
                        line=dict(color='rgba(255,255,255,0)'),
                        hoverinfo='skip',
                        showlegend=False
                    ))

                # Set custom tick values for cleaner x-axis
                if len(display_dates) > 10:
                    # For many dates, show quarters only at year boundaries
                    tick_indices = [i for i, date in enumerate(display_dates) if date.month == 1 or i == 0 or i == len(display_dates)-1]
                    tick_vals = [display_dates.iloc[i] for i in tick_indices]
                    tick_texts = [date_labels.iloc[i] for i in tick_indices]
                else:
                    # For few dates, show all
                    tick_vals = display_dates
                    tick_texts = date_labels

                # Customize layout
                fig.update_layout(
                    title=f"{metric_options[dashboard_metric]} Over Time (Dashboard Style)",
                    xaxis_title="Survey Date",
                    yaxis_title=metric_options[dashboard_metric],
                    legend_title="Metric",
                    yaxis=dict(range=[0, 100]),
                    margin=dict(l=40, r=20, t=60, b=40),
                    plot_bgcolor='white',
                    xaxis=dict(
                        tickvals=tick_vals,
                        ticktext=tick_texts,
                        tickangle=45
                    )
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

                # Add COVID-19 period marker (March 2020 - December 2021)
                covid_start = np.datetime64('2020-03-01')
                covid_end = np.datetime64('2021-12-31')

                # Only add the marker if the date range includes the COVID period
                if (ci_df['Date'].min() < covid_end) and (ci_df['Date'].max() > covid_start):
                    # Add vertical lines for COVID period
                    fig.add_vline(x=covid_start, line_dash="dash", line_color="gray")
                    fig.add_vline(x=covid_end, line_dash="dash", line_color="gray")

                    # Add annotation for COVID period
                    fig.add_annotation(
                        x=(covid_start + (covid_end - covid_start)/2),
                        y=95,  # Position near the top
                        text="COVID-19 Period",
                        showarrow=False,
                        font=dict(size=12, color="gray")
                    )

                    # Create separate traces with different line styles for pre-COVID, COVID, and post-COVID periods
                    # First, filter the data into the three periods
                    pre_covid_df = ci_df[ci_df['Date'] < covid_start]
                    covid_df = ci_df[(ci_df['Date'] >= covid_start) & (ci_df['Date'] <= covid_end)]
                    post_covid_df = ci_df[ci_df['Date'] > covid_end]

                    # Clear the previous trace and add the new segmented traces
                    fig.data = []

                    # Add pre-COVID period (solid line)
                    if not pre_covid_df.empty:
                        fig.add_trace(go.Scatter(
                            x=pre_covid_df['Date'],
                            y=pre_covid_df['Value'],
                            mode='lines',
                            name=dashboard_metric,
                            line=dict(color='blue', width=2)
                        ))

                    # Add COVID period (dashed line)
                    if not covid_df.empty:
                        fig.add_trace(go.Scatter(
                            x=covid_df['Date'],
                            y=covid_df['Value'],
                            mode='lines',
                            name=f"{dashboard_metric} (COVID)",
                            line=dict(color='blue', width=2, dash='dash')
                        ))

                    # Add post-COVID period (solid line)
                    if not post_covid_df.empty:
                        fig.add_trace(go.Scatter(
                            x=post_covid_df['Date'],
                            y=post_covid_df['Value'],
                            mode='lines',
                            name=dashboard_metric,
                            line=dict(color='blue', width=2)
                        ))

                    # If confidence intervals are present, add them for each period
                    if 'CI_Lower' in ci_df.columns and 'CI_Upper' in ci_df.columns:
                        # Add confidence intervals for pre-COVID
                        if not pre_covid_df.empty:
                            fig.add_trace(go.Scatter(
                                x=pre_covid_df['Date'].tolist() + pre_covid_df['Date'].tolist()[::-1],
                                y=pre_covid_df['CI_Upper'].tolist() + pre_covid_df['CI_Lower'].tolist()[::-1],
                                fill='toself',
                                fillcolor='rgba(0, 0, 255, 0.2)',
                                line=dict(color='rgba(255, 255, 255, 0)'),
                                hoverinfo='skip',
                                showlegend=False
                            ))

                        # Add confidence intervals for COVID
                        if not covid_df.empty:
                            fig.add_trace(go.Scatter(
                                x=covid_df['Date'].tolist() + covid_df['Date'].tolist()[::-1],
                                y=covid_df['CI_Upper'].tolist() + covid_df['CI_Lower'].tolist()[::-1],
                                fill='toself',
                                fillcolor='rgba(0, 0, 255, 0.2)',
                                line=dict(color='rgba(255, 255, 255, 0)'),
                                hoverinfo='skip',
                                showlegend=False
                            ))

                        # Add confidence intervals for post-COVID
                        if not post_covid_df.empty:
                            fig.add_trace(go.Scatter(
                                x=post_covid_df['Date'].tolist() + post_covid_df['Date'].tolist()[::-1],
                                y=post_covid_df['CI_Upper'].tolist() + post_covid_df['CI_Lower'].tolist()[::-1],
                                fill='toself',
                                fillcolor='rgba(0, 0, 255, 0.2)',
                                line=dict(color='rgba(255, 255, 255, 0)'),
                                hoverinfo='skip',
                                showlegend=False
                            ))

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

    # Filter for valid rows based on Survey_Status = 1
    if 'Survey_Status' in df.columns:
        valid_count = df[df['Survey_Status'] == 1].shape[0]
        invalid_count = df[df['Survey_Status'] != 1].shape[0]
        total_count = df.shape[0]

        # Filter the DataFrame
        df = df[df['Survey_Status'] == 1]

        # Show notice about filtering
        if invalid_count > 0:
            st.info(f"Filtered data to include only valid surveys (Survey_Status = 1). Removed {invalid_count} of {total_count} rows ({(invalid_count/total_count*100):.1f}%).")
    else:
        st.warning("'Survey_Status' column not found in the dataset. Unable to filter for valid surveys.")

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

    # Hide filtered dataframe (removed as requested)
    if len(filtered_df) > 0:
        # Calculate fish metrics
        st.subheader("Calculated Metrics")

        # Group by survey ID to analyze each survey separately
        survey_groups = filtered_df.groupby('Survey_ID')

        survey_metrics = []
        commercial_metrics = []

        # Commercial fish families/species list
        commercial_species = [
            'Snapper', 'Grouper', 'Sweetlips', 'Trevally', 'Barracuda', 
            'Emperor', 'Parrotfish', 'Rabbitfish', 'Surgeonfish',
            'Goatfish', 'Triggerfish', 'Tuna', 'Mackerel', 'Fusilier',
            'Unicornfish', 'Soldierfish', 'Bream', 'Big Eye', 'Bigeye'
        ]

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
                        # Handle None or NaN values
                        if pd.isna(size_range):
                            return None

                        # Convert to string if numeric
                        if not isinstance(size_range, str):
                            try:
                                # If it's already a number, just return it as float
                                return float(size_range)
                            except (ValueError, TypeError):
                                return None

                        # Handle range format (e.g., "5-10")
                        if '-' in size_range:
                            parts = size_range.split('-')
                            try:
                                min_size = float(parts[0])
                                max_size = float(parts[1])
                                return (min_size + max_size) / 2
                            except (ValueError, IndexError):
                                return None

                        # Handle single value as string
                        try:
                            return float(size_range)
                        except (ValueError, TypeError):
                            return None

                    survey_data['Average_Size'] = survey_data['Size'].apply(get_average_size)

                    # Load species-specific length-weight parameters
                    try:
                        # Load coefficients from CSV file
                        biomass_params_file = "attached_assets/Fish Data Analysis - Biomass CO.csv"
                        if os.path.exists(biomass_params_file):
                            biomass_params_df = pd.read_csv(biomass_params_file)
                            # Convert to dictionary for faster lookups
                            biomass_params = {}
                            for _, row in biomass_params_df.iterrows():
                                if pd.notna(row['Species']) and pd.notna(row['Coeff a']) and pd.notna(row['Coeff b']):
                                    biomass_params[row['Species']] = (float(row['Coeff a']), float(row['Coeff b']))
                        else:
                            st.warning(f"Biomass parameters file not found: {biomass_params_file}")
                            biomass_params = {}
                    except Exception as e:
                        st.warning(f"Error loading biomass parameters: {str(e)}")
                        biomass_params = {}

                    # Calculate weight for each fish species
                    total_biomass = 0
                    commercial_biomass = 0

                    # Identify commercial fish species
                    is_commercial = survey_data['Species'].str.contains('|'.join(commercial_species), case=False, na=False)
                    commercial_fish = survey_data[is_commercial]

                    # Calculate biomass for each row (species)
                    for _, fish in survey_data.iterrows():
                        species = fish['Species']
                        count = fish['Total']
                        avg_size = fish['Average_Size']

                        if pd.isna(avg_size) or pd.isna(count) or avg_size <= 0 or count <= 0:
                            continue

                        # Make sure avg_size is a number
                        try:
                            avg_size = float(avg_size)
                        except (ValueError, TypeError):
                            # Skip this fish if size can't be converted to float
                            continue

                        # Look for exact species match first, then try partial match, then default values
                        if species in biomass_params:
                            a, b = biomass_params[species]
                        else:
                            # Try to find partial match (e.g., "Parrotfish - XXX" matches "Parrotfish - Other")
                            found = False
                            if ' - ' in species:
                                family = species.split(' - ')[0]
                                family_other = f"{family} - Other"

                                if family_other in biomass_params:
                                    a, b = biomass_params[family_other]
                                    found = True
                                elif family in biomass_params:
                                    a, b = biomass_params[family]
                                    found = True

                            if not found:
                                # Default values if no match is found
                                a, b = 0.01, 3.0

                        # Calculate weight in grams
                        weight_grams = a * (avg_size ** b)
                        weight_kg = weight_grams / 1000  # Convert to kg

                        # Add to total biomass
                        biomass = weight_kg * count
                        total_biomass += biomass

                        # Check if this is a commercial species
                        if isinstance(species, str) and any(comm_sp in species for comm_sp in commercial_species):
                            commercial_biomass += biomass

                    # Calculate biomass per 100m²
                    transect_area = 150  # 5m width x 30m length
                    commercial_biomass_per_100sqm = (commercial_biomass / transect_area) * 100

                    # Add to commercial metrics for quarter analysis
                    quarter = get_quarter(pd.to_datetime(date))
                    commercial_metrics.append({
                        'Survey_ID': survey_id,
                        'Site': site,
                        'Date': pd.to_datetime(date),
                        'Quarter': quarter,
                        'QuarterLabel': format_season(pd.to_datetime(date)),
                        'Commercial_Biomass': commercial_biomass_per_100sqm
                    })

                    # Store total biomass in grams
                    survey_data['Total_Biomass'] = total_biomass * 1000  # Store in grams for consistency
                except Exception as e:
                    total_biomass = None
                    commercial_biomass = None
                    st.warning(f"Could not calculate biomass: {str(e)}")
            else:
                total_biomass = None
                commercial_biomass = None

            # Add to metrics list
            survey_metrics.append({
                'Survey_ID': survey_id,
                'Site': site,
                'Date': date,
                'Total_Fish': total_fish,
                'Total_Biomass': total_biomass,
                'Commercial_Biomass': commercial_biomass if 'commercial_biomass' in locals() and commercial_biomass is not None else None
            })

        # Convert to DataFrame
        metrics_df = pd.DataFrame(survey_metrics)

        # Display individual survey metrics
        st.subheader("Survey Metrics")
        st.dataframe(metrics_df, use_container_width=True)

        # Calculate and display average commercial biomass by quarter
        if len(commercial_metrics) > 0:
            commercial_df = pd.DataFrame(commercial_metrics)

            # Group by quarter and calculate average
            quarterly_biomass = commercial_df.groupby(['QuarterLabel', 'Quarter', 'Site'])['Commercial_Biomass'].agg(
                avg_biomass=('mean'),
                num_surveys=('count')
            ).reset_index()

            # Sort by date (quarter)
            quarterly_biomass = quarterly_biomass.sort_values(by=['Quarter'])

            # Display the quarterly data
            st.subheader("Average Commercial Biomass by Quarter")
            st.write("Commercial biomass per 100m² averaged by 3-month survey periods")

            # Get unique sites for comparison selection
            available_sites = sorted(commercial_df['Site'].unique())

            # Add site selection filters similar to Site Dashboard
            col1, col2 = st.columns([1, 1])

            with col1:
                primary_site = st.selectbox(
                    "Select Primary Site", 
                    available_sites,
                    index=0 if available_sites else None,
                    key="biomass_primary_site"
                )

            with col2:
                comparison_sites = st.multiselect(
                    "Select Sites to Compare", 
                    [site for site in available_sites if site != primary_site],
                    key="biomass_comparison_sites"
                )

            # Create a list of sites to display
            sites_to_display = [primary_site] + comparison_sites

            # Add view type selector
            view_type = st.radio(
                "Select View Type",
                ["Quarterly Averages", "Annual Trends", "Size Distribution"],
                horizontal=True,
                key="biomass_view_type"
            )

            # Filter data for selected sites
            filtered_data = commercial_df[commercial_df['Site'].isin(sites_to_display)]

            if view_type == "Quarterly Averages":
                # Filter and sort quarterly averages
                filtered_quarterly = quarterly_biomass[quarterly_biomass['Site'].isin(sites_to_display)]
                filtered_quarterly = filtered_quarterly.sort_values(by=['Quarter'])

                # Create quarterly bar chart
                fig = px.bar(
                    filtered_quarterly,
                    x='QuarterLabel',
                    y='avg_biomass',
                    color='Site',
                    labels={
                        'QuarterLabel': 'Survey Period',
                        'avg_biomass': 'Average Commercial Biomass (kg/100m²)',
                        'Site': 'Site'
                    },
                    title='Average Commercial Fish Biomass by Quarter',
                    hover_data=['num_surveys'],
                    color_discrete_sequence=px.colors.qualitative.G10
                )

            elif view_type == "Annual Trends":
                # Calculate annual averages
                filtered_data['Year'] = pd.to_datetime(filtered_data['Date']).dt.year
                annual_trends = filtered_data.groupby(['Year', 'Site'])['Commercial_Biomass'].agg(
                    avg_biomass=('mean'),
                    num_surveys=('count')
                ).reset_index()

                # Create line chart for trends
                fig = px.line(
                    annual_trends,
                    x='Year',
                    y='avg_biomass',
                    color='Site',
                    labels={
                        'Year': 'Year',
                        'avg_biomass': 'Average Commercial Biomass (kg/100m²)',
                        'Site': 'Site'
                    },
                    title='Annual Commercial Fish Biomass Trends',
                    hover_data=['num_surveys'],
                    markers=True
                )

            else:  # Size Distribution
                # Check if we have size data
                if 'Average_Size' not in filtered_data.columns:
                    # We need to calculate average size from the raw data
                    # Add error handling for the case where Size column contains non-numeric values
                    st.info("Processing size data...")
                    
                    def get_avg_size(size_range):
                        """Convert size ranges to numeric values"""
                        if pd.isna(size_range):
                            return None
                            
                        try:
                            # If already numeric, return as float
                            if isinstance(size_range, (int, float)):
                                return float(size_range)
                                
                            # Clean the string and handle common formatting issues
                            size_str = str(size_range).strip().replace(' ', '')
                            
                            # Handle range format (e.g. "5-10" or "5 - 10")
                            if '-' in size_str:
                                try:
                                    parts = size_str.split('-')
                                    if len(parts) == 2:
                                        low = float(parts[0].strip())
                                        high = float(parts[1].strip())
                                        if low <= high:
                                            return (low + high) / 2
                                except:
                                    pass
                                    
                            # Try direct conversion for single values
                            try:
                                return float(size_str)
                            except:
                                return None
                                
                        except (ValueError, TypeError, AttributeError):
                            return None
                            
                        return None
                            
                    # Create size categories
                    try:
                        # Ensure Size column exists
                        if 'Size' not in filtered_data.columns:
                            st.error("Size column not found in the dataset")
                            return
                            
                        # Convert sizes to numeric values
                        filtered_data['Average_Size'] = filtered_data['Size'].apply(get_avg_size)
                        
                        # Report conversion statistics
                        total_rows = len(filtered_data)
                        converted_rows = filtered_data['Average_Size'].notna().sum()
                        if converted_rows < total_rows:
                            st.info(f"Successfully converted {converted_rows} of {total_rows} size values. {total_rows - converted_rows} values could not be converted.")
                        
                        # Remove rows where size conversion failed
                        filtered_data = filtered_data.dropna(subset=['Average_Size'])
                    except Exception as e:
                        st.error(f"Error calculating average sizes: {str(e)}. Using raw 'Size' column instead.")
                        # Fall back to using the raw Size column for grouping
                        size_dist = filtered_data.groupby(['Site', 'Size'])['Total'].sum().reset_index()
                        
                        # Create bar chart
                        fig = px.bar(
                            size_dist,
                            x='Size',
                            y='Total',
                            color='Site',
                            barmode='group',
                            labels={
                                'Size': 'Size Range (cm)',
                                'Total': 'Number of Fish',
                                'Site': 'Site'
                            },
                            title='Commercial Fish Size Distribution'
                        )
                        
                        # Skip the rest of the Size Distribution code since we're handling it differently
                        try:
                            # Update layout for better mobile viewing
                            fig.update_layout(
                                xaxis_tickangle=45,
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                margin=dict(l=10, r=10, t=50, b=100)
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error displaying chart: {str(e)}")
                        
                        # Skip the rest of this branch by returning from this function
                        return
                
                # Only continue here if we successfully have Average_Size
                try:
                    # Calculate size distribution
                    filtered_data['Size_Category'] = pd.cut(
                        pd.to_numeric(filtered_data['Average_Size'], errors='coerce'),
                        bins=[0, 10, 20, 30, 40, 50, float('inf')],
                        labels=['0-10 cm', '11-20 cm', '21-30 cm', '31-40 cm', '41-50 cm', '>50 cm']
                    )

                    size_dist = filtered_data.groupby(['Site', 'Size_Category'])['Total'].sum().reset_index()
                except Exception as e:
                    st.error(f"Error categorizing sizes: {str(e)}. Using raw 'Size' column instead.")
                    # Fall back to using the raw Size column
                    size_dist = filtered_data.groupby(['Site', 'Size'])['Total'].sum().reset_index()

                # Create size distribution chart
                x_column = 'Size_Category' if 'Size_Category' in size_dist.columns else 'Size'
                x_label = 'Size Range' if x_column == 'Size_Category' else 'Size Range (cm)'
                
                fig = px.bar(
                    size_dist,
                    x=x_column,
                    y='Total',
                    color='Site',
                    barmode='group',
                    labels={
                        x_column: x_label,
                        'Total': 'Number of Fish',
                        'Site': 'Site'
                    },
                    title='Commercial Fish Size Distribution'
                )

            # Update hover template to show number of surveys
            try:
                if view_type in ["Quarterly Averages", "Annual Trends"]:
                    fig.update_traces(
                        hovertemplate='<b>%{x}</b><br>' +
                                     'Site: %{color}<br>' +
                                     'Avg. Biomass: %{y:.2f} kg/100m²<br>' +
                                     'Number of Surveys: %{customdata[0]}'
                    )
            except Exception as e:
                # Skip hover template update if there's an error
                pass

            # Update layout for better mobile viewing
            fig.update_layout(
                xaxis_tickangle=45,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=10, r=10, t=50, b=100)
            )

            st.plotly_chart(fig, use_container_width=True)

            # Add explanation of calculation
            st.info("""
            **How is this calculated?**
            1. For each survey, we calculate the commercial fish biomass based on species-specific length-weight relationships.
            2. Commercial fish include: Snapper, Grouper, Sweetlips, Trevally, Barracuda, Emperor, Parrotfish, Rabbitfish, Surgeonfish, Goatfish, Triggerfish, Tuna, Mackerel, Fusilier, Unicornfish, Soldierfish, Bream, and Big Eye.
            3. Surveys are grouped into 3-month periods (quarters) by season, or annually.
            4. The average biomass is calculated by dividing the total commercial biomass by the number of surveys in each period.
            5. Results are standardized to kg per 100m² for comparison across sites.
            """)

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
def filter_valid_surveys(df):
    """
    Filter dataframe to include only rows with Survey_Status = 1
    Ensures numeric conversion of Survey_Status column to avoid string comparison issues

    Args:
        df: Pandas DataFrame to filter

    Returns:
        Tuple of (filtered_df, valid_count, invalid_count, total_count)
    """
    if 'Survey_Status' not in df.columns:
        return df, 0, 0, df.shape[0]

    # Ensure Survey_Status is numeric for comparison
    df['Survey_Status'] = pd.to_numeric(df['Survey_Status'], errors='coerce').fillna(0).astype(int)

    # Get counts for reporting
    valid_count = df[df['Survey_Status'] == 1].shape[0]
    invalid_count = df[df['Survey_Status'] != 1].shape[0]
    total_count = df.shape[0]

    # Filter the DataFrame
    filtered_df = df[df['Survey_Status'] == 1]

    return filtered_df, valid_count, invalid_count, total_count

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

    # Use our live data explorer specific session state key prefix
    # The key is automatically created when the selectbox is rendered
    file_key = f'{live_data_prefix}selected_file'
    selected_file = st.session_state.get(file_key, '')

    # For substrate surveys
    if {'Observer_name_1', 'Group', 'Status', 'Total'}.issubset(columns) or 'DBMCP_Substrates' in selected_file:
        return "substrate"

    # For fish surveys
    elif {'Observer_name_1', 'Species', 'Size', 'Total'}.issubset(columns) or 'DBMCP_Fish' in selected_file:
        return "fish"

    # For predation surveys - these have Group column with predator species like "Drupella"
    elif 'DBMCP_Predation' in selected_file:
        return "predation"

    # For invertebrate surveys
    elif 'DBMCP_Inverts' in selected_file:
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

# Data source selection - using a key prefix specific to this page
# This helps isolate this page's state from other pages
live_data_prefix = "live_explorer_"
data_source = st.radio(
    "Select Data Source",
    ["Use Sample Files", "Upload File (currently disabled)"],
    index=0,
    key=f"{live_data_prefix}data_source"
)

if data_source == "Use Sample Files":
    if available_files:
        # Select a file - the value will be automatically stored in session state
        # using the provided key, so we don't need to set it again manually
        selected_file = st.selectbox(
            "Select a sample data file to analyze",
            available_files,
            key=f"{live_data_prefix}selected_file"
        )

        if selected_file:
            try:
                # Load data
                file_path = os.path.join(data_dir, selected_file)
                df = pd.read_csv(file_path)

                # Filter for valid surveys
                df, valid_count, invalid_count, total_count = filter_valid_surveys(df)

                # Show notice about filtering if needed
                if 'Survey_Status' in df.columns and invalid_count > 0:
                    st.info(f"Filtered data to include only valid surveys (Survey_Status = 1). Removed {invalid_count} of {total_count} rows ({(invalid_count/total_count*100):.1f}%).")

                # Hide raw data sample
                # Raw data sample has been removed as requested

                # Detect survey type
                survey_type = detect_survey_type(df)

                # Add diagnostic view for Andulay commercial fish
                if survey_type == "fish" and isinstance(selected_file, str) and "DBMCP_Fish" in selected_file:
                    # Create an expandable section for the diagnostic data
                    with st.expander("Diagnostic: Andulay Commercial Fish Data"):
                        st.subheader("Commercial Fish at Andulay")

                        # Filter for Andulay site
                        andulay_data = df[df['Site'].str.contains('Andulay', case=False)]

                        if not andulay_data.empty:
                            # Commercial fish species
                            commercial_species = [
                                'Snapper', 'Grouper', 'Sweetlips', 'Trevally', 'Barracuda', 
                                'Emperor', 'Parrotfish', 'Rabbitfish', 'Surgeonfish',
                                'Goatfish', 'Triggerfish', 'Tuna', 'Mackerel', 'Fusilier',
                                'Unicornfish', 'Soldierfish', 'Bream', 'Big Eye', 'Bigeye'
                            ]

                            # Find commercial fish
                            is_commercial = andulay_data['Species'].str.contains('|'.join(commercial_species), case=False, na=False)
                            commercial_fish = andulay_data[is_commercial]

                            if not commercial_fish.empty:
                                # Group by species and size
                                comm_summary = commercial_fish.groupby(['Species', 'Size'])['Total'].sum().reset_index()
                                comm_summary = comm_summary.sort_values(['Species', 'Size'])

                                st.write(f"Found {len(commercial_fish)} commercial fish records at Andulay")
                                st.dataframe(comm_summary, use_container_width=True)

                                # Calculate biomass for each species
                                st.subheader("Commercial Biomass Calculation Details")

                                # Load biomass parameters
                                try:
                                    biomass_params_file = "attached_assets/Fish Data Analysis - Biomass CO.csv"
                                    if os.path.exists(biomass_params_file):
                                        biomass_params_df = pd.read_csv(biomass_params_file)
                                        # Convert to dictionary for faster lookups
                                        biomass_params = {}
                                        for _, row in biomass_params_df.iterrows():
                                            if pd.notna(row['Species']) and pd.notna(row['Coeff a']) and pd.notna(row['Coeff b']):
                                                biomass_params[row['Species']] = (float(row['Coeff a']), float(row['Coeff b']))
                                    else:
                                        biomass_params = {}
                                except Exception as e:
                                    st.warning(f"Error loading biomass parameters: {str(e)}")
                                    biomass_params = {}

                                # Helper function for average size calculation
                                def get_avg_size(size_range):
                                    if pd.isna(size_range):
                                        return None

                                    # Convert to string if numeric
                                    if not isinstance(size_range, str):
                                        try:
                                            return float(size_range)
                                        except (ValueError, TypeError):
                                            return None

                                    # Handle range format (e.g., "5-10")
                                    if '-' in size_range:
                                        parts = size_range.split('-')
                                        try:
                                            min_size = float(parts[0])
                                            max_size = float(parts[1])
                                            return (min_size + max_size) / 2
                                        except (ValueError, IndexError):
                                            return None

                                    # Handle single value as string
                                    try:
                                        return float(size_range)
                                    except (ValueError, TypeError):
                                        return None

                                # Calculate biomass per species
                                biomass_details = []
                                total_biomass = 0

                                for _, fish in commercial_fish.iterrows():
                                    species = fish['Species']
                                    size = fish['Size']
                                    count = fish['Total']
                                    survey_id = fish['Survey_ID']

                                    # Calculate average size
                                    avg_size = get_avg_size(size)

                                    if avg_size is not None and avg_size > 0 and count > 0:
                                        # Get biomass parameters
                                        a, b = 0.01, 3.0  # Default values

                                        if species in biomass_params:
                                            a, b = biomass_params[species]
                                        else:
                                            # Try to find partial match
                                            found = False
                                            if ' - ' in species:
                                                family = species.split(' - ')[0]
                                                family_other = f"{family} - Other"

                                                if family_other in biomass_params:
                                                    a, b = biomass_params[family_other]
                                                    found = True
                                                elif family in biomass_params:
                                                    a, b = biomass_params[family]
                                                    found = True

                                        # Calculate weight
                                        weight_grams = a * (avg_size ** b)
                                        weight_kg = weight_grams / 1000

                                        # Total biomass for this entry
                                        fish_biomass = weight_kg * count
                                        total_biomass += fish_biomass

                                        biomass_details.append({
                                            'Survey_ID': survey_id,
                                            'Species': species,
                                            'Size Range': size,
                                            'Average Size (cm)': avg_size,
                                            'Count': count,
                                            'Parameter a': a,
                                            'Parameter b': b,
                                            'Individual Weight (kg)': weight_kg,
                                            'Total Biomass (kg)': fish_biomass
                                        })

                                # Display biomass calculation details
                                biomass_df = pd.DataFrame(biomass_details)
                                st.dataframe(biomass_df, use_container_width=True)

                                # Display total summary
                                st.subheader("Total Biomass Summary")
                                transect_area = 150  # 5m width x 30m length
                                biomass_per_100sqm = (total_biomass / transect_area) * 100

                                st.write(f"Total Commercial Biomass: {total_biomass:.2f} kg")
                                st.write(f"Transect Area: {transect_area} m²")
                                st.write(f"Commercial Biomass per 100m²: {biomass_per_100sqm:.2f} kg/100m²")
                            else:
                                st.warning("No commercial fish found at Andulay site.")
                        else:
                            st.warning("No data found for Andulay site.")

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