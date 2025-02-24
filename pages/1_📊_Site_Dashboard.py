import streamlit as st

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="Site Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
from utils.data_processor import DataProcessor
from utils.graph_generator import GraphGenerator
from utils.translations import TRANSLATIONS
from utils.database import get_db

# Initialize language in session state if not present
if 'language' not in st.session_state:
    st.session_state.language = "English"

# Initialize processors
@st.cache_resource
def get_data_processor():
    db = next(get_db())
    return DataProcessor(db), GraphGenerator(DataProcessor(db))

data_processor, graph_generator = get_data_processor()

# Get all sites
sites = data_processor.get_sites()

# Create ordered groups by municipality
zamboanguita_sites = sorted([site.name for site in sites if site.municipality == "Zamboanguita"])
siaton_sites = sorted([site.name for site in sites if site.municipality == "Siaton"])
santa_catalina_sites = sorted([site.name for site in sites if site.municipality == "Santa Catalina"])

# Combine in desired order
site_names = zamboanguita_sites + siaton_sites + santa_catalina_sites

# Load custom CSS
@st.cache_data
def load_css():
    with open('assets/site_styles.css') as f:
        return f'<style>{f.read()}</style>'

st.markdown(load_css(), unsafe_allow_html=True)

# Sidebar for site selection and language
with st.sidebar:
    # Back to main link first
    if st.session_state.language == "English":
        st.markdown("[🏠 Back to Main](../)")
    else:
        st.markdown("[🏠 Balik sa Main](../)")

    st.markdown("---")  # Add separator

    # Language selection
    st.session_state.language = st.selectbox(
        "Language / Wika",
        ["English", "Filipino"],
        key="language_selector",
        index=0 if st.session_state.language == "English" else 1
    )

    st.markdown("---")  # Add separator

    # Site selection with municipality grouping
    st.subheader("Select Site")
    site_options = []
    if zamboanguita_sites:
        site_options.append("Zamboanguita")
        site_options.extend([f"  {site}" for site in zamboanguita_sites])
    if siaton_sites:
        site_options.append("Siaton")
        site_options.extend([f"  {site}" for site in siaton_sites])
    if santa_catalina_sites:
        site_options.append("Santa Catalina")
        site_options.extend([f"  {site}" for site in santa_catalina_sites])

    selected_option = st.selectbox(
        "Choose a site to view",
        site_options,
        index=site_options.index(f"  {st.query_params.get('site')}") if st.query_params.get('site') in [s.strip() for s in site_options] else 0
    )

    # Extract actual site name (remove leading spaces if it's a site)
    selected_site = selected_option.strip() if selected_option.startswith("  ") else None

    if selected_site and selected_site in site_names:
        # Update URL when site is selected
        st.query_params["site"] = selected_site


# Display site content
if selected_site:
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


        # Get current site's municipality
        site_municipality = selected_site_obj.municipality if selected_site_obj else None

        # Sidebar metric comparisons
        with st.sidebar:
            st.title("Metric Comparisons")

            # Biomass comparison options
            st.subheader("Commercial Fish Biomass")
            biomass_comparison = st.selectbox(
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
                biomass_compare_scope = st.selectbox(
                    "Select average scope:",
                    ["Municipality Average", "All Sites Average"],
                    key="biomass_compare_scope"
                )

            # Hard Coral Cover comparison options
            st.subheader("Hard Coral Cover")
            coral_comparison = st.selectbox(
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
                coral_compare_scope = st.selectbox(
                    "Select average scope:",
                    ["Municipality Average", "All Sites Average"],
                    key="coral_compare_scope"
                )

            # Fleshy Algae comparison options
            st.subheader("Fleshy Algae Cover")
            algae_comparison = st.selectbox(
                "Compare fleshy algae with:",
                ["No Comparison", "Compare with Site", "Compare with Average"],
                key="algae_comparison"
            )

            algae_compare_site = None
            algae_compare_scope = None
            if algae_comparison == "Compare with Site":
                compare_sites = [site for site in site_names if site != selected_site]
                algae_compare_site = st.selectbox(
                    "Select site to compare fleshy algae:",
                    compare_sites,
                    key="algae_compare_site"
                )
            elif algae_comparison == "Compare with Average":
                algae_compare_scope = st.selectbox(
                    "Select average scope:",
                    ["Municipality Average", "All Sites Average"],
                    key="algae_compare_scope"
                )

            # Herbivore comparison options
            st.subheader("Herbivore Density")
            herbivore_comparison = st.selectbox(
                "Compare herbivore density with:",
                ["No Comparison", "Compare with Site", "Compare with Average"],
                key="herbivore_comparison"
            )

            herbivore_compare_site = None
            herbivore_compare_scope = None
            if herbivore_comparison == "Compare with Site":
                compare_sites = [site for site in site_names if site != selected_site]
                herbivore_compare_site = st.selectbox(
                    "Select site to compare herbivore density:",
                    compare_sites,
                    key="herbivore_compare_site"
                )
            elif herbivore_comparison == "Compare with Average":
                herbivore_compare_scope = st.selectbox(
                    "Select average scope:",
                    ["Municipality Average", "All Sites Average"],
                    key="herbivore_compare_scope"
                )

            # Omnivore comparison options
            st.subheader("Omnivore Density")
            omnivore_comparison = st.selectbox(
                "Compare omnivore density with:",
                ["No Comparison", "Compare with Site", "Compare with Average"],
                key="omnivore_comparison"
            )

            omnivore_compare_site = None
            omnivore_compare_scope = None
            if omnivore_comparison == "Compare with Site":
                compare_sites = [site for site in site_names if site != selected_site]
                omnivore_compare_site = st.selectbox(
                    "Select site to compare omnivore density:",
                    compare_sites,
                    key="omnivore_compare_site"
                )
            elif omnivore_comparison == "Compare with Average":
                omnivore_compare_scope = st.selectbox(
                    "Select average scope:",
                    ["Municipality Average", "All Sites Average"],
                    key="omnivore_compare_scope"
                )

            # Corallivore comparison options
            st.subheader("Corallivore Density")
            corallivore_comparison = st.selectbox(
                "Compare corallivore density with:",
                ["No Comparison", "Compare with Site", "Compare with Average"],
                key="corallivore_comparison"
            )

            corallivore_compare_site = None
            corallivore_compare_scope = None
            if corallivore_comparison == "Compare with Site":
                compare_sites = [site for site in site_names if site != selected_site]
                corallivore_compare_site = st.selectbox(
                    "Select site to compare corallivore density:",
                    compare_sites,
                    key="corallivore_compare_site"
                )
            elif corallivore_comparison == "Compare with Average":
                corallivore_compare_scope = st.selectbox(
                    "Select average scope:",
                    ["Municipality Average", "All Sites Average"],
                    key="corallivore_compare_scope"
                )

            # Add Bleaching comparison options
            st.subheader("Bleaching")
            bleaching_comparison = st.selectbox(
                "Compare bleaching with:",
                ["No Comparison", "Compare with Site", "Compare with Average"],
                key="bleaching_comparison"
            )

            bleaching_compare_site = None
            bleaching_compare_scope = None
            if bleaching_comparison == "Compare with Site":
                compare_sites = [site for site in site_names if site != selected_site]
                bleaching_compare_site = st.selectbox(
                    "Select site to compare bleaching:",
                    compare_sites,
                    key="bleaching_compare_site"
                )
            elif bleaching_comparison == "Compare with Average":
                bleaching_compare_scope = st.selectbox(
                    "Select average scope:",
                    ["Municipality Average", "All Sites Average"],
                    key="bleaching_compare_scope"
                )

            # Add Rubble comparison options
            st.subheader("Rubble Cover")
            rubble_comparison = st.selectbox(
                "Compare rubble cover with:",
                ["No Comparison", "Compare with Site", "Compare with Average"],
                key="rubble_comparison"
            )

            rubble_compare_site = None
            rubble_compare_scope = None
            if rubble_comparison == "Compare with Site":
                compare_sites = [site for site in site_names if site != selected_site]
                rubble_compare_site = st.selectbox(
                    "Select site to compare rubble cover:",
                    compare_sites,
                    key="rubble_compare_site"
                )
            elif rubble_comparison == "Compare with Average":
                rubble_compare_scope = st.selectbox(
                    "Select average scope:",
                    ["Municipality Average", "All Sites Average"],
                    key="rubble_compare_scope"
                )

        # Display metrics section with comparisons
        if selected_site_obj:
            st.header("Site Metrics")

            # Configure Plotly chart settings
            plotly_config = {
                'responsive': True,
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['lasso2d', 'select2d']
            }

            # Add spacing before first chart
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Get biomass data and comparison
            biomass_data = data_processor.get_biomass_data(selected_site)
            biomass_comparison_data = None
            if biomass_comparison == "Compare with Site" and biomass_compare_site:
                biomass_comparison_data = data_processor.get_biomass_data(biomass_compare_site)
            elif biomass_comparison == "Compare with Average":
                municipality = site_municipality if biomass_compare_scope == "Municipality Average" else None
                biomass_comparison_data = data_processor.get_average_biomass_data(
                    exclude_site=selected_site,
                    municipality=municipality
                )
            biomass_fig, biomass_config = graph_generator.create_time_series(
                biomass_data,
                f"Commercial Fish Biomass - {selected_site}",
                "Biomass (kg/ha)",
                comparison_data=biomass_comparison_data
            )
            st.plotly_chart(biomass_fig, use_container_width=True, config=biomass_config, key='biomass_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Get coral cover data and comparison
            coral_data = data_processor.get_metric_data(selected_site, 'hard_coral')
            coral_comparison_data = None
            if coral_comparison == "Compare with Site" and coral_compare_site:
                coral_comparison_data = data_processor.get_metric_data(coral_compare_site, 'hard_coral')
            elif coral_comparison == "Compare with Average":
                municipality = site_municipality if coral_compare_scope == "Municipality Average" else None
                coral_comparison_data = data_processor.get_average_metric_data(
                    'hard_coral',
                    exclude_site=selected_site,
                    municipality=municipality
                )
            coral_fig, coral_config = graph_generator.create_time_series(
                coral_data,
                f"Hard Coral Cover - {selected_site}",
                "Cover (%)",
                comparison_data=coral_comparison_data
            )
            st.plotly_chart(coral_fig, use_container_width=True, config=coral_config, key='coral_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Get fleshy algae data and comparison
            algae_data = data_processor.get_metric_data(selected_site, 'fleshy_algae')
            algae_comparison_data = None
            if algae_comparison == "Compare with Site" and algae_compare_site:
                algae_comparison_data = data_processor.get_metric_data(algae_compare_site, 'fleshy_algae')
            elif algae_comparison == "Compare with Average":
                municipality = site_municipality if algae_compare_scope == "Municipality Average" else None
                algae_comparison_data = data_processor.get_average_metric_data(
                    'fleshy_algae',
                    exclude_site=selected_site,
                    municipality=municipality
                )
            algae_fig, algae_config = graph_generator.create_time_series(
                algae_data,
                f"Fleshy Algae Cover - {selected_site}",
                "Cover (%)",
                comparison_data=algae_comparison_data
            )
            st.plotly_chart(algae_fig, use_container_width=True, config=algae_config, key='algae_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Get herbivore data and comparison
            herbivore_data = data_processor.get_metric_data(selected_site, 'herbivore')
            herbivore_comparison_data = None
            if herbivore_comparison == "Compare with Site" and herbivore_compare_site:
                herbivore_comparison_data = data_processor.get_metric_data(herbivore_compare_site, 'herbivore')
            elif herbivore_comparison == "Compare with Average":
                municipality = site_municipality if herbivore_compare_scope == "Municipality Average" else None
                herbivore_comparison_data = data_processor.get_average_metric_data(
                    'herbivore',
                    exclude_site=selected_site,
                    municipality=municipality
                )
            herbivore_fig, herbivore_config = graph_generator.create_time_series(
                herbivore_data,
                f"Herbivore Density - {selected_site}",
                "Density (ind/ha)",
                comparison_data=herbivore_comparison_data
            )
            st.plotly_chart(herbivore_fig, use_container_width=True, config=herbivore_config, key='herbivore_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Get omnivore data and comparison
            omnivore_data = data_processor.get_metric_data(selected_site, 'omnivore')
            omnivore_comparison_data = None
            if omnivore_comparison == "Compare with Site" and omnivore_compare_site:
                omnivore_comparison_data = data_processor.get_metric_data(omnivore_compare_site, 'omnivore')
            elif omnivore_comparison == "Compare with Average":
                municipality = site_municipality if omnivore_compare_scope == "Municipality Average" else None
                omnivore_comparison_data = data_processor.get_average_metric_data(
                    'omnivore',
                    exclude_site=selected_site,
                    municipality=municipality
                )
            omnivore_fig, omnivore_config = graph_generator.create_time_series(
                omnivore_data,
                f"Omnivore Density - {selected_site}",
                "Density (ind/ha)",
                comparison_data=omnivore_comparison_data
            )
            st.plotly_chart(omnivore_fig, use_container_width=True, config=omnivore_config, key='omnivore_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Get corallivore data and comparison
            corallivore_data = data_processor.get_metric_data(selected_site, 'corallivore')
            corallivore_comparison_data = None
            if corallivore_comparison == "Compare with Site" and corallivore_compare_site:
                corallivore_comparison_data = data_processor.get_metric_data(corallivore_compare_site, 'corallivore')
            elif corallivore_comparison == "Compare with Average":
                municipality = site_municipality if corallivore_compare_scope == "Municipality Average" else None
                corallivore_comparison_data = data_processor.get_average_metric_data(
                    'corallivore',
                    exclude_site=selected_site,
                    municipality=municipality
                )
            corallivore_fig, corallivore_config = graph_generator.create_time_series(
                corallivore_data,
                f"Corallivore Density - {selected_site}",
                "Density (ind/ha)",
                comparison_data=corallivore_comparison_data
            )
            st.plotly_chart(corallivore_fig, use_container_width=True, config=corallivore_config, key='corallivore_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Add bleaching visualization
            bleaching_data = data_processor.get_metric_data(selected_site, 'bleaching')
            bleaching_comparison_data = None
            if bleaching_comparison == "Compare with Site" and bleaching_compare_site:
                bleaching_comparison_data = data_processor.get_metric_data(bleaching_compare_site, 'bleaching')
            elif bleaching_comparison == "Compare with Average":
                municipality = site_municipality if bleaching_compare_scope == "Municipality Average" else None
                bleaching_comparison_data = data_processor.get_average_metric_data(
                    'bleaching',
                    exclude_site=selected_site,
                    municipality=municipality
                )
            bleaching_fig, bleaching_config = graph_generator.create_time_series(
                bleaching_data,
                f"Bleaching - {selected_site}",
                "Bleaching (%)",
                comparison_data=bleaching_comparison_data
            )
            st.plotly_chart(bleaching_fig, use_container_width=True, config=bleaching_config, key='bleaching_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Add rubble visualization
            rubble_data = data_processor.get_metric_data(selected_site, 'rubble')
            rubble_comparison_data = None
            if rubble_comparison == "Compare with Site" and rubble_compare_site:
                rubble_comparison_data = data_processor.get_metric_data(rubble_compare_site, 'rubble')
            elif rubble_comparison == "Compare with Average":
                municipality = site_municipality if rubble_compare_scope == "Municipality Average" else None
                rubble_comparison_data = data_processor.get_average_metric_data(
                    'rubble',
                    exclude_site=selected_site,
                    municipality=municipality
                )
            rubble_fig, rubble_config = graph_generator.create_time_series(
                rubble_data,
                f"Rubble Cover - {selected_site}",
                "Rubble Cover (%)",
                comparison_data=rubble_comparison_data
            )
            st.plotly_chart(rubble_fig, use_container_width=True, config=rubble_config, key='rubble_chart')