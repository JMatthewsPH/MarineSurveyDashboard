import streamlit as st
import pandas as pd
from utils.data_processor import DataProcessor
from utils.graph_generator import GraphGenerator
from utils.translations import TRANSLATIONS
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Marine Conservation Dashboard",
    layout="wide",
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

# Language toggle
if st.button(get_text('lang_toggle')):
    st.session_state.language = 'fil' if st.session_state.language == 'en' else 'en'

# Title and site selection
st.title(get_text('title'))

# Sidebar for site selection
st.sidebar.title("Site Selection")
selected_site = st.sidebar.selectbox(
    "Select Site",
    ["Site 1", "Site 2", "Site 3"]  # Replace with actual site IDs
)

# Initialize data processor and graph generator
# Note: Replace this with actual data loading from MongoDB
sample_data = []  # Replace with actual data
data_processor = DataProcessor(sample_data)
graph_generator = GraphGenerator(data_processor)

# Site Description Section
st.header(get_text('site_description'))
col1, col2 = st.columns([1, 2])
with col1:
    # Site image would be loaded here
    st.image("https://via.placeholder.com/400x300", use_column_width=True)
with col2:
    st.markdown(f"Site description in {st.session_state.language}")

# Commercial Fish Biomass Graph
st.header(get_text('fish_biomass'))
comparison_type = st.selectbox(
    "Comparison",
    ["none", "site", "average"],
    key="biomass_comparison"
)
biomass_data = data_processor.get_biomass_data(selected_site)
biomass_fig = graph_generator.create_time_series(
    biomass_data,
    get_text('fish_biomass'),
    "Biomass (kg/ha)"
)
st.plotly_chart(biomass_fig, use_container_width=True)

# Hard Coral Cover Graph
st.header(get_text('coral_cover'))
comparison_type = st.selectbox(
    "Comparison",
    ["none", "site", "average"],
    key="coral_comparison"
)
coral_data = data_processor.get_coral_cover_data(selected_site)
coral_fig = graph_generator.create_time_series(
    coral_data,
    get_text('coral_cover'),
    "Cover (%)"
)
st.plotly_chart(coral_fig, use_container_width=True)

# Fish Average Length Graph
st.header(get_text('fish_length'))
selected_species = st.selectbox(
    get_text('select_species'),
    ["Species 1", "Species 2", "Species 3"]  # Replace with actual species
)
comparison_type = st.selectbox(
    "Comparison",
    ["none", "site", "average"],
    key="length_comparison"
)
length_data = data_processor.get_fish_length_data(selected_site, selected_species)
length_fig = graph_generator.create_time_series(
    length_data,
    get_text('fish_length'),
    "Length (cm)"
)
st.plotly_chart(length_fig, use_container_width=True)

# Eco-Tourism Information
st.header(get_text('eco_tourism'))
observation_type = st.radio(
    get_text('observation_type'),
    ['percentage', 'numeric']
)
comparison_type = st.selectbox(
    "Comparison",
    ["none", "previous_year", "all_sites"],
    key="eco_comparison"
)
ecotourism_data = data_processor.get_ecotourism_data(selected_site, observation_type)
eco_fig = graph_generator.create_eco_tourism_chart(
    ecotourism_data,
    get_text('eco_tourism'),
    observation_type
)
st.plotly_chart(eco_fig, use_container_width=True)
