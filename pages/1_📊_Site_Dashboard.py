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

# Initialize language in session state if not present
if 'language' not in st.session_state:
    st.session_state.language = "English"

# Sidebar for language selection
with st.sidebar:
    st.title("Settings")
    # Update session state when language changes
    st.session_state.language = st.selectbox(
        "Language / Wika",
        ["English", "Filipino"],
        key="language_selector",
        index=0 if st.session_state.language == "English" else 1
    )

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

# Sidebar for metric comparisons
with st.sidebar:
    st.title("Metric Comparisons")

    # Biomass comparison options
    st.subheader("Commercial Fish Biomass")
    biomass_comparison = st.radio(
        "Compare biomass with:",
        ["No Comparison", "Compare with Site", "Compare with Average"],
        key="biomass_comparison"
    )

    biomass_compare_site = None
    biomass_compare_scope = None
    if biomass_comparison == "Compare with Site":
        compare_sites = [site for site in site_names if site != selected_site]
        biomass_compare_site = st.selectbox(
            "Select site to compare biomass:",
            compare_sites,
            key="biomass_compare_site"
        )
    elif biomass_comparison == "Compare with Average":
        biomass_compare_scope = st.radio(
            "Select average scope:",
            ["Municipality Average", "All Sites Average"],
            key="biomass_compare_scope"
        )

    # Coral cover comparison options
    st.subheader("Hard Coral Cover")
    coral_comparison = st.radio(
        "Compare coral cover with:",
        ["No Comparison", "Compare with Site", "Compare with Average"],
        key="coral_comparison"
    )

    coral_compare_site = None
    coral_compare_scope = None
    if coral_comparison == "Compare with Site":
        compare_sites = [site for site in site_names if site != selected_site]
        coral_compare_site = st.selectbox(
            "Select site to compare coral cover:",
            compare_sites,
            key="coral_compare_site"
        )
    elif coral_comparison == "Compare with Average":
        coral_compare_scope = st.radio(
            "Select average scope:",
            ["Municipality Average", "All Sites Average"],
            key="coral_compare_scope"
        )

# Display site content
selected_site_obj = next((site for site in sites if site.name == selected_site), None)
if selected_site_obj:
    st.title(f"{selected_site} Dashboard")

    # Site Description Section
    st.header("Site Description")

    cols = st.columns([1, 2])

    with cols[0]:
        st.image("https://via.placeholder.com/400x300", use_container_width=True)

    with cols[1]:
        selected_language = st.session_state.language
        description = selected_site_obj.description_en if selected_language == "English" else selected_site_obj.description_tl
        st.markdown(description or f"Description for {selected_site}")


    # Metrics Section - More compact layout
    st.header("Site Metrics")
    # Configure Plotly chart settings
    plotly_config = {
        'responsive': True,
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['lasso2d', 'select2d']
    }

    # Get current site's municipality
    site_municipality = selected_site_obj.municipality if selected_site_obj else None

    # Get comparison data for biomass
    biomass_comparison_data = None
    if biomass_comparison == "Compare with Site" and biomass_compare_site:
        biomass_comparison_data = data_processor.get_biomass_data(biomass_compare_site)
    elif biomass_comparison == "Compare with Average":
        municipality = site_municipality if biomass_compare_scope == "Municipality Average" else None
        biomass_comparison_data = data_processor.get_average_biomass_data(
            exclude_site=selected_site,
            municipality=municipality
        )

    # Get comparison data for coral cover
    coral_comparison_data = None
    if coral_comparison == "Compare with Site" and coral_compare_site:
        coral_comparison_data = data_processor.get_coral_cover_data(coral_compare_site)
    elif coral_comparison == "Compare with Average":
        municipality = site_municipality if coral_compare_scope == "Municipality Average" else None
        coral_comparison_data = data_processor.get_average_coral_cover_data(
            exclude_site=selected_site,
            municipality=municipality
        )

    st.subheader("Commercial Fish Biomass")
    biomass_data = data_processor.get_biomass_data(selected_site)
    biomass_fig = graph_generator.create_time_series(
        biomass_data,
        f"Commercial Fish Biomass - {selected_site}",
        "Biomass (kg/ha)",
        comparison_data=biomass_comparison_data
    )
    st.plotly_chart(biomass_fig, use_container_width=True, config=plotly_config)

    st.subheader("Hard Coral Cover")
    coral_data = data_processor.get_coral_cover_data(selected_site)
    coral_fig = graph_generator.create_time_series(
        coral_data,
        f"Hard Coral Cover - {selected_site}",
        "Cover (%)",
        comparison_data=coral_comparison_data
    )
    st.plotly_chart(coral_fig, use_container_width=True, config=plotly_config)