import streamlit as st
import time

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

# Hide anchor elements and this page from navigation
hide_anchors_and_page_js = """
<style>
/* Hide Streamlit's automatic header anchors */
.stMarkdown h1 .anchor-link,
.stMarkdown h2 .anchor-link,
.stMarkdown h3 .anchor-link,
.stMarkdown h4 .anchor-link,
.stMarkdown h5 .anchor-link,
.stMarkdown h6 .anchor-link,
h1 > a,
h2 > a, 
h3 > a,
h4 > a,
h5 > a,
h6 > a {
    display: none !important;
}
</style>
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

st.markdown(hide_anchors_and_page_js, unsafe_allow_html=True)

import os
import pandas as pd
from datetime import datetime, date
from utils.data_processor import DataProcessor
from utils.simple_graph_generator import SimpleGraphGenerator
from utils.translations import TRANSLATIONS
from utils.database import get_db
from utils.branding import display_logo, add_favicon, add_custom_loading_animation
from utils.export_utils import generate_site_report_pdf
from utils.ui_helpers import (
    loading_spinner, 
    skeleton_chart, 
    create_loading_placeholder, 
    load_css, 
    skeleton_text_placeholder
)

# Import navigation utilities
from utils.navigation import display_navigation

# Apply critical CSS directly in the page first
st.markdown("""
<style>
/* Critical styles for immediate display */
body {
    font-family: sans-serif;
    opacity: 1;
    transition: opacity 0.2s;
}
.site-card { 
    border: 1px solid #eee;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 15px;
    transition: transform 0.2s;
}
</style>
""", unsafe_allow_html=True)

# Then apply the main CSS styles
st.markdown(load_css(), unsafe_allow_html=True)

# Apply branding including custom loading animation
add_favicon()
add_custom_loading_animation()

# Initialize language in session state if not present
if 'language' not in st.session_state:
    st.session_state.language = "en"  # Default to English

# Language code mapping
LANGUAGE_DISPLAY = {
    "en": "English",
    "tl": "Tagalog",
    "ceb": "Cebuano"
}

# Initialize processors with optimized caching
@st.cache_resource(ttl=3600)  # Cache for 1 hour to reduce database connection overhead
def get_data_processor():
    """
    Get cached data processor and graph generator instances
    Uses a single database connection for both to reduce overhead
    """
    db = next(get_db())
    data_processor = DataProcessor(db)
    # Pass the same data processor to graph generator to avoid duplicate db connections
    return data_processor, SimpleGraphGenerator(data_processor)

# Get processors with performance logging
start_time = time.time()
data_processor, graph_generator = get_data_processor()
init_time = time.time() - start_time
if init_time > 0.5:  # Log if initialization is slow
    print(f"Data processor initialization took {init_time:.2f} seconds")

# Get all sites
sites = data_processor.get_sites()

# Create ordered groups by municipality
zamboanguita_sites = sorted([site.name for site in sites if site.municipality == "Zamboanguita"])
siaton_sites = sorted([site.name for site in sites if site.municipality == "Siaton"])
santa_catalina_sites = sorted([site.name for site in sites if site.municipality == "Santa Catalina"])

# Combine in desired order for display in sidebar
site_names = zamboanguita_sites + siaton_sites + santa_catalina_sites

# All comparison dropdowns now use the create_comparison_options function
# This provides municipality grouping with headers for all site comparison options




# Add favicon to the page
add_favicon()

# Sidebar for site selection and language
with st.sidebar:
    st.title(TRANSLATIONS[st.session_state.language]['settings'])
    
    # Language selection dropdown
    current_language_display = LANGUAGE_DISPLAY.get(st.session_state.language, "English")
    selected_language_display = st.selectbox(
        TRANSLATIONS[st.session_state.language]['lang_toggle'],
        list(LANGUAGE_DISPLAY.values()),
        index=list(LANGUAGE_DISPLAY.values()).index(current_language_display),
        key="language_selector"
    )
    
    # Check if language changed and update session state
    for code, name in LANGUAGE_DISPLAY.items():
        if name == selected_language_display and code != st.session_state.language:
            st.session_state.language = code
            st.rerun()

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
    
    # Helper function to create municipality-organized comparison options for multiselect
    def create_comparison_options(exclude_site=None):
        """
        Creates a list of options for multiselect dropdowns with municipality headers
        
        Args:
            exclude_site: Site to exclude from the options (usually the current selected site)
            
        Returns:
            List of options with municipality headers and indented site names
        """
        options = []
        
        # Add Zamboanguita sites
        zambo_sites = [site for site in zamboanguita_sites if site != exclude_site]
        if zambo_sites:
            options.append("Zamboanguita")  # Municipality header
            options.extend([f"  {site}" for site in zambo_sites])  # Indented sites
            
        # Add Siaton sites
        siaton_sites_filtered = [site for site in siaton_sites if site != exclude_site]
        if siaton_sites_filtered:
            options.append("Siaton")  # Municipality header
            options.extend([f"  {site}" for site in siaton_sites_filtered])  # Indented sites
            
        # Add Santa Catalina sites
        santa_sites = [site for site in santa_catalina_sites if site != exclude_site]
        if santa_sites:
            options.append("Santa Catalina")  # Municipality header
            options.extend([f"  {site}" for site in santa_sites])  # Indented sites
            
        return options
    
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

    # Initialize selected site from URL or session state
    url_site = st.query_params.get('site')
    
    # Store selected site in session state if not already there
    if 'selected_site_name' not in st.session_state or (url_site and url_site != st.session_state.get('selected_site_name')):
        st.session_state.selected_site_name = url_site if url_site in site_names else site_names[0] if site_names else None
    
    # Find the correct option in site_options that corresponds to the selected site
    default_index = 0
    if st.session_state.selected_site_name:
        # Find the option that contains this site name with leading spaces
        for i, opt in enumerate(site_options):
            if opt.strip() == st.session_state.selected_site_name:
                default_index = i
                break
    
    # Function to handle site selection change with debouncing
    def on_site_change():
        # Get the value from session state
        option = st.session_state.site_selector
        # Only process if it's a site (starts with spaces)
        if option.startswith("  "):
            site = option.strip()
            if site in site_names and site != st.session_state.get('selected_site_name'):
                # Update both session state and URL params
                st.session_state.selected_site_name = site
                st.query_params["site"] = site
                # Force a rerun to apply the change immediately but don't do this if we're already
                # showing the correct site (improves performance)
                st.rerun()
    
    # Create the dropdown with the correct default selection and callback
    selected_option = st.selectbox(
        TRANSLATIONS[st.session_state.language]['choose_site'],
        site_options,
        index=default_index,
        format_func=format_site_option,
        key="site_selector",
        on_change=on_site_change
    )
    
    # Extract actual site name (remove leading spaces if it's a site)
    selected_site = selected_option.strip() if selected_option.startswith("  ") else None
    
    # PDF Report Export Section with single-click download
    if selected_site:
        st.markdown("---")
        
        # Generate PDF and create download immediately
        try:
            # Make sure available_metrics is defined here
            available_metrics = ["hard_coral", "fleshy_algae", "herbivore", "carnivore",
                              "omnivore", "corallivore", "bleaching", "rubble"]
            
            # Generate PDF bytes with all metrics and biomass included
            pdf_bytes = generate_site_report_pdf(
                selected_site, 
                data_processor, 
                metrics=available_metrics,  # Include all metrics
                include_biomass=True        # Always include biomass
            )
            
            # Create timestamp for filename using same format as PDF content
            timestamp = datetime.now().strftime("%Y-%B-%d")
            filename = f"{selected_site}_report_{timestamp}.pdf"
            
            # Single download button - generates and downloads in one click
            st.download_button(
                label="Export PDF Report",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                key=f"export_pdf_{selected_site}",
                use_container_width=True,
                help="Click to generate and download comprehensive PDF report with all charts"
            )
            
        except Exception as e:
            import traceback
            print(f"PDF Generation Error: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            st.error(f"Error preparing PDF report: {str(e)}")
            st.info("Please check console for error details.")
    

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
            
            # Display the site image
            image_placeholder.empty()
            
            # Use the site's image_url if available, otherwise use a placeholder
            image_path = selected_site_obj.image_url if selected_site_obj.image_url else "https://via.placeholder.com/400x300"
            
            # Display image normally - will use CSS to hide fullscreen button
            st.image(image_path, use_container_width=True, 
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
            elif language_code == 'ceb':
                # Use dedicated Cebuano description, fallback to Filipino then English
                description = selected_site_obj.description_ceb or selected_site_obj.description_fil or selected_site_obj.description_en
            else:
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
            
            # Compact Analysis Options with small question marks
            st.markdown("**Analysis Options**")
            
            # Let Streamlit handle checkbox state natively - no session state needed
            
            # Error Bars with compact question mark
            col1, col2 = st.columns([6, 1])
            with col1:
                show_error_bars = st.checkbox(
                    "Error Bars (s.d.)",
                    key="error_bars_checkbox"
                )
            with col2:
                if st.button("?", key="error_bars_help", help="Click for explanation"):
                    st.session_state.show_error_bars_popup = True
            
            # Confidence Intervals with compact question mark
            col1, col2 = st.columns([6, 1])
            with col1:
                show_confidence_interval = st.checkbox(
                    "Confidence Intervals (95%)",
                    key="confidence_interval_checkbox"
                )
            with col2:
                if st.button("?", key="confidence_help", help="Click for explanation"):
                    st.session_state.show_confidence_popup = True
            
            # Straight Line Graphs with compact question mark
            col1, col2 = st.columns([6, 1])
            with col1:
                use_straight_lines = st.checkbox(
                    "Straight Line Graphs",
                    value=st.session_state.get('use_straight_lines', False),
                    key="straight_lines_checkbox"
                )
            with col2:
                if st.button("?", key="straight_lines_help", help="Click for explanation"):
                    st.session_state.show_straight_lines_popup = True
            
            # No session state updates needed - let Streamlit handle checkbox state natively
            
            # Helper function to handle mutual exclusivity for analysis options
            def get_analysis_options():
                actual_show_error_bars = show_error_bars
                actual_show_confidence_interval = show_confidence_interval
                if show_error_bars and show_confidence_interval:
                    # If both are selected, prioritize error bars
                    actual_show_confidence_interval = False
                return actual_show_error_bars, actual_show_confidence_interval
            
            # Clear popup flags - they should only be triggered by question mark buttons, not checkboxes
            if 'show_error_bars_popup' not in st.session_state:
                st.session_state.show_error_bars_popup = False
            if 'show_confidence_popup' not in st.session_state:
                st.session_state.show_confidence_popup = False  
            if 'show_straight_lines_popup' not in st.session_state:
                st.session_state.show_straight_lines_popup = False
            

            
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
            
            # Export Data section removed per user request
            # Will be rethought and reimplemented later
            
            # Metric selection - include all metrics displayed on the webpage (moved up, but kept for use with PDF generation)
            available_metrics = ["hard_coral", "fleshy_algae", "herbivore", "carnivore",
                               "omnivore", "corallivore", "bleaching", "rubble"]
            
            # Display names for the metrics for friendly selection (moved up, but kept for use with PDF generation)
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
            
            # PDF generation code moved to the sidebar content below
            
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
                calculated_min = pd.to_datetime(all_data['date'].min())
                calculated_max = pd.to_datetime(all_data['date'].max())
                # Ensure we always start from 2017 to include all historical data
                min_date = pd.to_datetime('2017-01-01')  # Always start from beginning
                max_date = calculated_max
                print(f"DEBUG: Calculated range {calculated_min} to {calculated_max}, using {min_date} to {max_date}")
            else:
                # Fallback dates if no data
                min_date = pd.to_datetime('2017-01-01')
                max_date = pd.to_datetime('2025-12-31')
                print(f"DEBUG: Using fallback date range from {min_date} to {max_date}")
            
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
                # Get options organized by municipality
                comparison_options = create_comparison_options(exclude_site=selected_site)
                
                # Define function to extract site names (filtering out headers)
                def extract_site_name(option):
                    if option.startswith("  "):
                        return option.strip()
                    return None
                
                biomass_compare_sites = st.multiselect(
                    "Select sites to compare biomass:",
                    options=comparison_options,
                    format_func=format_site_option,
                    key="biomass_compare_sites",
                    max_selections=5  # Limit to 5 sites for readability
                )
                
                # Filter out the header items to get just the site names
                biomass_compare_sites = [extract_site_name(site) for site in biomass_compare_sites if extract_site_name(site)]
                if biomass_compare_sites:
                    # Always group by municipality by default (helps organize datasets)
                    site_to_muni = {site.name: site.municipality for site in sites}
                    biomass_compare_labels = [f"{site} ({site_to_muni.get(site, 'Unknown')})" for site in biomass_compare_sites]
                        
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
                ["No Comparison", "Compare with Sites", "Compare with Average"],
                key="coral_comparison"
            )

            coral_compare_sites = None
            coral_compare_scope = None
            coral_compare_labels = None
            
            if coral_comparison == "Compare with Sites":
                # Get options organized by municipality
                comparison_options = create_comparison_options(exclude_site=selected_site)
                
                # Define function to extract site names (filtering out headers)
                def extract_site_name(option):
                    if option.startswith("  "):
                        return option.strip()
                    return None
                
                coral_compare_sites = st.multiselect(
                    "Select sites to compare coral cover:",
                    options=comparison_options,
                    format_func=format_site_option,
                    key="coral_compare_sites",
                    max_selections=5  # Limit to 5 sites for readability
                )
                
                # Filter out the header items to get just the site names
                coral_compare_sites = [extract_site_name(site) for site in coral_compare_sites if extract_site_name(site)]
                if coral_compare_sites:
                    # Always group by municipality by default (helps organize datasets)
                    site_to_muni = {site.name: site.municipality for site in sites}
                    coral_compare_labels = [f"{site} ({site_to_muni.get(site, 'Unknown')})" for site in coral_compare_sites]
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
                ["No Comparison", "Compare with Sites", "Compare with Average"],
                key="algae_comparison"
            )

            algae_compare_sites = None
            algae_compare_scope = None
            algae_compare_labels = None
            
            if algae_comparison == "Compare with Sites":
                # Get options organized by municipality
                comparison_options = create_comparison_options(exclude_site=selected_site)
                
                algae_compare_sites = st.multiselect(
                    "Select sites to compare fleshy algae:",
                    options=comparison_options,
                    format_func=format_site_option,
                    key="algae_compare_sites",
                    max_selections=5  # Limit to 5 sites for readability
                )
                
                # Filter out the header items to get just the site names
                algae_compare_sites = [option.strip() for option in algae_compare_sites if option.startswith("  ")]
                if algae_compare_sites:
                    # Always group by municipality by default (helps organize datasets)
                    site_to_muni = {site.name: site.municipality for site in sites}
                    algae_compare_labels = [f"{site} ({site_to_muni.get(site, 'Unknown')})" for site in algae_compare_sites]
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
                ["No Comparison", "Compare with Sites", "Compare with Average"],
                key="herbivore_comparison"
            )

            herbivore_compare_sites = None
            herbivore_compare_scope = None
            herbivore_compare_labels = None
            
            if herbivore_comparison == "Compare with Sites":
                # Get options organized by municipality
                comparison_options = create_comparison_options(exclude_site=selected_site)
                
                herbivore_compare_sites = st.multiselect(
                    "Select sites to compare herbivore density:",
                    options=comparison_options,
                    format_func=format_site_option,
                    key="herbivore_compare_sites",
                    max_selections=5  # Limit to 5 sites for readability
                )
                
                # Filter out the header items to get just the site names
                herbivore_compare_sites = [option.strip() for option in herbivore_compare_sites if option.startswith("  ")]
                if herbivore_compare_sites:
                    # Always group by municipality by default (helps organize datasets)
                    site_to_muni = {site.name: site.municipality for site in sites}
                    herbivore_compare_labels = [f"{site} ({site_to_muni.get(site, 'Unknown')})" for site in herbivore_compare_sites]
            elif herbivore_comparison == "Compare with Average":
                herbivore_compare_scope = st.selectbox(
                    "Select average scope:",
                    ["Municipality Average", "All Sites Average"],
                    key="herbivore_compare_scope"
                )
                
            # Carnivore comparison options
            st.subheader("Carnivore Density")
            carnivore_comparison = st.selectbox(
                "Compare carnivore density with:",
                ["No Comparison", "Compare with Sites", "Compare with Average"],
                key="carnivore_comparison"
            )

            carnivore_compare_sites = None
            carnivore_compare_scope = None
            carnivore_compare_labels = None
            
            if carnivore_comparison == "Compare with Sites":
                # Get options organized by municipality
                comparison_options = create_comparison_options(exclude_site=selected_site)
                
                carnivore_compare_sites = st.multiselect(
                    "Select sites to compare carnivore density:",
                    options=comparison_options,
                    format_func=format_site_option,
                    key="carnivore_compare_sites",
                    max_selections=5  # Limit to 5 sites for readability
                )
                
                # Filter out the header items to get just the site names
                carnivore_compare_sites = [option.strip() for option in carnivore_compare_sites if option.startswith("  ")]
                if carnivore_compare_sites:
                    # Always group by municipality by default (helps organize datasets)
                    site_to_muni = {site.name: site.municipality for site in sites}
                    carnivore_compare_labels = [f"{site} ({site_to_muni.get(site, 'Unknown')})" for site in carnivore_compare_sites]
            elif carnivore_comparison == "Compare with Average":
                carnivore_compare_scope = st.selectbox(
                    "Select average scope:",
                    ["Municipality Average", "All Sites Average"],
                    key="carnivore_compare_scope"
                )

            # Omnivore comparison options
            st.subheader("Omnivore Density")
            omnivore_comparison = st.selectbox(
                "Compare omnivore density with:",
                ["No Comparison", "Compare with Sites", "Compare with Average"],
                key="omnivore_comparison"
            )

            omnivore_compare_sites = None
            omnivore_compare_scope = None
            omnivore_compare_labels = None
            
            if omnivore_comparison == "Compare with Sites":
                # Get options organized by municipality
                comparison_options = create_comparison_options(exclude_site=selected_site)
                
                omnivore_compare_sites = st.multiselect(
                    "Select sites to compare omnivore density:",
                    options=comparison_options,
                    format_func=format_site_option,
                    key="omnivore_compare_sites",
                    max_selections=5  # Limit to 5 sites for readability
                )
                
                # Filter out the header items to get just the site names
                omnivore_compare_sites = [option.strip() for option in omnivore_compare_sites if option.startswith("  ")]
                if omnivore_compare_sites:
                    # Always group by municipality by default (helps organize datasets)
                    site_to_muni = {site.name: site.municipality for site in sites}
                    omnivore_compare_labels = [f"{site} ({site_to_muni.get(site, 'Unknown')})" for site in omnivore_compare_sites]
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
                ["No Comparison", "Compare with Sites", "Compare with Average"],
                key="corallivore_comparison"
            )

            corallivore_compare_sites = None
            corallivore_compare_scope = None
            corallivore_compare_labels = None
            
            if corallivore_comparison == "Compare with Sites":
                # Get options organized by municipality
                comparison_options = create_comparison_options(exclude_site=selected_site)
                
                corallivore_compare_sites = st.multiselect(
                    "Select sites to compare corallivore density:",
                    options=comparison_options,
                    format_func=format_site_option,
                    key="corallivore_compare_sites",
                    max_selections=5  # Limit to 5 sites for readability
                )
                
                # Filter out the header items to get just the site names
                corallivore_compare_sites = [option.strip() for option in corallivore_compare_sites if option.startswith("  ")]
                if corallivore_compare_sites:
                    # Always group by municipality by default (helps organize datasets)
                    site_to_muni = {site.name: site.municipality for site in sites}
                    corallivore_compare_labels = [f"{site} ({site_to_muni.get(site, 'Unknown')})" for site in corallivore_compare_sites]
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
                ["No Comparison", "Compare with Sites", "Compare with Average"],
                key="bleaching_comparison"
            )

            bleaching_compare_sites = None
            bleaching_compare_scope = None
            bleaching_compare_labels = None
            
            if bleaching_comparison == "Compare with Sites":
                # Get options organized by municipality
                comparison_options = create_comparison_options(exclude_site=selected_site)
                
                bleaching_compare_sites = st.multiselect(
                    "Select sites to compare bleaching:",
                    options=comparison_options,
                    format_func=format_site_option,
                    key="bleaching_compare_sites",
                    max_selections=5  # Limit to 5 sites for readability
                )
                
                # Filter out the header items to get just the site names
                bleaching_compare_sites = [option.strip() for option in bleaching_compare_sites if option.startswith("  ")]
                if bleaching_compare_sites:
                    # Always group by municipality by default (helps organize datasets)
                    site_to_muni = {site.name: site.municipality for site in sites}
                    bleaching_compare_labels = [f"{site} ({site_to_muni.get(site, 'Unknown')})" for site in bleaching_compare_sites]
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
                ["No Comparison", "Compare with Sites", "Compare with Average"],
                key="rubble_comparison"
            )

            rubble_compare_sites = None
            rubble_compare_scope = None
            rubble_compare_labels = None
            
            if rubble_comparison == "Compare with Sites":
                # Get options organized by municipality
                comparison_options = create_comparison_options(exclude_site=selected_site)
                
                rubble_compare_sites = st.multiselect(
                    "Select sites to compare rubble cover:",
                    options=comparison_options,
                    format_func=format_site_option,
                    key="rubble_compare_sites",
                    max_selections=5  # Limit to 5 sites for readability
                )
                
                # Filter out the header items to get just the site names
                rubble_compare_sites = [option.strip() for option in rubble_compare_sites if option.startswith("  ")]
                if rubble_compare_sites:
                    # Always group by municipality by default (helps organize datasets)
                    site_to_muni = {site.name: site.municipality for site in sites}
                    rubble_compare_labels = [f"{site} ({site_to_muni.get(site, 'Unknown')})" for site in rubble_compare_sites]
            elif rubble_comparison == "Compare with Average":
                rubble_compare_scope = st.selectbox(
                    "Select average scope:",
                    ["Municipality Average", "All Sites Average"],
                    key="rubble_compare_scope"
                )

        # Streamlit native modals for explanations
        @st.dialog("Error Bars (Standard Deviation)")
        def show_error_bars_dialog():
            st.write("Error bars show the standard deviation of the data points around the mean value. They indicate the variability or spread of the data:")
            st.write("• **Shorter bars:** Data points are close together (low variability)")
            st.write("• **Longer bars:** Data points are spread out (high variability)")
            st.write("• **Interpretation:** About 68% of data points fall within 1 standard deviation")
            st.info("Note: Error bars and confidence intervals are mutually exclusive options.")

        @st.dialog("Confidence Intervals (95%)")
        def show_confidence_dialog():
            st.write("Confidence intervals show the range where we can be 95% confident that the true population mean lies:")
            st.write("• **Narrow bands:** More precise estimates (larger sample sizes)")
            st.write("• **Wide bands:** Less precise estimates (smaller sample sizes)")
            st.write("• **Interpretation:** If we repeated the study 100 times, 95 of those intervals would contain the true mean")
            st.info("Note: Confidence intervals and error bars are mutually exclusive options.")

        @st.dialog("Straight Line Graphs")
        def show_straight_lines_dialog():
            st.write("Toggle between straight lines and smooth curves for trend visualization:")
            st.write("• **Straight lines:** Direct point-to-point connections showing exact data progression")
            st.write("• **Smooth curves (default):** Rounded spline curves that emphasize overall trends")
            st.write("• **Use straight lines when:** You want to see precise data changes between time periods")
            st.write("• **Use smooth curves when:** You want to focus on general trend patterns")

        # Show only one dialog at a time based on session state
        if st.session_state.get('show_error_bars_popup', False):
            show_error_bars_dialog()
            # Clear the popup flag after showing dialog
            st.session_state.show_error_bars_popup = False
        elif st.session_state.get('show_confidence_popup', False):
            show_confidence_dialog()
            # Clear the popup flag after showing dialog
            st.session_state.show_confidence_popup = False
        elif st.session_state.get('show_straight_lines_popup', False):
            show_straight_lines_dialog()
            # Clear the popup flag after showing dialog
            st.session_state.show_straight_lines_popup = False

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

            # Commercial Fish Biomass Chart (title will be on chart)
            
            with st.spinner("Loading biomass data..."):
                # Get biomass data and comparison
                biomass_data = data_processor.get_biomass_data(selected_site)
                biomass_comparison_data = None
                biomass_comparison_labels = None
                
                if biomass_comparison == "Compare with Sites" and biomass_compare_sites:
                    # Use batch loading for better performance
                    site_data_dict = data_processor.batch_get_biomass_data(biomass_compare_sites, start_date='2017-01-01')
                    
                    # Convert to the format expected by the graph generator
                    comparison_data_list = []
                    actual_comparison_labels = []
                    
                    for site_name in biomass_compare_sites:
                        if site_name in site_data_dict and not site_data_dict[site_name].empty:
                            comparison_data_list.append(site_data_dict[site_name])
                            # Use custom labels if provided, otherwise use site name
                            if biomass_compare_labels and len(biomass_compare_labels) > len(actual_comparison_labels):
                                actual_comparison_labels.append(biomass_compare_labels[len(actual_comparison_labels)])
                            else:
                                actual_comparison_labels.append(site_name)
                    
                    if comparison_data_list:
                        biomass_comparison_data = comparison_data_list
                        biomass_comparison_labels = actual_comparison_labels
                            
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
                        
                # Get analysis options with mutual exclusivity
                actual_show_error_bars, actual_show_confidence_interval = get_analysis_options()

                # Create the time series chart with date range filtering and analysis options
                biomass_fig, biomass_config = graph_generator.create_time_series(
                    biomass_data,
                    f"Commercial Fish Biomass - {selected_site}",  # Title on chart
                    "Biomass (kg/ha)",
                    comparison_data=biomass_comparison_data,
                    comparison_labels=biomass_comparison_labels,
                    date_range=date_range,
                    show_confidence_interval=actual_show_confidence_interval,
                    show_error_bars=actual_show_error_bars,
                    use_straight_lines=use_straight_lines
                )
                
                # Display the chart
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
            coral_comparison_labels = None
            
            if coral_comparison == "Compare with Sites" and coral_compare_sites:
                # Use batch loading for better performance
                site_data_dict = data_processor.batch_get_coral_cover_data(coral_compare_sites, start_date='2017-01-01')
                
                # Convert to the format expected by the graph generator
                comparison_data_list = [df for site, df in site_data_dict.items() if not df.empty]
                
                if comparison_data_list:
                    coral_comparison_data = comparison_data_list
                    # Use custom labels if provided
                    if coral_compare_labels:
                        coral_comparison_labels = coral_compare_labels
                    else:
                        coral_comparison_labels = coral_compare_sites
            elif coral_comparison == "Compare with Average":
                municipality = site_municipality if coral_compare_scope == "Municipality Average" else None
                coral_comparison_data = data_processor.get_average_metric_data(
                    'hard_coral',
                    exclude_site=selected_site,
                    municipality=municipality
                )
                if not coral_comparison_data.empty:
                    label = f"{site_municipality} Average" if coral_compare_scope == "Municipality Average" else "All Sites Average"
                    coral_comparison_labels = [label]
            # Get analysis options with mutual exclusivity
            actual_show_error_bars, actual_show_confidence_interval = get_analysis_options()

            coral_fig, coral_config = graph_generator.create_time_series(
                coral_data,
                f"Hard Coral Cover - {selected_site}",  # Title on chart
                "Cover (%)",
                comparison_data=coral_comparison_data,
                comparison_labels=coral_comparison_labels,
                date_range=date_range,
                show_confidence_interval=actual_show_confidence_interval,
                show_error_bars=actual_show_error_bars,
                use_straight_lines=use_straight_lines
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
            algae_comparison_labels = None
            
            if algae_comparison == "Compare with Sites" and algae_compare_sites:
                # Use batch loading for better performance
                site_data_dict = data_processor.batch_get_metric_data(algae_compare_sites, 'fleshy_algae', start_date='2017-01-01')
                
                # Convert to the format expected by the graph generator
                comparison_data_list = [df for site, df in site_data_dict.items() if not df.empty]
                
                if comparison_data_list:
                    algae_comparison_data = comparison_data_list
                    # Use custom labels if provided
                    if algae_compare_labels:
                        algae_comparison_labels = algae_compare_labels
                    else:
                        algae_comparison_labels = algae_compare_sites
            elif algae_comparison == "Compare with Average":
                municipality = site_municipality if algae_compare_scope == "Municipality Average" else None
                algae_comparison_data = data_processor.get_average_metric_data(
                    'fleshy_algae',
                    exclude_site=selected_site,
                    municipality=municipality
                )
                if not algae_comparison_data.empty:
                    label = f"{site_municipality} Average" if algae_compare_scope == "Municipality Average" else "All Sites Average"
                    algae_comparison_labels = [label]
            # Get analysis options with mutual exclusivity
            actual_show_error_bars, actual_show_confidence_interval = get_analysis_options()

            algae_fig, algae_config = graph_generator.create_time_series(
                algae_data,
                f"Fleshy Algae Cover - {selected_site}",
                "Cover (%)",
                comparison_data=algae_comparison_data,
                comparison_labels=algae_comparison_labels,
                date_range=date_range,
                show_confidence_interval=actual_show_confidence_interval,
                show_error_bars=actual_show_error_bars,
                use_straight_lines=use_straight_lines
            )
            st.plotly_chart(algae_fig, use_container_width=True, config=algae_config, key='algae_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Get herbivore data and comparison
            herbivore_data = data_processor.get_metric_data(selected_site, 'herbivore')
            herbivore_comparison_data = None
            herbivore_comparison_labels = None
            
            if herbivore_comparison == "Compare with Sites" and herbivore_compare_sites:
                # Use batch loading for better performance
                site_data_dict = data_processor.batch_get_metric_data(herbivore_compare_sites, 'herbivore', start_date='2017-01-01')
                
                # Convert to the format expected by the graph generator
                comparison_data_list = [df for site, df in site_data_dict.items() if not df.empty]
                
                if comparison_data_list:
                    herbivore_comparison_data = comparison_data_list
                    # Use custom labels if provided
                    if herbivore_compare_labels:
                        herbivore_comparison_labels = herbivore_compare_labels
                    else:
                        herbivore_comparison_labels = herbivore_compare_sites
            elif herbivore_comparison == "Compare with Average":
                municipality = site_municipality if herbivore_compare_scope == "Municipality Average" else None
                herbivore_comparison_data = data_processor.get_average_metric_data(
                    'herbivore',
                    exclude_site=selected_site,
                    municipality=municipality
                )
                if not herbivore_comparison_data.empty:
                    label = f"{site_municipality} Average" if herbivore_compare_scope == "Municipality Average" else "All Sites Average"
                    herbivore_comparison_labels = [label]
            # Get analysis options with mutual exclusivity
            actual_show_error_bars, actual_show_confidence_interval = get_analysis_options()

            herbivore_fig, herbivore_config = graph_generator.create_time_series(
                herbivore_data,
                f"Herbivore Density - {selected_site}",
                "Density (ind/ha)",
                comparison_data=herbivore_comparison_data,
                comparison_labels=herbivore_comparison_labels,
                date_range=date_range,
                show_confidence_interval=actual_show_confidence_interval,
                show_error_bars=actual_show_error_bars,
                use_straight_lines=use_straight_lines
            )
            st.plotly_chart(herbivore_fig, use_container_width=True, config=herbivore_config, key='herbivore_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)
            
            # Get carnivore data and comparison
            carnivore_data = data_processor.get_metric_data(selected_site, 'carnivore')
            carnivore_comparison_data = None
            carnivore_comparison_labels = None
            
            if carnivore_comparison == "Compare with Sites" and carnivore_compare_sites:
                # Use batch loading for better performance
                site_data_dict = data_processor.batch_get_metric_data(carnivore_compare_sites, 'carnivore', start_date='2017-01-01')
                
                # Convert to the format expected by the graph generator
                comparison_data_list = [df for site, df in site_data_dict.items() if not df.empty]
                
                if comparison_data_list:
                    carnivore_comparison_data = comparison_data_list
                    # Use custom labels if provided
                    if carnivore_compare_labels:
                        carnivore_comparison_labels = carnivore_compare_labels
                    else:
                        carnivore_comparison_labels = carnivore_compare_sites
            elif carnivore_comparison == "Compare with Average":
                municipality = site_municipality if carnivore_compare_scope == "Municipality Average" else None
                carnivore_comparison_data = data_processor.get_average_metric_data(
                    'carnivore',
                    exclude_site=selected_site,
                    municipality=municipality
                )
                if not carnivore_comparison_data.empty:
                    label = f"{site_municipality} Average" if carnivore_compare_scope == "Municipality Average" else "All Sites Average"
                    carnivore_comparison_labels = [label]
            # Get analysis options with mutual exclusivity
            actual_show_error_bars, actual_show_confidence_interval = get_analysis_options()

            carnivore_fig, carnivore_config = graph_generator.create_time_series(
                carnivore_data,
                f"Carnivore Density - {selected_site}",
                "Density (ind/ha)",
                comparison_data=carnivore_comparison_data,
                comparison_labels=carnivore_comparison_labels,
                date_range=date_range,
                show_confidence_interval=actual_show_confidence_interval,
                show_error_bars=actual_show_error_bars,
                use_straight_lines=use_straight_lines
            )
            st.plotly_chart(carnivore_fig, use_container_width=True, config=carnivore_config, key='carnivore_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Get omnivore data and comparison
            omnivore_data = data_processor.get_metric_data(selected_site, 'omnivore')
            omnivore_comparison_data = None
            omnivore_comparison_labels = None
            
            if omnivore_comparison == "Compare with Sites" and omnivore_compare_sites:
                # Use batch loading for better performance
                site_data_dict = data_processor.batch_get_metric_data(omnivore_compare_sites, 'omnivore', start_date='2017-01-01')
                
                # Convert to the format expected by the graph generator
                comparison_data_list = [df for site, df in site_data_dict.items() if not df.empty]
                
                if comparison_data_list:
                    omnivore_comparison_data = comparison_data_list
                    # Use custom labels if provided
                    if omnivore_compare_labels:
                        omnivore_comparison_labels = omnivore_compare_labels
                    else:
                        omnivore_comparison_labels = omnivore_compare_sites
            elif omnivore_comparison == "Compare with Average":
                municipality = site_municipality if omnivore_compare_scope == "Municipality Average" else None
                omnivore_comparison_data = data_processor.get_average_metric_data(
                    'omnivore',
                    exclude_site=selected_site,
                    municipality=municipality
                )
                if not omnivore_comparison_data.empty:
                    label = f"{site_municipality} Average" if omnivore_compare_scope == "Municipality Average" else "All Sites Average"
                    omnivore_comparison_labels = [label]
            # Get analysis options with mutual exclusivity
            actual_show_error_bars, actual_show_confidence_interval = get_analysis_options()

            omnivore_fig, omnivore_config = graph_generator.create_time_series(
                omnivore_data,
                f"Omnivore Density - {selected_site}",
                "Density (ind/ha)",
                comparison_data=omnivore_comparison_data,
                comparison_labels=omnivore_comparison_labels,
                date_range=date_range,
                show_confidence_interval=actual_show_confidence_interval,
                show_error_bars=actual_show_error_bars,
                use_straight_lines=use_straight_lines
            )
            st.plotly_chart(omnivore_fig, use_container_width=True, config=omnivore_config, key='omnivore_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Get corallivore data and comparison
            corallivore_data = data_processor.get_metric_data(selected_site, 'corallivore')
            corallivore_comparison_data = None
            corallivore_comparison_labels = None
            
            if corallivore_comparison == "Compare with Sites" and corallivore_compare_sites:
                # Use batch loading for better performance
                site_data_dict = data_processor.batch_get_metric_data(corallivore_compare_sites, 'corallivore', start_date='2017-01-01')
                
                # Convert to the format expected by the graph generator
                comparison_data_list = [df for site, df in site_data_dict.items() if not df.empty]
                
                if comparison_data_list:
                    corallivore_comparison_data = comparison_data_list
                    # Use custom labels if provided
                    if corallivore_compare_labels:
                        corallivore_comparison_labels = corallivore_compare_labels
                    else:
                        corallivore_comparison_labels = corallivore_compare_sites
            elif corallivore_comparison == "Compare with Average":
                municipality = site_municipality if corallivore_compare_scope == "Municipality Average" else None
                corallivore_comparison_data = data_processor.get_average_metric_data(
                    'corallivore',
                    exclude_site=selected_site,
                    municipality=municipality
                )
                if not corallivore_comparison_data.empty:
                    label = f"{site_municipality} Average" if corallivore_compare_scope == "Municipality Average" else "All Sites Average"
                    corallivore_comparison_labels = [label]
            # Get analysis options with mutual exclusivity
            actual_show_error_bars, actual_show_confidence_interval = get_analysis_options()

            corallivore_fig, corallivore_config = graph_generator.create_time_series(
                corallivore_data,
                f"Corallivore Density - {selected_site}",
                "Density (ind/ha)",
                comparison_data=corallivore_comparison_data,
                comparison_labels=corallivore_comparison_labels,
                date_range=date_range,
                show_confidence_interval=actual_show_confidence_interval,
                show_error_bars=actual_show_error_bars,
                use_straight_lines=use_straight_lines
            )
            st.plotly_chart(corallivore_fig, use_container_width=True, config=corallivore_config, key='corallivore_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Add bleaching visualization
            bleaching_data = data_processor.get_metric_data(selected_site, 'bleaching')
            bleaching_comparison_data = None
            bleaching_comparison_labels = None
            
            if bleaching_comparison == "Compare with Sites" and bleaching_compare_sites:
                # Use batch loading for better performance
                site_data_dict = data_processor.batch_get_metric_data(bleaching_compare_sites, 'bleaching', start_date='2017-01-01')
                
                # Convert to the format expected by the graph generator
                comparison_data_list = [df for site, df in site_data_dict.items() if not df.empty]
                
                if comparison_data_list:
                    bleaching_comparison_data = comparison_data_list
                    # Use custom labels if provided
                    if bleaching_compare_labels:
                        bleaching_comparison_labels = bleaching_compare_labels
                    else:
                        bleaching_comparison_labels = bleaching_compare_sites
            elif bleaching_comparison == "Compare with Average":
                municipality = site_municipality if bleaching_compare_scope == "Municipality Average" else None
                bleaching_comparison_data = data_processor.get_average_metric_data(
                    'bleaching',
                    exclude_site=selected_site,
                    municipality=municipality
                )
                if not bleaching_comparison_data.empty:
                    label = f"{site_municipality} Average" if bleaching_compare_scope == "Municipality Average" else "All Sites Average"
                    bleaching_comparison_labels = [label]
            # Get analysis options with mutual exclusivity
            actual_show_error_bars, actual_show_confidence_interval = get_analysis_options()

            bleaching_fig, bleaching_config = graph_generator.create_time_series(
                bleaching_data,
                f"Bleaching - {selected_site}",
                "Bleaching (%)",
                comparison_data=bleaching_comparison_data,
                comparison_labels=bleaching_comparison_labels,
                date_range=date_range,
                show_confidence_interval=actual_show_confidence_interval,
                show_error_bars=actual_show_error_bars,
                use_straight_lines=use_straight_lines
            )
            st.plotly_chart(bleaching_fig, use_container_width=True, config=bleaching_config, key='bleaching_chart')

            # Add spacing between charts
            st.markdown("<div style='margin-top: 2em;'></div>", unsafe_allow_html=True)

            # Add rubble visualization
            rubble_data = data_processor.get_metric_data(selected_site, 'rubble')
            rubble_comparison_data = None
            rubble_comparison_labels = None
            
            if rubble_comparison == "Compare with Sites" and rubble_compare_sites:
                # Use batch loading for better performance
                site_data_dict = data_processor.batch_get_metric_data(rubble_compare_sites, 'rubble', start_date='2017-01-01')
                
                # Convert to the format expected by the graph generator
                comparison_data_list = [df for site, df in site_data_dict.items() if not df.empty]
                
                if comparison_data_list:
                    rubble_comparison_data = comparison_data_list
                    # Use custom labels if provided
                    if rubble_compare_labels:
                        rubble_comparison_labels = rubble_compare_labels
                    else:
                        rubble_comparison_labels = rubble_compare_sites
            elif rubble_comparison == "Compare with Average":
                municipality = site_municipality if rubble_compare_scope == "Municipality Average" else None
                rubble_comparison_data = data_processor.get_average_metric_data(
                    'rubble',
                    exclude_site=selected_site,
                    municipality=municipality
                )
                if not rubble_comparison_data.empty:
                    label = f"{site_municipality} Average" if rubble_compare_scope == "Municipality Average" else "All Sites Average"
                    rubble_comparison_labels = [label]
            # Get analysis options with mutual exclusivity
            actual_show_error_bars, actual_show_confidence_interval = get_analysis_options()

            rubble_fig, rubble_config = graph_generator.create_time_series(
                rubble_data,
                f"Rubble Cover - {selected_site}",
                "Rubble Cover (%)",
                comparison_data=rubble_comparison_data,
                comparison_labels=rubble_comparison_labels,
                date_range=date_range,
                show_confidence_interval=actual_show_confidence_interval,
                show_error_bars=actual_show_error_bars,
                use_straight_lines=use_straight_lines
            )
            st.plotly_chart(rubble_fig, use_container_width=True, config=rubble_config, key='rubble_chart')
            
            # Close the mobile-responsive charts container
            st.markdown('</div>', unsafe_allow_html=True)