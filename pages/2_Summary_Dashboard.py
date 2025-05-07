import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Import local modules
from utils.data_processor import DataProcessor
from utils.graph_generator import GraphGenerator
from utils.translations import TRANSLATIONS
from utils.database import get_db_session
from utils.branding import display_logo, add_favicon
from utils.ui_helpers import loading_spinner, create_loading_placeholder, load_css, skeleton_text_placeholder
from utils.navigation import display_navigation

# Set page config
st.set_page_config(
    page_title="MCP Summary Dashboard",
    page_icon="assets/branding/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get or create session state for language
if 'language' not in st.session_state:
    st.session_state.language = 'en'  # Default to English

# Add favicon
add_favicon()




# Initialize data processor with optimized caching
@st.cache_resource(ttl=3600)
def get_data_processor():
    """
    Get cached data processor and graph generator instances
    Uses a single database connection for both to reduce overhead
    """
    with get_db_session() as db:
        data_processor = DataProcessor(db)
        # Pass the same data processor to graph generator to avoid duplicate db connections
        graph_generator = GraphGenerator(data_processor)
        return data_processor, graph_generator

# Get processors with performance logging
start_time = time.time()
data_processor, graph_generator = get_data_processor()
init_time = time.time() - start_time
if init_time > 0.5:  # Log if initialization is slow
    print(f"Data processor initialization took {init_time:.2f} seconds")

# Apply critical CSS directly in the page first
st.markdown("""
<style>
/* Critical styles for immediate display */
body {
    font-family: sans-serif;
    opacity: 1;
    transition: opacity 0.2s;
}
.site-card { 
    border: 1px solid #eee;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 15px;
    transition: transform 0.2s;
}
</style>
""", unsafe_allow_html=True)

# Then apply the main CSS
st.markdown(load_css(), unsafe_allow_html=True)

# Display logo at the top
display_logo(size="medium")

# Dashboard title
st.title(f"{TRANSLATIONS[st.session_state.language]['summary_dashboard']}")
st.markdown(f"<div class='subtitle'>{TRANSLATIONS[st.session_state.language]['all_sites_analysis']}</div>", unsafe_allow_html=True)

# Date selector in the sidebar
with st.sidebar:
    st.title(TRANSLATIONS[st.session_state.language]['settings'])
    
    # Language selection
    LANGUAGE_DISPLAY = {
        "en": "English",
        "tl": "Tagalog",
        "ceb": "Cebuano"
    }
    
    selected_language = st.selectbox(
        TRANSLATIONS[st.session_state.language]['lang_toggle'],
        list(LANGUAGE_DISPLAY.values()),
        key="language_selector",
        index=list(LANGUAGE_DISPLAY.values()).index(LANGUAGE_DISPLAY.get(st.session_state.language, "English"))
    )
    
    # Convert display language back to language code
    for code, name in LANGUAGE_DISPLAY.items():
        if name == selected_language:
            st.session_state.language = code
            break
    
    # Streamlit navigation is now automatically handled in the sidebar
    
    st.title(TRANSLATIONS[st.session_state.language]['analysis_options'])
    
    # Get the min and max dates from all surveys 
    all_surveys = []
    sites = data_processor.get_sites()
    for site in sites:
        site_surveys = data_processor.get_biomass_data(site.name)
        if not site_surveys.empty:
            all_surveys.append(site_surveys)
    
    # Combine all survey data to get date range
    if all_surveys:
        all_data = pd.concat(all_surveys)
        min_date = pd.to_datetime(all_data['date'].min())
        max_date = pd.to_datetime(all_data['date'].max())
    else:
        # Fallback dates if no data
        min_date = pd.to_datetime('2017-01-01')
        max_date = pd.to_datetime('2023-12-31')
    
    # Date range selection
    st.header(TRANSLATIONS[st.session_state.language]['date_range'])
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(TRANSLATIONS[st.session_state.language]['start_date'], 
                                  value=min_date,
                                  min_value=min_date,
                                  max_value=max_date)
    with col2:
        end_date = st.date_input(TRANSLATIONS[st.session_state.language]['end_date'], 
                                value=max_date,
                                min_value=min_date,
                                max_value=max_date)
    
    # Set date range only if valid selection
    # Convert date_input objects (datetime.date) to pandas Timestamp objects for consistent comparison
    start_timestamp = pd.to_datetime(start_date)
    end_timestamp = pd.to_datetime(end_date)
    
    date_range = (start_timestamp, end_timestamp) if start_date <= end_date else None
    if start_date > end_date:
        st.error(TRANSLATIONS[st.session_state.language]['date_range_error'])
    
    # Municipality filter option
    st.header("Filter by Municipality")
    
    # Get all municipalities
    municipalities = sorted(list(set([site.municipality for site in sites])))
    selected_municipality = st.selectbox(
        "Select Municipality",
        ["All Municipalities"] + municipalities,
        index=0  # Default to "All Municipalities"
    )
    
    municipality_filter = None if selected_municipality == "All Municipalities" else selected_municipality
    
    # Comparison metric selection
    st.header("Comparison Metric")
    comparison_metric = st.selectbox(
        "Select Primary Metric for Comparison",
        ["Commercial Biomass", "Hard Coral Cover", "Fleshy Algae Cover", 
         "Herbivore Density", "Omnivore Density", "Corallivore Density"],
        index=0  # Default to Commercial Biomass
    )
    
    # Metric mapping
    metric_mapping = {
        "Commercial Biomass": "commercial_biomass",
        "Hard Coral Cover": "hard_coral_cover",
        "Fleshy Algae Cover": "fleshy_algae_cover",
        "Herbivore Density": "herbivore_density", 
        "Omnivore Density": "omnivore_density",
        "Corallivore Density": "corallivore_density"
    }
    
    selected_metric = metric_mapping[comparison_metric]

# Main dashboard content with multi-column layout
# Section 1: Overall Statistics
st.header("Overall Statistics")
overall_stats_container = st.container()

# Create placeholder for loading state
with overall_stats_container:
    stats_placeholder = st.empty()
    with stats_placeholder:
        stats_loading = skeleton_text_placeholder(lines=2)

# Get summary metrics
summary_metrics = data_processor.get_all_sites_summary_metrics()

# Replace placeholder with actual content
stats_placeholder.empty()

with overall_stats_container:
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="Total Sites", 
            value=summary_metrics["site_count"]
        )
    
    with col2:
        start = summary_metrics["start_date"]
        end = summary_metrics["end_date"]
        date_text = f"{start.strftime('%b %Y')} - {end.strftime('%b %Y')}" if start and end else "No data"
        st.metric(
            label="Data Range", 
            value=date_text
        )

# Section 2: Key Ecological Health Indicators
st.header("Key Ecological Health Indicators")
indicators_container = st.container()

with indicators_container:
    # Create placeholders for metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        coral_placeholder = st.empty()
        with coral_placeholder:
            skeleton_text_placeholder(lines=2)
        
        coral_val = f"{summary_metrics['avg_hard_coral']:.1f}%" if summary_metrics["avg_hard_coral"] > 0 else "No data"
        coral_placeholder.metric(
            label="Average Hard Coral Cover",
            value=coral_val,
            delta=None
        )
    
    with col2:
        biomass_placeholder = st.empty()
        with biomass_placeholder:
            skeleton_text_placeholder(lines=2)
            
        biomass_val = f"{summary_metrics['avg_biomass']:.1f} kg/ha" if summary_metrics["avg_biomass"] > 0 else "No data"
        biomass_placeholder.metric(
            label="Average Commercial Fish Biomass",
            value=biomass_val,
            delta=None
        )
    
    with col3:
        algae_placeholder = st.empty()
        with algae_placeholder:
            skeleton_text_placeholder(lines=2)
            
        algae_val = f"{summary_metrics['avg_fleshy_algae']:.1f}%" if summary_metrics["avg_fleshy_algae"] > 0 else "No data"
        algae_placeholder.metric(
            label="Average Fleshy Algae Cover",
            value=algae_val,
            delta=None
        )

# Section 3: Site Comparison Matrix
st.header("Site Comparison Matrix")
matrix_container = st.container()

with matrix_container:
    # Create placeholder for heatmap
    matrix_placeholder = st.empty()
    with matrix_placeholder:
        st.text("Loading site comparison matrix...")
    
    # Get comparison matrix data
    matrix_data = data_processor.get_site_comparison_matrix()
    
    if matrix_data is not None and not matrix_data.empty:
        # Apply municipality filter if specified
        if municipality_filter:
            matrix_data = matrix_data[matrix_data['municipality'] == municipality_filter]
        
        # Create heatmap
        fig, config = graph_generator.create_site_comparison_heatmap(
            matrix_data=matrix_data,
            metric_column=selected_metric,
            title=f"Site Comparison: {comparison_metric}"
        )
        
        # Display heatmap
        matrix_placeholder.empty()
        matrix_placeholder.plotly_chart(fig, use_container_width=True, config=config)
    else:
        matrix_placeholder.warning("No comparison data available for the selected filters.")

# Section 4: Geographic Visualization (simplified version)
st.header("Geographic Distribution")
geo_container = st.container()

with geo_container:
    # Create placeholder for map visualization
    geo_placeholder = st.empty()
    with geo_placeholder:
        st.text("Loading geographic visualization...")
    
    # Use the same matrix data for geographic visualization
    if matrix_data is not None and not matrix_data.empty:
        try:
            # Make a clean copy of the data for visualization
            geo_viz_data = matrix_data.copy()
            
            # Replace NaN values with 0 for the visualization
            if selected_metric in geo_viz_data.columns:
                geo_viz_data[selected_metric] = geo_viz_data[selected_metric].fillna(0)
                
                # Add a fixed size column to avoid NaN errors
                geo_viz_data['point_size'] = 15  # Fixed size for all points
                
                # Create a simple bar chart instead of scatter for now
                fig = px.bar(
                    geo_viz_data, 
                    x='municipality', 
                    y=selected_metric, 
                    color='site',
                    title=f"Distribution by Municipality: {comparison_metric}",
                    labels={
                        'municipality': 'Municipality',
                        selected_metric: comparison_metric,
                        'site': 'Site'
                    },
                    height=500
                )
                
                fig.update_layout(
                    template="plotly_white",
                    margin=dict(l=40, r=40, t=60, b=60),
                    legend=dict(title="Sites")
                )
                
                # Standard config for download options
                config = {
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': f"geographic_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'height': 800,
                        'width': 1200,
                        'scale': 2
                    },
                    'displaylogo': False,
                    'responsive': True,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                    'scrollZoom': False
                }
                
                # Display visualization
                geo_placeholder.empty()
                geo_placeholder.plotly_chart(fig, use_container_width=True, config=config)
            else:
                geo_placeholder.warning(f"Metric '{selected_metric}' not found in data.")
        except Exception as e:
            # Show error information
            geo_placeholder.error(f"Error creating geographic visualization: {str(e)}")
            st.info("Using a simplified bar chart visualization until geographic data is available.")
            
            # Create a simple fallback visualization
            try:
                # Group by municipality for a summary view
                muni_summary = matrix_data.groupby('municipality')[selected_metric].mean().reset_index()
                
                # Create a simple bar chart
                fig = px.bar(
                    muni_summary,
                    x='municipality',
                    y=selected_metric,
                    title=f"Average {comparison_metric} by Municipality",
                    labels={
                        'municipality': 'Municipality',
                        selected_metric: f"Average {comparison_metric}"
                    }
                )
                
                geo_placeholder.plotly_chart(fig, use_container_width=True)
            except:
                geo_placeholder.warning("Could not create visualization with the available data.")
    else:
        geo_placeholder.warning("No geographic data available for the selected filters.")

# Section 5: Trend Analysis
st.header("Trend Analysis")
trend_container = st.container()

with trend_container:
    # Options for trend analysis
    col1, col2 = st.columns([1, 2])
    
    with col1:
        grouping_option = st.radio(
            "Group by:",
            ["Individual Sites", "Municipality"]
        )
        
        group_by_municipality = grouping_option == "Municipality"
        
        highlight_option = st.checkbox("Highlight specific sites", value=False)
        
        highlight_sites = None
        if highlight_option:
            # Get site names
            site_names = [site.name for site in sites]
            if municipality_filter:
                # Filter sites by municipality
                filtered_sites = [site.name for site in sites if site.municipality == municipality_filter]
                highlight_sites = st.multiselect(
                    "Select sites to highlight:",
                    filtered_sites,
                    max_selections=5
                )
            else:
                highlight_sites = st.multiselect(
                    "Select sites to highlight:",
                    site_names,
                    max_selections=5
                )
    
    # Create placeholder for trend chart
    trend_placeholder = st.empty()
    with trend_placeholder:
        st.text("Loading trend analysis chart...")
    
    # Map comparison_metric to actual metric name in data
    metric_to_column = {
        "Commercial Biomass": "commercial_biomass",
        "Hard Coral Cover": "hard_coral_cover", 
        "Fleshy Algae Cover": "fleshy_algae",
        "Omnivore Density": "omnivore_density"
    }
    
    # Map the selection to the proper trend metric name
    if comparison_metric == "Commercial Biomass":
        trend_metric = "Commercial Biomass"  # This matches the column name in get_biomass_data
    elif comparison_metric == "Hard Coral Cover":
        trend_metric = "Hard Coral Cover"  # This matches the column name in get_coral_cover_data
    elif comparison_metric == "Omnivore Density":
        trend_metric = "Omnivore Density"  # This will match column name in get_metric_data
    else:
        # For other metrics, default to the comparison_metric
        trend_metric = comparison_metric
    
    # Get trend analysis data based on selected metric
    if comparison_metric == "Commercial Biomass":
        # For Commercial Biomass, we can use existing methods
        trend_data_list = []
        for site in sites:
            if municipality_filter and site.municipality != municipality_filter:
                continue
                
            site_data = data_processor.get_biomass_data(site.name)
            if not site_data.empty:
                site_data['site'] = site.name
                site_data['municipality'] = site.municipality
                trend_data_list.append(site_data)
        
        if trend_data_list:
            trend_data = pd.concat(trend_data_list)
            
            # Filter by date range if specified
            if date_range:
                # date_range already contains pandas timestamps
                start_timestamp, end_timestamp = date_range
                
                # Ensure trend_data['date'] is in datetime64 format
                trend_data['date'] = pd.to_datetime(trend_data['date'])
                
                # Now filter using compatible types
                trend_data = trend_data[
                    (trend_data['date'] >= start_timestamp) & 
                    (trend_data['date'] <= end_timestamp)
                ]
            
            # Create trend chart
            fig, config = graph_generator.create_multi_site_trend_chart(
                trend_data=trend_data,
                metric_name="Commercial Biomass",
                group_by_municipality=group_by_municipality,
                highlight_sites=highlight_sites
            )
            
            # Display trend chart
            trend_placeholder.empty()
            trend_placeholder.plotly_chart(fig, use_container_width=True, config=config)
        else:
            trend_placeholder.warning("No trend data available for the selected filters.")
            
    elif comparison_metric == "Omnivore Density":
        # For Omnivore Density, we use the get_metric_data method
        trend_data_list = []
        for site in sites:
            if municipality_filter and site.municipality != municipality_filter:
                continue
                
            # Use 'omnivore' as the metric type in get_metric_data
            # This corresponds to the key in DataProcessor.METRIC_MAP
            site_data = data_processor.get_metric_data(site.name, "omnivore")
            if not site_data.empty:
                site_data['site'] = site.name
                site_data['municipality'] = site.municipality
                trend_data_list.append(site_data)
        
        if trend_data_list:
            trend_data = pd.concat(trend_data_list)
            
            # Filter by date range if specified
            if date_range:
                # date_range already contains pandas timestamps
                start_timestamp, end_timestamp = date_range
                
                # Ensure trend_data['date'] is in datetime64 format
                trend_data['date'] = pd.to_datetime(trend_data['date'])
                
                # Now filter using compatible types
                trend_data = trend_data[
                    (trend_data['date'] >= start_timestamp) & 
                    (trend_data['date'] <= end_timestamp)
                ]
            
            # Create trend chart
            fig, config = graph_generator.create_multi_site_trend_chart(
                trend_data=trend_data,
                metric_name="omnivore",  # Use the actual column name from the dataframe
                group_by_municipality=group_by_municipality,
                highlight_sites=highlight_sites
            )
            
            # Display trend chart
            trend_placeholder.empty()
            trend_placeholder.plotly_chart(fig, use_container_width=True, config=config)
        else:
            trend_placeholder.warning("No trend data available for the selected filters.")
            
    else:
        # For other metrics, display a placeholder message
        trend_placeholder.info(f"Trend analysis for {comparison_metric} will be implemented soon.")

# Add a footer with timestamp
st.markdown("---")
current_date = datetime.now().strftime("%B %d, %Y")
st.markdown(f"<div class='footer'>Dashboard last updated: {current_date}</div>", unsafe_allow_html=True)