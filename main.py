import streamlit as st
import pandas as pd
from utils.data_processor import DataProcessor
from utils.graph_generator import GraphGenerator
from utils.translations import TRANSLATIONS
from utils.database import get_db, init_sample_data
from utils.data_importer import run_import
import plotly.graph_objects as go

# Initialize database with sample data and import CSV data
init_sample_data()
run_import()  # Import CSV data

# Page configuration
st.set_page_config(
    page_title="Marine Conservation Philippines",
    layout="wide",  # Set to wide mode for better scaling
    initial_sidebar_state="expanded"
)

# Load custom CSS
with open('assets/site_styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Session state initialization
if 'language' not in st.session_state:
    st.session_state.language = 'en'

def get_text(key):
    return TRANSLATIONS[st.session_state.language][key]

# Title and Subheading
st.title("Marine Conservation Philippines")
st.header("Data Dashboard")

# Get database session
db = next(get_db())
data_processor = DataProcessor(db)
graph_generator = GraphGenerator(data_processor)

# Get all sites for selection
sites = data_processor.get_sites()
site_names = [site.name for site in sites]

# Sidebar
st.sidebar.title("Settings")

# Language selection in sidebar
selected_language = st.sidebar.selectbox(
    "Language / Wika",
    options=['en', 'fil'],
    format_func=lambda x: 'English' if x == 'en' else 'Filipino',
    index=0 if st.session_state.language == 'en' else 1
)

# Update session state language
if selected_language != st.session_state.language:
    st.session_state.language = selected_language

# Site selection
st.sidebar.title("Site Selection")
selected_site = st.sidebar.selectbox(
    "Select Site",
    site_names
)

# Comparison Settings
st.sidebar.title("Comparison Settings")

# Biomass comparison
st.sidebar.subheader(get_text('fish_biomass'))
comparison_options = [get_text('compare_none')] + \
                    [site for site in site_names if site != selected_site] + \
                    [get_text('compare_avg')]
biomass_comparison = st.sidebar.selectbox(
    "Comparison",
    comparison_options,
    key="biomass_comparison"
)

# Coral cover comparison
st.sidebar.subheader(get_text('coral_cover'))
coral_comparison = st.sidebar.selectbox(
    "Comparison",
    comparison_options,
    key="coral_comparison"
)

# Additional metrics selection
st.sidebar.subheader(get_text('additional_metrics'))
metric_options = {
    'fleshy_algae': get_text('fleshy_algae'),
    'bleaching': get_text('bleaching'),
    'herbivore': get_text('herbivore'),
    'carnivore': get_text('carnivore'),
    'omnivore': get_text('omnivore'),
    'corallivore': get_text('corallivore')
}
selected_metric = st.sidebar.selectbox(
    "Select Metric",
    options=list(metric_options.keys()),
    format_func=lambda x: metric_options[x],
    key="metric_selection"
)

# Additional metric comparison
metric_comparison = st.sidebar.selectbox(
    "Comparison",
    comparison_options,
    key="metric_comparison"
)

# Main content area using columns for better layout
# Site Description Section
st.header(get_text('site_description'))
col1, col2 = st.columns([1, 2])
with col1:
    # Site image would be loaded here
    st.image("https://via.placeholder.com/400x300", use_container_width=True)
with col2:
    selected_site_obj = next((site for site in sites if site.name == selected_site), None)
    if selected_site_obj:
        description = selected_site_obj.description_fil if st.session_state.language == 'fil' else selected_site_obj.description_en
        st.markdown(description or f"Description for {selected_site} in {st.session_state.language}")

# Use container for better spacing
with st.container():
    # Commercial Fish Biomass Graph
    st.header(get_text('fish_biomass'))
    biomass_data = data_processor.get_biomass_data(selected_site)
    comparison_data = None
    if biomass_comparison != get_text('compare_none'):
        if biomass_comparison == get_text('compare_avg'):
            comparison_data = data_processor.get_average_biomass_data(exclude_site=selected_site)
        else:
            comparison_data = data_processor.get_biomass_data(biomass_comparison)
    biomass_fig = graph_generator.create_time_series(
        biomass_data,
        f"{get_text('fish_biomass')} - {selected_site}",
        "Biomass (kg/ha)",
        comparison_data
    )
    st.plotly_chart(biomass_fig, use_container_width=True)

# Use another container for coral cover
with st.container():
    # Hard Coral Cover Graph
    st.header(get_text('coral_cover'))
    coral_data = data_processor.get_coral_cover_data(selected_site)
    comparison_data = None
    if coral_comparison != get_text('compare_none'):
        if coral_comparison == get_text('compare_avg'):
            comparison_data = data_processor.get_average_coral_cover_data(exclude_site=selected_site)
        else:
            comparison_data = data_processor.get_coral_cover_data(coral_comparison)
    coral_fig = graph_generator.create_time_series(
        coral_data,
        f"{get_text('coral_cover')} - {selected_site}",
        "Cover (%)",
        comparison_data
    )
    st.plotly_chart(coral_fig, use_container_width=True)

# Additional metric graph
with st.container():
    st.header(metric_options[selected_metric])
    metric_data = data_processor.get_metric_data(selected_site, selected_metric)
    comparison_data = None
    if metric_comparison != get_text('compare_none'):
        if metric_comparison == get_text('compare_avg'):
            comparison_data = data_processor.get_average_metric_data(selected_metric, exclude_site=selected_site)
        else:
            comparison_data = data_processor.get_metric_data(metric_comparison, selected_metric)
    metric_fig = graph_generator.create_time_series(
        metric_data,
        f"{metric_options[selected_metric]} - {selected_site}",
        "Value",
        comparison_data
    )
    st.plotly_chart(metric_fig, use_container_width=True)

# Clean up
db.close()