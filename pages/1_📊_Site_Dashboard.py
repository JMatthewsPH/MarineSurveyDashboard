import streamlit as st

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="Site Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import os
from utils.data_processor import DataProcessor
from utils.graph_generator import GraphGenerator
from utils.translations import TRANSLATIONS
from utils.database import get_db

# Initialize processors
@st.cache_resource
def get_data_processor():
    db = next(get_db())
    return DataProcessor(db), GraphGenerator(DataProcessor(db))

data_processor, graph_generator = get_data_processor()

# Get site from URL parameter
def get_site_from_params():
    query_params = st.query_params
    return query_params.get("site", None)

# Get all sites
sites = data_processor.get_sites()

# Create ordered groups by municipality
zamboanguita_sites = sorted([site.name for site in sites if site.municipality == "Zamboanguita"])
siaton_sites = sorted([site.name for site in sites if site.municipality == "Siaton"])
santa_catalina_sites = sorted([site.name for site in sites if site.municipality == "Santa Catalina"])

# Combine in desired order
site_names = zamboanguita_sites + siaton_sites + santa_catalina_sites

# Get site from URL or dropdown
selected_site = get_site_from_params()
if not selected_site or selected_site not in site_names:
    selected_site = st.selectbox("Select Site", site_names)
    # Update URL when site is selected
    st.query_params["site"] = selected_site

# Load custom CSS
@st.cache_data
def load_css():
    with open('assets/site_styles.css') as f:
        return f'<style>{f.read()}</style>'

st.markdown(load_css(), unsafe_allow_html=True)

# Display site content
selected_site_obj = next((site for site in sites if site.name == selected_site), None)
if selected_site_obj:
    st.title(f"{selected_site} Dashboard")

    # Site Description Section
    st.header("Site Description")

    with st.container():
        cols = st.columns([1, 2])

        with cols[0]:
            st.markdown('<div class="image-container">', unsafe_allow_html=True)
            st.image("https://via.placeholder.com/400x300", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with cols[1]:
            st.markdown('<div class="site-description">', unsafe_allow_html=True)
            description = selected_site_obj.description_en
            st.markdown(description or f"Description for {selected_site}")
            st.markdown('</div>', unsafe_allow_html=True)

    # Metrics Section
    st.header("Site Metrics")

    # Configure Plotly chart settings
    plotly_config = {
        'responsive': True,
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['lasso2d', 'select2d']
    }

    with st.container():
        st.markdown('<div class="graph-container">', unsafe_allow_html=True)
        st.subheader("Commercial Fish Biomass")
        biomass_data = data_processor.get_biomass_data(selected_site)
        biomass_fig = graph_generator.create_time_series(
            biomass_data,
            f"Commercial Fish Biomass - {selected_site}",
            "Biomass (kg/ha)"
        )
        st.plotly_chart(biomass_fig, use_container_width=True, config=plotly_config)
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="graph-container">', unsafe_allow_html=True)
        st.subheader("Hard Coral Cover")
        coral_data = data_processor.get_coral_cover_data(selected_site)
        coral_fig = graph_generator.create_time_series(
            coral_data,
            f"Hard Coral Cover - {selected_site}",
            "Cover (%)"
        )
        st.plotly_chart(coral_fig, use_container_width=True, config=plotly_config)
        st.markdown('</div>', unsafe_allow_html=True)