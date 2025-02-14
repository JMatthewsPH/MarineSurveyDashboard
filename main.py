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

# Sidebar for site selection and language
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

# Clean up
db.close()