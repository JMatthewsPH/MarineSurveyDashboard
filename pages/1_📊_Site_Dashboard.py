"""
Site Dashboard Page with detailed metrics for selected marine sites

This page displays detailed ecological metrics for a selected marine site,
including commercial fish biomass, hard coral cover, and other indicators.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Import utilities
from utils.data_processor import DataProcessor
from utils.graph_generator import GraphGenerator
from utils.branding import display_logo
from utils.ui_helpers import loading_spinner, skeleton_chart, create_loading_placeholder, skeleton_text_placeholder
from utils.translations import TRANSLATIONS
from utils.database import get_db

# Page configuration
st.set_page_config(
    page_title="Site Dashboard | Marine Conservation Dashboard",
    page_icon="📊",
    layout="wide"
)

# Initialize session state for language if not already set
if 'language' not in st.session_state:
    st.session_state.language = 'en'  # Default to English

# CSS for mobile-responsive layout
def load_css():
    with open('assets/site_styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Load custom CSS
load_css()

# Initialize data processor with database connection
@st.cache_resource
def get_data_processor():
    db = next(get_db())
    return DataProcessor(db)

# Main function to run the dashboard
def main():
    # Display logo and header
    display_logo()
    
    # Set language code for translations
    language_code = st.session_state.language
    
    # Get data processor and graph generator
    data_processor = get_data_processor()
    graph_generator = GraphGenerator(data_processor)
    
    # Get all sites
    sites = data_processor.get_sites()
    
    # Create alphabetically sorted site names for dropdown
    alphabetical_site_names = sorted([site.name for site in sites])
    
    # Top navigation
    st.title(TRANSLATIONS[language_code]['dashboard'])
    
    # Site selection in main area (more prominent)
    selected_site = st.selectbox(
        TRANSLATIONS[language_code]['select_site'],
        alphabetical_site_names,
        key="site_selector"
    )
    
    # Find the selected site object
    selected_site_obj = next((site for site in sites if site.name == selected_site), None)
    
    if selected_site:
        # Mobile-responsive container for all charts
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Site Information Section
        st.header(f"{TRANSLATIONS[language_code]['site_description']} - {selected_site}")
        
        # For desktop, use columns with 1:2 ratio
        # For mobile, CSS will stack these vertically

        cols = st.columns([1, 2])

        with cols[0]:
            # Create a placeholder for the image while it loads
            image_placeholder = st.empty()
            with image_placeholder:
                create_loading_placeholder(
                    st, 
                    message="Loading site image...", 
                    height=300
                )
            
            # Replace with the actual image
            image_placeholder.image(
                "https://via.placeholder.com/400x300", 
                use_container_width=True, 
                output_format="JPEG", 
                caption=selected_site
            )

        with cols[1]:
            # Show a loading placeholder for the description
            desc_placeholder = st.empty()
            with desc_placeholder:
                skeleton_text_placeholder(lines=5)
            
            # Load the site description with spinner
            with loading_spinner("Loading site description..."):
                language_code = st.session_state.language
                
                # Get description based on language
                if language_code == 'en':
                    description = selected_site_obj.description_en
                elif language_code == 'tl':
                    description = selected_site_obj.description_fil  # Using Filipino description for Tagalog
                else:  # Cebuano - fallback to English for now
                    description = selected_site_obj.description_en
                    
                # Default description if not available
                if not description:
                    description = f"{TRANSLATIONS[language_code]['site_desc_placeholder']} ({selected_site})"
            
            # Replace the placeholder with the actual content
            desc_placeholder.markdown(f"""<div class="site-description-text">
                               {description}
                             </div>""", unsafe_allow_html=True)


        # Get current site's municipality
        site_municipality = selected_site_obj.municipality if selected_site_obj else None

        # Sidebar metric comparisons and date range selection
        with st.sidebar:
            st.title(TRANSLATIONS[st.session_state.language]['analysis_options'])
            
            # Date Range Selection
            st.header(TRANSLATIONS[st.session_state.language]['date_range'])
            
            # Get the min and max dates from all surveys 
            all_surveys = []
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
            date_range = (pd.to_datetime(start_date), pd.to_datetime(end_date)) if start_date <= end_date else None
            if start_date > end_date:
                st.error(TRANSLATIONS[st.session_state.language]['date_range_error'])
                
            st.markdown("---")
            
            st.title(TRANSLATIONS[st.session_state.language]['metric_comparisons'])

            # Biomass comparison options
            st.subheader("Commercial Fish Biomass")
            biomass_comparison = st.selectbox(
                "Compare biomass with:",
                ["No Comparison", "Compare with Sites", "Compare with Average"],
                key="biomass_comparison"
            )

            biomass_compare_sites = None
            biomass_compare_scope = None
            biomass_compare_labels = None
            
            if biomass_comparison == "Compare with Sites":
                compare_sites = [site for site in alphabetical_site_names if site != selected_site]
                biomass_compare_sites = st.multiselect(
                    "Select sites to compare biomass:",
                    compare_sites,
                    key="biomass_compare_sites",
                    max_selections=5  # Limit to 5 sites for readability
                )
                if biomass_compare_sites:
                    # Show option to group by municipality (helps organize large datasets)
                    group_by_municipality = st.checkbox("Group by municipality", key="biomass_group_by_muni", value=False)
                    if group_by_municipality:
                        site_to_muni = {site.name: site.municipality for site in sites}
                        biomass_compare_labels = [f"{site} ({site_to_muni.get(site, 'Unknown')})" for site in biomass_compare_sites]
                    else:
                        biomass_compare_labels = biomass_compare_sites
                        
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
                compare_sites = [site for site in alphabetical_site_names if site != selected_site]
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
                compare_sites = [site for site in alphabetical_site_names if site != selected_site]
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
                compare_sites = [site for site in alphabetical_site_names if site != selected_site]
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
                compare_sites = [site for site in alphabetical_site_names if site != selected_site]
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
                compare_sites = [site for site in alphabetical_site_names if site != selected_site]
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
                compare_sites = [site for site in alphabetical_site_names if site != selected_site]
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
                "Compare rubble with:",
                ["No Comparison", "Compare with Site", "Compare with Average"],
                key="rubble_comparison"
            )

            rubble_compare_site = None
            rubble_compare_scope = None
            if rubble_comparison == "Compare with Site":
                compare_sites = [site for site in alphabetical_site_names if site != selected_site]
                rubble_compare_site = st.selectbox(
                    "Select site to compare rubble:",
                    compare_sites,
                    key="rubble_compare_site"
                )
            elif rubble_comparison == "Compare with Average":
                rubble_compare_scope = st.selectbox(
                    "Select average scope:",
                    ["Municipality Average", "All Sites Average"],
                    key="rubble_compare_scope"
                )

        # Create graphs section
        st.header(TRANSLATIONS[language_code]['site_metrics'])
        
        # Biomass Section with loading states
        if selected_site:
            # Create a placeholder for the biomass chart with loading indicator
            biomass_chart_container = st.container()
            with biomass_chart_container:
                # Show title for chart
                st.subheader(f"Commercial Fish Biomass - {selected_site}")
                
                # Create a loading placeholder and skeleton chart that we'll replace later
                biomass_chart_placeholder = st.empty()
                with biomass_chart_placeholder:
                    # Create a loading indicator within the placeholder
                    create_loading_placeholder(
                        st, 
                        message="Loading biomass data...", 
                        height=400
                    )
                    
                    # Display a skeleton chart while data is loading
                    st.plotly_chart(
                        skeleton_chart(height=400, chart_type="line"),
                        use_container_width=True,
                        key="biomass_skeleton_chart" 
                    )
            
            # Get biomass data and comparison with loading indicator
            with loading_spinner("Processing fish biomass data..."):
                biomass_data = data_processor.get_biomass_data(selected_site)
                biomass_comparison_data = None
                biomass_comparison_labels = None
                
                if biomass_comparison == "Compare with Sites" and biomass_compare_sites:
                    # Get data for multiple comparison sites
                    biomass_comparison_data = []
                    for compare_site in biomass_compare_sites:
                        site_data = data_processor.get_biomass_data(compare_site)
                        if not site_data.empty:
                            biomass_comparison_data.append(site_data)
                    
                    # Set comparison labels (either plain site names or with municipality)
                    if not biomass_compare_labels:
                        biomass_compare_labels = biomass_compare_sites
                        
                elif biomass_comparison == "Compare with Average":
                    municipality = site_municipality if biomass_compare_scope == "Municipality Average" else None
                    biomass_comparison_data = data_processor.get_average_biomass_data(
                        exclude_site=selected_site,
                        municipality=municipality
                    )
                    
                    # Set label for the average
                    if biomass_compare_scope == "Municipality Average" and site_municipality:
                        biomass_comparison_labels = [f"Avg. {site_municipality}"]
                    else:
                        biomass_comparison_labels = ["Avg. All Sites"]
            
            # Create biomass visualization
            with loading_spinner("Generating biomass chart..."):
                # Generate the plotly figure
                biomass_fig, biomass_config = graph_generator.create_time_series(
                    biomass_data,
                    f"Commercial Fish Biomass - {selected_site}",
                    "Biomass (kg/ha)",
                    comparison_data=biomass_comparison_data,
                    comparison_labels=biomass_comparison_labels,
                    date_range=date_range
                )
                
                # Update filename in config
                biomass_config['toImageButtonOptions']['filename'] = f'biomass_{selected_site}'
                
                # Replace the placeholder with the real chart
                biomass_chart_placeholder.empty()  # Clear the placeholder
                biomass_chart_placeholder.plotly_chart(
                    biomass_fig, 
                    use_container_width=True, 
                    config=biomass_config,
                    key="biomass_chart"
                )
            
            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)
            
            # Coral Cover Section
            coral_chart_container = st.container()
            with coral_chart_container:
                # Show title for chart
                st.subheader(f"Hard Coral Cover - {selected_site}")
                
                # Create a loading placeholder that we'll replace later
                coral_chart_placeholder = st.empty()
                with coral_chart_placeholder:
                    # Create a loading indicator within the placeholder
                    create_loading_placeholder(
                        st, 
                        message="Loading coral cover data...", 
                        height=400
                    )
                    
                    # Display a skeleton chart while data is loading
                    st.plotly_chart(
                        skeleton_chart(height=400, chart_type="line"),
                        use_container_width=True,
                        key="coral_skeleton_chart"
                    )
            
            # Get coral cover data and comparison with loading indicator
            with loading_spinner("Processing coral cover data..."):
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
            
            # Create coral cover visualization
            with loading_spinner("Generating coral cover chart..."):
                # Get the comparison label
                coral_comparison_label = None
                if coral_comparison == "Compare with Site" and coral_compare_site:
                    coral_comparison_label = [coral_compare_site]
                elif coral_comparison == "Compare with Average":
                    if coral_compare_scope == "Municipality Average" and site_municipality:
                        coral_comparison_label = [f"Avg. {site_municipality}"]
                    else:
                        coral_comparison_label = ["Avg. All Sites"]
                
                # Generate the plotly figure
                coral_fig, coral_config = graph_generator.create_time_series(
                    coral_data,
                    f"Hard Coral Cover - {selected_site}",
                    "Cover (%)",
                    comparison_data=coral_comparison_data,
                    comparison_labels=coral_comparison_label,
                    date_range=date_range
                )
                
                # Update filename in config
                coral_config['toImageButtonOptions']['filename'] = f'coral_cover_{selected_site}'
                
                # Replace the placeholder with the real chart
                coral_chart_placeholder.empty()  # Clear the placeholder
                coral_chart_placeholder.plotly_chart(
                    coral_fig, 
                    use_container_width=True, 
                    config=coral_config,
                    key="coral_chart"
                )
            
            # Add spacing between charts  
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)
            
            # Get fleshy algae data and comparison
            with loading_spinner("Processing fleshy algae data..."):
                algae_data = data_processor.get_metric_data(selected_site, 'fleshy_algae')
                algae_comparison_data = None
                
                if algae_comparison == "Compare with Site" and algae_compare_site:
                    algae_comparison_data = data_processor.get_metric_data(algae_compare_site, 'fleshy_algae')
                    algae_comparison_label = [algae_compare_site]
                elif algae_comparison == "Compare with Average":
                    municipality = site_municipality if algae_compare_scope == "Municipality Average" else None
                    algae_comparison_data = data_processor.get_average_metric_data(
                        'fleshy_algae',
                        exclude_site=selected_site,
                        municipality=municipality
                    )
                    
                    if algae_compare_scope == "Municipality Average" and site_municipality:
                        algae_comparison_label = [f"Avg. {site_municipality}"]
                    else:
                        algae_comparison_label = ["Avg. All Sites"]
                else:
                    algae_comparison_label = None
                
                # Generate the plotly figure
                algae_fig, algae_config = graph_generator.create_time_series(
                    algae_data,
                    f"Fleshy Algae Cover - {selected_site}",
                    "Cover (%)",
                    comparison_data=algae_comparison_data,
                    comparison_labels=algae_comparison_label,
                    date_range=date_range
                )
                
                # Update filename in config
                algae_config['toImageButtonOptions']['filename'] = f'algae_cover_{selected_site}'
            
            # Display the fleshy algae chart
            st.subheader(f"Fleshy Algae Cover - {selected_site}")
            st.plotly_chart(algae_fig, use_container_width=True, config=algae_config, key='algae_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Get herbivore data and comparison
            with loading_spinner("Processing herbivore density data..."):
                herbivore_data = data_processor.get_metric_data(selected_site, 'herbivore')
                herbivore_comparison_data = None
                
                if herbivore_comparison == "Compare with Site" and herbivore_compare_site:
                    herbivore_comparison_data = data_processor.get_metric_data(herbivore_compare_site, 'herbivore')
                    herbivore_comparison_label = [herbivore_compare_site]
                elif herbivore_comparison == "Compare with Average":
                    municipality = site_municipality if herbivore_compare_scope == "Municipality Average" else None
                    herbivore_comparison_data = data_processor.get_average_metric_data(
                        'herbivore',
                        exclude_site=selected_site,
                        municipality=municipality
                    )
                    
                    if herbivore_compare_scope == "Municipality Average" and site_municipality:
                        herbivore_comparison_label = [f"Avg. {site_municipality}"]
                    else:
                        herbivore_comparison_label = ["Avg. All Sites"]
                else:
                    herbivore_comparison_label = None
                
                # Generate the plotly figure
                herbivore_fig, herbivore_config = graph_generator.create_time_series(
                    herbivore_data,
                    f"Herbivore Density - {selected_site}",
                    "Density (ind/ha)",
                    comparison_data=herbivore_comparison_data,
                    comparison_labels=herbivore_comparison_label,
                    date_range=date_range
                )
                
                # Update filename in config
                herbivore_config['toImageButtonOptions']['filename'] = f'herbivore_density_{selected_site}'
            
            # Display the herbivore chart
            st.subheader(f"Herbivore Density - {selected_site}")
            st.plotly_chart(herbivore_fig, use_container_width=True, config=herbivore_config, key='herbivore_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Get omnivore data and comparison
            with loading_spinner("Processing omnivore density data..."):
                omnivore_data = data_processor.get_metric_data(selected_site, 'omnivore')
                omnivore_comparison_data = None
                
                if omnivore_comparison == "Compare with Site" and omnivore_compare_site:
                    omnivore_comparison_data = data_processor.get_metric_data(omnivore_compare_site, 'omnivore')
                    omnivore_comparison_label = [omnivore_compare_site]
                elif omnivore_comparison == "Compare with Average":
                    municipality = site_municipality if omnivore_compare_scope == "Municipality Average" else None
                    omnivore_comparison_data = data_processor.get_average_metric_data(
                        'omnivore',
                        exclude_site=selected_site,
                        municipality=municipality
                    )
                    
                    if omnivore_compare_scope == "Municipality Average" and site_municipality:
                        omnivore_comparison_label = [f"Avg. {site_municipality}"]
                    else:
                        omnivore_comparison_label = ["Avg. All Sites"]
                else:
                    omnivore_comparison_label = None
                
                # Generate the plotly figure
                omnivore_fig, omnivore_config = graph_generator.create_time_series(
                    omnivore_data,
                    f"Omnivore Density - {selected_site}",
                    "Density (ind/ha)",
                    comparison_data=omnivore_comparison_data,
                    comparison_labels=omnivore_comparison_label,
                    date_range=date_range
                )
                
                # Update filename in config
                omnivore_config['toImageButtonOptions']['filename'] = f'omnivore_density_{selected_site}'
            
            # Display the omnivore chart
            st.subheader(f"Omnivore Density - {selected_site}")
            st.plotly_chart(omnivore_fig, use_container_width=True, config=omnivore_config, key='omnivore_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Get corallivore data and comparison
            with loading_spinner("Processing corallivore density data..."):
                corallivore_data = data_processor.get_metric_data(selected_site, 'corallivore')
                corallivore_comparison_data = None
                
                if corallivore_comparison == "Compare with Site" and corallivore_compare_site:
                    corallivore_comparison_data = data_processor.get_metric_data(corallivore_compare_site, 'corallivore')
                    corallivore_comparison_label = [corallivore_compare_site]
                elif corallivore_comparison == "Compare with Average":
                    municipality = site_municipality if corallivore_compare_scope == "Municipality Average" else None
                    corallivore_comparison_data = data_processor.get_average_metric_data(
                        'corallivore',
                        exclude_site=selected_site,
                        municipality=municipality
                    )
                    
                    if corallivore_compare_scope == "Municipality Average" and site_municipality:
                        corallivore_comparison_label = [f"Avg. {site_municipality}"]
                    else:
                        corallivore_comparison_label = ["Avg. All Sites"]
                else:
                    corallivore_comparison_label = None
                
                # Generate the plotly figure
                corallivore_fig, corallivore_config = graph_generator.create_time_series(
                    corallivore_data,
                    f"Corallivore Density - {selected_site}",
                    "Density (ind/ha)",
                    comparison_data=corallivore_comparison_data,
                    comparison_labels=corallivore_comparison_label,
                    date_range=date_range
                )
                
                # Update filename in config
                corallivore_config['toImageButtonOptions']['filename'] = f'corallivore_density_{selected_site}'
            
            # Display the corallivore chart
            st.subheader(f"Corallivore Density - {selected_site}")
            st.plotly_chart(corallivore_fig, use_container_width=True, config=corallivore_config, key='corallivore_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Add bleaching visualization
            with loading_spinner("Processing bleaching data..."):
                bleaching_data = data_processor.get_metric_data(selected_site, 'bleaching')
                bleaching_comparison_data = None
                
                if bleaching_comparison == "Compare with Site" and bleaching_compare_site:
                    bleaching_comparison_data = data_processor.get_metric_data(bleaching_compare_site, 'bleaching')
                    bleaching_comparison_label = [bleaching_compare_site]
                elif bleaching_comparison == "Compare with Average":
                    municipality = site_municipality if bleaching_compare_scope == "Municipality Average" else None
                    bleaching_comparison_data = data_processor.get_average_metric_data(
                        'bleaching',
                        exclude_site=selected_site,
                        municipality=municipality
                    )
                    
                    if bleaching_compare_scope == "Municipality Average" and site_municipality:
                        bleaching_comparison_label = [f"Avg. {site_municipality}"]
                    else:
                        bleaching_comparison_label = ["Avg. All Sites"]
                else:
                    bleaching_comparison_label = None
                
                bleaching_fig, bleaching_config = graph_generator.create_time_series(
                    bleaching_data,
                    f"Bleaching - {selected_site}",
                    "Bleaching (%)",
                    comparison_data=bleaching_comparison_data,
                    comparison_labels=bleaching_comparison_label,
                    date_range=date_range
                )
                
                # Update filename in config
                bleaching_config['toImageButtonOptions']['filename'] = f'bleaching_{selected_site}'
            
            st.subheader(f"Bleaching - {selected_site}")
            st.plotly_chart(bleaching_fig, use_container_width=True, config=bleaching_config, key='bleaching_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Add rubble visualization
            with loading_spinner("Processing rubble data..."):
                rubble_data = data_processor.get_metric_data(selected_site, 'rubble')
                rubble_comparison_data = None
                
                if rubble_comparison == "Compare with Site" and rubble_compare_site:
                    rubble_comparison_data = data_processor.get_metric_data(rubble_compare_site, 'rubble')
                    rubble_comparison_label = [rubble_compare_site]
                elif rubble_comparison == "Compare with Average":
                    municipality = site_municipality if rubble_compare_scope == "Municipality Average" else None
                    rubble_comparison_data = data_processor.get_average_metric_data(
                        'rubble',
                        exclude_site=selected_site,
                        municipality=municipality
                    )
                    
                    if rubble_compare_scope == "Municipality Average" and site_municipality:
                        rubble_comparison_label = [f"Avg. {site_municipality}"]
                    else:
                        rubble_comparison_label = ["Avg. All Sites"]
                else:
                    rubble_comparison_label = None
                
                rubble_fig, rubble_config = graph_generator.create_time_series(
                    rubble_data,
                    f"Rubble Cover - {selected_site}",
                    "Rubble Cover (%)",
                    comparison_data=rubble_comparison_data,
                    comparison_labels=rubble_comparison_label,
                    date_range=date_range
                )
                
                # Update filename in config
                rubble_config['toImageButtonOptions']['filename'] = f'rubble_{selected_site}'
            
            st.subheader(f"Rubble Cover - {selected_site}")
            st.plotly_chart(rubble_fig, use_container_width=True, config=rubble_config, key='rubble_chart')
            
            # Close the mobile-responsive charts container
            st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # No site selected (this shouldn't happen with the default selection)
        st.info(TRANSLATIONS[language_code]['select_site_prompt'])

# Run the main function when this file is executed
if __name__ == "__main__":
    main()