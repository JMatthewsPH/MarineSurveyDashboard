import streamlit as st

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="Marine Conservation Philippines",
    layout="wide",  # Set to wide mode for better scaling
    initial_sidebar_state="expanded"
)

import pandas as pd
from utils.data_processor import DataProcessor
from utils.graph_generator import GraphGenerator
from utils.translations import TRANSLATIONS
from utils.database import get_db, init_sample_data
from utils.data_importer import run_import
import plotly.graph_objects as go

# Initialize database with sample data and import CSV data
@st.cache_resource
def initialize_database():
    init_sample_data()
    run_import()  # Import CSV data

initialize_database()

# Load custom CSS
@st.cache_data
def load_css():
    with open('assets/site_styles.css') as f:
        return f'<style>{f.read()}</style>'

st.markdown(load_css(), unsafe_allow_html=True)

# Session state initialization
if 'language' not in st.session_state:
    st.session_state.language = 'en'

def get_text(key):
    return TRANSLATIONS[st.session_state.language][key]

# Title and Subheading
st.title("Marine Conservation Philippines")
st.header("Data Dashboard")

# Get database session
@st.cache_resource
def get_data_processor():
    db = next(get_db())
    return DataProcessor(db), GraphGenerator(DataProcessor(db))

data_processor, graph_generator = get_data_processor()

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
st.sidebar.subheader(get_text('metric_comparison'))
metric_options = {
    'fleshy_algae': get_text('fleshy_algae'),
    'bleaching': get_text('bleaching'),
    'herbivore': get_text('herbivore'),
    'carnivore': get_text('carnivore'),
    'omnivore': get_text('omnivore'),
    'corallivore': get_text('corallivore')
}

# Primary metric selection
primary_metric = st.sidebar.selectbox(
    get_text('primary_metric'),
    options=list(metric_options.keys()),
    format_func=lambda x: metric_options[x],
    key="primary_metric"
)

# Secondary metric selection (optional)
secondary_metric = st.sidebar.selectbox(
    get_text('secondary_metric'),
    options=[None] + list(metric_options.keys()),
    format_func=lambda x: "None" if x is None else metric_options[x],
    key="secondary_metric"
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

# Commercial Fish Biomass Graph
with st.container():
    st.header(get_text('fish_biomass'))
    with st.spinner('Loading biomass data...'):
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

# Hard Coral Cover Graph
with st.container():
    st.header(get_text('coral_cover'))
    with st.spinner('Loading coral cover data...'):
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

# Additional metrics graph
with st.container():
    # Get primary metric data
    with st.spinner(f'Loading {metric_options[primary_metric]} data...'):
        primary_data = data_processor.get_metric_data(selected_site, primary_metric)

        # Get secondary metric data if selected
        secondary_data = None
        if secondary_metric is not None:
            secondary_data = data_processor.get_metric_data(selected_site, secondary_metric)

        # Create graph with both metrics if secondary is selected
        metric_fig = graph_generator.create_time_series(
            primary_data,
            f"{metric_options[primary_metric]} {'& ' + metric_options[secondary_metric] if secondary_metric else ''} - {selected_site}",
            metric_options[primary_metric],
            secondary_data=secondary_data,
            secondary_label=metric_options.get(secondary_metric) if secondary_metric else None
        )
        st.plotly_chart(metric_fig, use_container_width=True)

# Clean up
db = next(get_db()) # Added to properly close the database connection.  The @st.cache_resource decorator doesn't manage this.
db.close()