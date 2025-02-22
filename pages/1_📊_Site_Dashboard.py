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
        description = selected_site_obj.description_en if selected_language == "English" else selected_site_obj.description_fil
        st.markdown(description or f"Description for {selected_site}")


    # Metrics Section
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

    # Define metrics for display
    metrics = {
        'biomass': {
            'title': 'Commercial Fish Biomass',
            'unit': 'kg/ha',
            'get_data': data_processor.get_biomass_data,
            'get_average': data_processor.get_average_biomass_data
        },
        'hard_coral': {
            'title': 'Hard Coral Cover',
            'unit': '%',
            'get_data': lambda site: data_processor.get_metric_data(site, 'hard_coral'),
            'get_average': lambda exclude_site, municipality: data_processor.get_average_metric_data('hard_coral', exclude_site, municipality)
        },
        'fleshy_algae': {
            'title': 'Fleshy Algae Cover',
            'unit': '%',
            'get_data': lambda site: data_processor.get_metric_data(site, 'fleshy_algae'),
            'get_average': lambda exclude_site, municipality: data_processor.get_average_metric_data('fleshy_algae', exclude_site, municipality)
        },
        'herbivore': {
            'title': 'Herbivore Density',
            'unit': 'ind/ha',
            'get_data': lambda site: data_processor.get_metric_data(site, 'herbivore'),
            'get_average': lambda exclude_site, municipality: data_processor.get_average_metric_data('herbivore', exclude_site, municipality)
        },
        'omnivore': {
            'title': 'Omnivore Density',
            'unit': 'ind/ha',
            'get_data': lambda site: data_processor.get_metric_data(site, 'omnivore'),
            'get_average': lambda exclude_site, municipality: data_processor.get_average_metric_data('omnivore', exclude_site, municipality)
        },
        'corallivore': {
            'title': 'Corallivore Density',
            'unit': 'ind/ha',
            'get_data': lambda site: data_processor.get_metric_data(site, 'corallivore'),
            'get_average': lambda exclude_site, municipality: data_processor.get_average_metric_data('corallivore', exclude_site, municipality)
        }
    }

    # Sidebar metric comparisons
    with st.sidebar:
        st.title("Metric Comparisons")

        comparison_options = {metric: {
            'comparison': st.selectbox(
                f"Compare {metrics[metric]['title']} with:",
                ["No Comparison", "Compare with Site", "Compare with Average"],
                key=f"{metric}_comparison"
            ),
            'compare_site': None,
            'compare_scope': None
        } for metric in metrics}

        # Handle comparison selections
        for metric, options in comparison_options.items():
            if options['comparison'] == "Compare with Site":
                compare_sites = [site for site in site_names if site != selected_site]
                options['compare_site'] = st.selectbox(
                    f"Select site to compare {metrics[metric]['title']}:",
                    compare_sites,
                    key=f"{metric}_compare_site"
                )
            elif options['comparison'] == "Compare with Average":
                options['compare_scope'] = st.selectbox(
                    f"Select average scope for {metrics[metric]['title']}:",
                    ["Municipality Average", "All Sites Average"],
                    key=f"{metric}_compare_scope"
                )

    # Display metrics
    for metric, config in metrics.items():
        st.subheader(config['title'])

        # Get main data
        metric_data = config['get_data'](selected_site)

        # Get comparison data if selected
        comparison_data = None
        if comparison_options[metric]['comparison'] == "Compare with Site" and comparison_options[metric]['compare_site']:
            comparison_data = config['get_data'](comparison_options[metric]['compare_site'])
        elif comparison_options[metric]['comparison'] == "Compare with Average":
            municipality = site_municipality if comparison_options[metric]['compare_scope'] == "Municipality Average" else None
            comparison_data = config['get_average'](
                exclude_site=selected_site,
                municipality=municipality
            )

        # Create and display figure
        fig = graph_generator.create_time_series(
            metric_data,
            f"{config['title']} - {selected_site}",
            f"{config['title']} ({config['unit']})",
            comparison_data=comparison_data
        )
        st.plotly_chart(fig, use_container_width=True, config=plotly_config)