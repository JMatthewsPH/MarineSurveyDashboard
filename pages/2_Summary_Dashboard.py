import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium

# Import local modules
from utils.data_processor import DataProcessor
from utils.summary_graph_generator import SummaryGraphGenerator
from utils.map_generator import MapGenerator
from utils.translations import TRANSLATIONS
from utils.database import get_db_session
from utils.branding import display_logo, add_favicon, add_custom_loading_animation
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

# Add favicon and custom loading animation
add_favicon()
add_custom_loading_animation()

# Hide anchor elements with CSS
st.markdown("""
<style>
/* Hide Streamlit's automatic header anchors */
.stMarkdown h1 .anchor-link,
.stMarkdown h2 .anchor-link,
.stMarkdown h3 .anchor-link,
.stMarkdown h4 .anchor-link,
.stMarkdown h5 .anchor-link,
.stMarkdown h6 .anchor-link,
h1 > a,
h2 > a, 
h3 > a,
h4 > a,
h5 > a,
h6 > a {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)




# Initialize data processor with optimized caching
@st.cache_resource(ttl=3600)
def get_data_processor():
    """
    Get cached data processor and summary graph generator instances
    Uses a single database connection for both to reduce overhead
    """
    with get_db_session() as db:
        data_processor = DataProcessor(db)
        # Pass the same data processor to summary graph generator to avoid duplicate db connections
        graph_generator = SummaryGraphGenerator(data_processor)
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
    
    # Language display mapping
    LANGUAGE_DISPLAY = {
        "en": "English",
        "tl": "Tagalog",
        "ceb": "Cebuano"
    }
    
    # Language selection dropdown
    current_language_display = LANGUAGE_DISPLAY.get(st.session_state.language, "English")
    selected_language_display = st.selectbox(
        TRANSLATIONS[st.session_state.language]['lang_toggle'],
        list(LANGUAGE_DISPLAY.values()),
        index=list(LANGUAGE_DISPLAY.values()).index(current_language_display),
        key="language_selector"
    )
    
    # Check if language changed and update session state
    for code, name in LANGUAGE_DISPLAY.items():
        if name == selected_language_display and code != st.session_state.language:
            st.session_state.language = code
            # Streamlit will automatically rerun when session state changes
    
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
            
        biomass_val = f"{summary_metrics['avg_biomass']:.1f} kg/100m²" if summary_metrics["avg_biomass"] > 0 else "No data"
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
    # Create placeholder for comparison chart
    matrix_placeholder = st.empty()
    with matrix_placeholder:
        st.text("Loading site comparison matrix...")
    
    # Get comparison matrix data
    matrix_data = data_processor.get_site_comparison_matrix()
    
    if matrix_data is not None and not matrix_data.empty:
        # Apply municipality filter if specified
        if municipality_filter:
            matrix_data = matrix_data[matrix_data['municipality'] == municipality_filter]
        
        matrix_placeholder.empty()
        
        # Show data availability info for commercial biomass
        if selected_metric == "commercial_biomass":
            sites_with_data = matrix_data[matrix_data[selected_metric].notna()]['site'].tolist()
            sites_no_data = matrix_data[matrix_data[selected_metric].isna()]['site'].tolist()
            
            if sites_no_data:
                st.info(f"📊 **Data Status**: {len(sites_with_data)} sites have biomass data, {len(sites_no_data)} sites have no biomass data in database. Sites without data appear as zero on the chart and show 'No data in database' when hovered.")
        
        # Always create bar chart as default
        if selected_metric == "commercial_biomass":
            # Create grouped bar chart with color coding for commercial biomass
            fig, config = graph_generator.create_municipality_grouped_bar_chart(
                matrix_data=matrix_data,
                metric_column=selected_metric,
                title=f"Site Comparison: {comparison_metric}",
                y_axis_label="Commercial Biomass (kg/100m²)"
            )
        else:
            # Create regular bar chart for other metrics
            fig, config = graph_generator.create_municipality_grouped_bar_chart(
                matrix_data=matrix_data,
                metric_column=selected_metric,
                title=f"Site Comparison: {comparison_metric}",
                y_axis_label=comparison_metric
            )
        
        # Display the selected chart
        matrix_placeholder.plotly_chart(fig, use_container_width=True, config=config)
    else:
        matrix_placeholder.warning("No comparison data available for the selected filters.")

# Section 4: Trend Analysis
st.header("Trend Analysis")
trend_container = st.container()

with trend_container:
    # Options for trend analysis
    col1, col2 = st.columns([1, 2])
    
    with col1:
        grouping_option = st.radio(
            "Group by:",
            ["All Sites", "Municipality", "Individual Sites"],
            index=0  # Default to "All Sites"
        )
        
        group_by_municipality = grouping_option == "Municipality"
        group_by_all_sites = grouping_option == "All Sites"
        
        # Only show site highlighting option when not on "All Sites" mode
        if grouping_option != "All Sites":
            highlight_option = st.checkbox("Highlight specific sites", value=False)
        else:
            highlight_option = False
        
        highlight_sites = []
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
            
            # Create trend chart based on grouping option
            if group_by_all_sites:
                # Use summary graph generator for all sites average
                fig, config = graph_generator.create_multi_site_trend_chart(
                    trend_data=trend_data,
                    metric_name="Commercial Biomass",
                    group_by_municipality=False,
                    highlight_sites=highlight_sites,
                    group_by_all_sites=True
                )
            else:
                # Use summary graph generator for municipality/individual sites
                fig, config = graph_generator.create_multi_site_trend_chart(
                    trend_data=trend_data,
                    metric_name="Commercial Biomass",
                    group_by_municipality=group_by_municipality,
                    highlight_sites=highlight_sites,
                    group_by_all_sites=False
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
            
            # Create trend chart based on grouping option
            if group_by_all_sites:
                # Use summary graph generator for all sites average
                fig, config = graph_generator.create_multi_site_trend_chart(
                    trend_data=trend_data,
                    metric_name="Omnivore Density",
                    group_by_municipality=False,
                    highlight_sites=highlight_sites,
                    group_by_all_sites=True
                )
            else:
                # Use summary graph generator for municipality/individual sites
                fig, config = graph_generator.create_multi_site_trend_chart(
                    trend_data=trend_data,
                    metric_name="Omnivore Density",
                    group_by_municipality=group_by_municipality,
                    highlight_sites=highlight_sites,
                    group_by_all_sites=False
                )
            
            # Display trend chart
            trend_placeholder.empty()
            trend_placeholder.plotly_chart(fig, use_container_width=True, config=config)
        else:
            trend_placeholder.warning("No trend data available for the selected filters.")
            

            
    else:
        # For other metrics, display a placeholder message
        trend_placeholder.info(f"Trend analysis for {comparison_metric} will be implemented soon.")

# Add disclaimer text below trend analysis
st.markdown("""
<div style="font-size: 12px; color: #666; margin-top: 15px; margin-bottom: 20px; padding: 10px; background-color: #f8f9fa; border-left: 4px solid #007acc; border-radius: 4px;">
<strong>Data Interpretation Note:</strong> Kindly note that the graphs are averages of all surveyed sites (either in totality or in the specific municipality you have selected.) In either case, this gives you a broad perspective of how historic trends is likely to have changed. <strong>Important note:</strong> The number of survey sites across municipalities have changed over the years. Some survey sites are no longer being monitored, while new MPAs have been created that MCP is now monitoring as well. The graph merely represent the historic averages, not how any particular MPA is doing. This means for example that the introduction of a new survey site may skew data. E.g. inclusion of a rich MPA will increase biomass averages even if no actual changes are observed in any sites.
</div>
""", unsafe_allow_html=True)

# =================================
# 📍 INTERACTIVE BIOMASS HEATMAP
# =================================

st.markdown("---")
st.markdown("## 📍 Interactive Biomass Heatmap")
st.markdown("Explore the geographic distribution of marine biomass across all MPA sites with this interactive map.")

# Create map generator
with st.spinner("Loading interactive biomass heatmap..."):
    try:
        map_generator = MapGenerator(data_processor)
        biomass_map = map_generator.create_biomass_heatmap(
            center_lat=9.15,  # Center between all sites
            center_lon=123.0,
            zoom_start=9
        )
        
        # Display the map
        st.markdown("### 🗺️ Geographic Biomass Distribution")
        st.markdown("""
        **How to use this map:**
        - 🟢 **Green markers**: High biomass sites (≥100 kg/100m²)
        - 🟠 **Orange markers**: Medium biomass sites (50-100 kg/100m²)  
        - 🔴 **Red markers**: Low biomass sites (<50 kg/100m²)
        - 🔥 **Heatmap overlay**: Shows biomass radiation intensity
        - 🗺️ **Layer control**: Switch between map view and satellite imagery
        - 📍 **Click markers**: View detailed site information
        """)
        
        # Display the folium map with responsive width
        map_data = st_folium(
            biomass_map, 
            use_container_width=True,
            height=600,
            returned_objects=["last_object_clicked_popup"]
        )
        
        # Display clicked site information if available
        if map_data["last_object_clicked_popup"]:
            st.success("🗺️ **Map Interaction**: Click on any marker to see detailed biomass information for that site!")
            
    except Exception as e:
        st.error(f"Error loading biomass heatmap: {str(e)}")
        st.info("📍 Interactive biomass heatmap will be available once all site coordinates are properly configured.")

# Add a footer with timestamp
st.markdown("---")
current_date = datetime.now().strftime("%B %d, %Y")
st.markdown(f"<div class='footer'>Dashboard last updated: {current_date}</div>", unsafe_allow_html=True)