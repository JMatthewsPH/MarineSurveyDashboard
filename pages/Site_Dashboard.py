import streamlit as st

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="Site Dashboard",
    page_icon="assets/branding/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': None,
        'Get help': None,
        'Report a bug': None
    }
)

# Hide this page from navigation using JavaScript
hide_page_js = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    function hideNavItem() {
        const navItems = document.querySelectorAll('[data-testid="stSidebarNav"] li a');
        navItems.forEach(item => {
            if (item.innerText.includes('Site Dashboard')) {
                const listItem = item.closest('li');
                if (listItem) {
                    listItem.style.display = 'none';
                    console.log('Hidden Site Dashboard from nav');
                }
            }
        });
        
        // Try again if navigation isn't fully loaded yet
        if (navItems.length === 0) {
            setTimeout(hideNavItem, 500);
        }
    }
    
    // Initial attempt
    hideNavItem();
    
    // Keep trying in case the navigation loads after our script
    setInterval(hideNavItem, 3000);
});
</script>
"""

st.markdown(hide_page_js, unsafe_allow_html=True)

import os
import pandas as pd
from datetime import datetime, date
from utils.data_processor import DataProcessor
from utils.graph_generator import GraphGenerator
from utils.translations import TRANSLATIONS
from utils.database import get_db
from utils.branding import display_logo, add_favicon
from utils.export_utils import create_export_section, generate_site_report_pdf, add_chart_export_button
from utils.ui_helpers import (
    loading_spinner, 
    skeleton_chart, 
    create_loading_placeholder, 
    load_css, 
    skeleton_text_placeholder
)

# Import navigation utilities
from utils.navigation import display_navigation

# Apply centralized CSS styles
st.markdown(load_css(), unsafe_allow_html=True)


# Initialize language in session state if not present
if 'language' not in st.session_state:
    st.session_state.language = "en"  # Default to English

# Language code mapping
LANGUAGE_DISPLAY = {
    "en": "English",
    "tl": "Tagalog",
    "ceb": "Cebuano"
}

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

# Combine in desired order for display in sidebar
site_names = zamboanguita_sites + siaton_sites + santa_catalina_sites

# Create alphabetical list for comparison dropdowns
alphabetical_site_names = sorted([site.name for site in sites])




# Add favicon to the page
add_favicon()

# Sidebar for site selection and language
with st.sidebar:
    st.title(TRANSLATIONS[st.session_state.language]['settings'])
    
    # Language selection
    selected_language = st.selectbox(
        TRANSLATIONS[st.session_state.language]['lang_toggle'],
        list(LANGUAGE_DISPLAY.values()),
        key="language_selector",
        index=list(LANGUAGE_DISPLAY.values()).index(LANGUAGE_DISPLAY.get(st.session_state.language, "English"))
    )
    
    # Convert display language back to language code
    for code, name in LANGUAGE_DISPLAY.items():
        if name == selected_language:
            st.session_state.language = code
            break

    # Streamlit navigation is now automatically handled in the sidebar

    # Site selection with municipality grouping
    st.subheader(TRANSLATIONS[st.session_state.language]['select_site'])
    
    # Create a custom CSS class for municipality options
    municipalities = ["Zamboanguita", "Siaton", "Santa Catalina"]
    
    # Create a custom formatting function for the dropdown
    def format_site_option(option):
        if option in municipalities:
            # Use uppercase for municipality headers
            return f"{option.upper()}"
        else:
            # Use non-breaking space entity to ensure indentation is preserved
            return f"- {option.strip()}"
    
    # Create the options list with municipalities as headers and alphabetically sorted sites
    site_options = []
    if zamboanguita_sites:
        site_options.append("Zamboanguita")
        site_options.extend([f"  {site}" for site in sorted(zamboanguita_sites)])
    if siaton_sites:
        site_options.append("Siaton")
        site_options.extend([f"  {site}" for site in sorted(siaton_sites)])
    if santa_catalina_sites:
        site_options.append("Santa Catalina")
        site_options.extend([f"  {site}" for site in sorted(santa_catalina_sites)])

    selected_option = st.selectbox(
        TRANSLATIONS[st.session_state.language]['choose_site'],
        site_options,
        index=site_options.index(f"  {st.query_params.get('site')}") if st.query_params.get('site') in [s.strip() for s in site_options] else 0,
        format_func=format_site_option
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
        # Display small logo at the top of the dashboard
        display_logo(size="small")
        
        # Display the site title
        st.title(f"{selected_site} {TRANSLATIONS[st.session_state.language]['dashboard']}")

        # Site Description Section
        st.header(TRANSLATIONS[st.session_state.language]['site_description'])

        # Use different column ratios based on screen size (CSS will handle the actual responsiveness)
        # For larger screens, we use a 1:2 ratio
        # For mobile, CSS will stack these vertically

        cols = st.columns([1, 2])

        with cols[0]:
            # Create a placeholder for the image while it loads
            image_placeholder = create_loading_placeholder(
                st, 
                message="Loading site image...", 
                height=300
            )
            
            # Display the image (in a real app, this would be loaded asynchronously)
            image_placeholder.empty()
            st.image("https://via.placeholder.com/400x300", use_container_width=True, 
                     output_format="JPEG", caption=selected_site)

        with cols[1]:
            # Show a loading placeholder for the description
            desc_placeholder = st.empty()
            with desc_placeholder:
                skeleton_text_placeholder(lines=5)
            
            # Process the site description without spinner
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
            
            # Confidence Interval checkbox
            show_confidence_interval = st.checkbox(
                "Show Confidence Interval",
                value=False  # Default to unchecked
            )
            
            # Helper function to get all site data for export
            def get_site_data_for_export(site_name):
                """Get all metrics data for the selected site in a single DataFrame"""
                # Start with an empty DataFrame with date column
                result_df = pd.DataFrame(columns=["date"])
                
                # Get all the metrics data
                # First, let's get all available metrics
                metrics = ["hard_coral", "fleshy_algae", "herbivore", "carnivore", 
                           "omnivore", "corallivore", "bleaching", "rubble"]
                
                # Process each metric
                for metric in metrics:
                    # Get the standard metric name from the mapping
                    metric_column = data_processor.METRIC_MAP[metric]
                    df = data_processor.get_metric_data(site_name, metric)
                    
                    if not df.empty:
                        # Check the actual columns in the DataFrame
                        available_columns = df.columns.tolist()
                        
                        # If we have the metric column, add it to the result
                        if metric_column in available_columns:
                            # Create a copy of just the columns we need
                            metric_data = df[["date", metric_column]].copy()
                            
                            # Merge with the result dataframe
                            if result_df.empty:
                                result_df = metric_data.copy()
                            else:
                                result_df = result_df.merge(metric_data, on="date", how="outer")
                
                # Commercial biomass is handled separately
                biomass_df = data_processor.get_biomass_data(site_name)
                if not biomass_df.empty:
                    # Check columns actually in the DataFrame
                    biomass_columns = biomass_df.columns.tolist()
                    
                    # Print the available columns for debugging
                    st.write(f"Biomass DataFrame columns: {biomass_columns}")
                    
                    # Find the column that contains 'biomass' in the name
                    biomass_col = None
                    for col in biomass_columns:
                        if 'biomass' in col.lower():
                            biomass_col = col
                            break
                    
                    if biomass_col:
                        # Use the actual column name from the DataFrame
                        biomass_data = biomass_df[["date", biomass_col]].copy()
                        
                        # Rename to standard name for merging
                        biomass_data.rename(columns={biomass_col: "commercial_biomass"}, inplace=True)
                        
                        # Merge with the result dataframe
                        if result_df.empty:
                            result_df = biomass_data.copy()
                        else:
                            result_df = result_df.merge(biomass_data, on="date", how="outer")
                
                # If we have data, sort it by date (newest first)
                if not result_df.empty:
                    result_df = result_df.sort_values("date", ascending=False)
                
                return result_df
            
            # Export Section
            st.subheader("Export Data")
            
            export_container = st.container()
            export_button = st.button("Prepare Site Data for Export")
            
            if export_button:
                with st.spinner("Preparing data for export..."):
                    export_data = get_site_data_for_export(selected_site)
                    if not export_data.empty:
                        # Format column names for better readability
                        export_data = export_data.rename(columns=data_processor.DISPLAY_NAMES)
                        create_export_section(export_data, export_container, prefix=f"{selected_site}_data")
                        st.success(f"Data for {selected_site} is ready for export.")
                    else:
                        st.warning(f"No data available for {selected_site}.")
            
            # PDF Report Export Section
            st.subheader("Export PDF Report")
            
            # Metric selection - only include metrics that are displayed on the webpage
            available_metrics = ["hard_coral", "fleshy_algae", "herbivore", 
                               "omnivore", "corallivore", "bleaching", "rubble"]
            
            # Display names for the metrics for friendly selection
            metric_display = {
                "hard_coral": "Hard Coral Cover",
                "fleshy_algae": "Fleshy Algae Cover",
                "herbivore": "Herbivore Density",
                "carnivore": "Carnivore Density",
                "omnivore": "Omnivore Density",
                "corallivore": "Corallivore Density",
                "bleaching": "Bleaching",
                "rubble": "Rubble"
            }
            
            # Include biomass by default
            st.markdown("Select charts to include in the PDF report:")
            
            # Biomass is a special option
            include_biomass = st.checkbox("Commercial Fish Biomass", value=True)
            
            # Create multiple columns for a more compact UI with 2 checkboxes per row
            col1, col2 = st.columns(2)
            
            # Create selected metrics dictionary
            selected_metrics = {}
            for i, metric in enumerate(available_metrics):
                # Alternate between columns
                col = col1 if i % 2 == 0 else col2
                selected_metrics[metric] = col.checkbox(metric_display[metric], value=True)
            
            # Filter selected metrics
            metrics_to_include = [m for m, selected in selected_metrics.items() if selected]
            
            # PDF export button
            pdf_report_button = st.button("Generate PDF Report")
            
            if pdf_report_button:
                with st.spinner("Generating PDF report with selected charts..."):
                    try:
                        # Generate PDF bytes
                        pdf_bytes = generate_site_report_pdf(
                            selected_site, 
                            data_processor, 
                            metrics=metrics_to_include,
                            include_biomass=include_biomass
                        )
                        
                        # Create timestamp for filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{selected_site}_report_{timestamp}.pdf"
                        
                        # Show download button
                        st.download_button(
                            label="Download PDF Report",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf",
                        )
                        
                        st.success(f"PDF report for {selected_site} generated successfully!")
                    except Exception as e:
                        st.error(f"Error generating PDF report: {str(e)}")
                        st.info("Try selecting fewer charts or checking console for error details.")
            
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
                "Compare rubble cover with:",
                ["No Comparison", "Compare with Site", "Compare with Average"],
                key="rubble_comparison"
            )

            rubble_compare_site = None
            rubble_compare_scope = None
            if rubble_comparison == "Compare with Site":
                compare_sites = [site for site in alphabetical_site_names if site != selected_site]
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
            st.header(TRANSLATIONS[st.session_state.language]['site_metrics'])

            # Configure Plotly chart settings with mobile optimizations
            plotly_config = {
                'responsive': True,
                'displayModeBar': 'hover',  # Only show on hover to save space
                'displaylogo': False,
                'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d'],
                'scrollZoom': False,  # Disable scroll zoom on mobile
                'doubleClick': 'reset'  # Double tap to reset view
            }
            
            # Add wrapper with mobile-responsive class
            st.markdown('<div class="mobile-responsive-charts">', unsafe_allow_html=True)

            # Add spacing before first chart
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Create a placeholder for the biomass chart with loading indicator
            biomass_chart_container = st.container()
            with biomass_chart_container:
                # Show title for chart
                st.subheader(f"Commercial Fish Biomass - {selected_site}")
                
                # Create a container for the skeleton chart that we can replace later
                biomass_skeleton_container = st.empty()
                
                # Display a skeleton chart while data is loading
                with biomass_skeleton_container:
                    # Create a loading placeholder for the biomass chart
                    create_loading_placeholder(
                        st, 
                        message="Loading biomass data...", 
                        height=400
                    )
                    
                    st.plotly_chart(
                        skeleton_chart(height=400, chart_type="line"),
                        use_container_width=True,
                        key='biomass_skeleton'
                    )
            
            # Get biomass data and comparison
            biomass_data = data_processor.get_biomass_data(selected_site)
            biomass_comparison_data = None
            biomass_comparison_labels = None
            
            if biomass_comparison == "Compare with Sites" and biomass_compare_sites:
                # Get data for multiple comparison sites
                comparison_data_list = []
                for site_name in biomass_compare_sites:
                    site_data = data_processor.get_biomass_data(site_name)
                    if not site_data.empty:
                        comparison_data_list.append(site_data)
                
                if comparison_data_list:
                    biomass_comparison_data = comparison_data_list
                    # Use custom labels if provided
                    if biomass_compare_labels:
                        biomass_comparison_labels = biomass_compare_labels
                    else:
                        biomass_comparison_labels = biomass_compare_sites
                        
            elif biomass_comparison == "Compare with Average":
                municipality = site_municipality if biomass_compare_scope == "Municipality Average" else None
                avg_data = data_processor.get_average_biomass_data(
                    exclude_site=selected_site,
                    municipality=municipality
                )
                if not avg_data.empty:
                    biomass_comparison_data = avg_data
                    label = f"{site_municipality} Average" if biomass_compare_scope == "Municipality Average" else "All Sites Average"
                    biomass_comparison_labels = [label]
                    
            # Create the time series chart with date range filtering and confidence interval
            biomass_fig, biomass_config = graph_generator.create_time_series(
                biomass_data,
                f"Commercial Fish Biomass - {selected_site}",
                "Biomass (kg/ha)",
                comparison_data=biomass_comparison_data,
                comparison_labels=biomass_comparison_labels,
                date_range=date_range,
                show_confidence_interval=show_confidence_interval  # Use the checkbox value
            )
            
            # Replace the placeholder with the actual chart
            # Clear the skeleton and display the actual chart
            biomass_skeleton_container.empty()
            
            with biomass_chart_container:
                # Display the actual chart
                st.plotly_chart(
                    biomass_fig, 
                    use_container_width=True, 
                    config=biomass_config, 
                    key='biomass_chart'
                )

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Create a placeholder for the coral cover chart with loading indicator
            coral_chart_container = st.container()
            with coral_chart_container:
                # Show title for chart
                st.subheader(f"Hard Coral Cover - {selected_site}")
                
                # Create a container for the skeleton chart that we can replace later
                coral_skeleton_container = st.empty()
                
                # Display a skeleton chart while data is loading
                with coral_skeleton_container:
                    # Create a loading placeholder for the coral cover chart
                    create_loading_placeholder(
                        st, 
                        message="Loading coral cover data...", 
                        height=400
                    )
                    
                    st.plotly_chart(
                        skeleton_chart(height=400, chart_type="line"),
                        use_container_width=True,
                        key='coral_skeleton'
                    )
            
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
                comparison_data=coral_comparison_data,
                date_range=date_range,
                show_confidence_interval=show_confidence_interval
            )
            
            # Replace the placeholder with the actual chart
            # Clear the skeleton and display the actual chart
            coral_skeleton_container.empty()
            
            with coral_chart_container:
                # Display the actual chart
                st.plotly_chart(
                    coral_fig, 
                    use_container_width=True, 
                    config=coral_config, 
                    key='coral_chart'
                )

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
                comparison_data=algae_comparison_data,
                date_range=date_range,
                show_confidence_interval=show_confidence_interval
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
                comparison_data=herbivore_comparison_data,
                date_range=date_range,
                show_confidence_interval=show_confidence_interval
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
                comparison_data=omnivore_comparison_data,
                date_range=date_range,
                show_confidence_interval=show_confidence_interval
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
                comparison_data=corallivore_comparison_data,
                date_range=date_range,
                show_confidence_interval=show_confidence_interval
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
                comparison_data=bleaching_comparison_data,
                date_range=date_range,
                show_confidence_interval=show_confidence_interval
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
                comparison_data=rubble_comparison_data,
                date_range=date_range,
                show_confidence_interval=show_confidence_interval
            )
            st.plotly_chart(rubble_fig, use_container_width=True, config=rubble_config, key='rubble_chart')
            
            # Close the mobile-responsive charts container
            st.markdown('</div>', unsafe_allow_html=True)