import streamlit as st
import os
import time
from utils.data_processor import DataProcessor
from utils.database import get_db
from utils.translations import TRANSLATIONS
from utils.branding import display_logo, add_favicon, add_custom_loading_animation

# Page configuration
st.set_page_config(
    page_title="Marine Conservation Philippines",
    page_icon="assets/branding/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply critical CSS directly in the page
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
    height: 340px;  /* Fixed height for uniform cards */
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.site-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}
.site-card-content {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
}
.site-card-footer {
    margin-top: auto;
}
</style>
""", unsafe_allow_html=True)

# Import and apply the main CSS after the critical styles
from utils.ui_helpers import load_css
st.markdown(load_css(), unsafe_allow_html=True)

# Simple CSS to hide anchor elements - Streamlit native approach
st.markdown("""
<style>
/* Hide only Streamlit's automatic header anchors, not custom site card links */
.stMarkdown h1 .anchor-link,
.stMarkdown h2 .anchor-link,
.stMarkdown h3 .anchor-link,
.stMarkdown h4 .anchor-link,
.stMarkdown h5 .anchor-link,
.stMarkdown h6 .anchor-link {
    display: none !important;
}

/* Hide header anchors only when they are NOT inside site cards */
.stMarkdown h1 > a:not(.site-card a),
.stMarkdown h2 > a:not(.site-card a), 
.stMarkdown h3 > a:not(.site-card a),
.stMarkdown h4 > a:not(.site-card a),
.stMarkdown h5 > a:not(.site-card a),
.stMarkdown h6 > a:not(.site-card a) {
    display: none !important;
}

/* Ensure site card buttons and links are visible and functional */
.site-card a,
.site-card button,
.site-button {
    display: inline-block !important;
    visibility: visible !important;
    opacity: 1 !important;
}
</style>
""", unsafe_allow_html=True)

# Add JavaScript for navigation fix only
fix_nav_js = """
<script>
document.addEventListener('DOMContentLoaded', function() {
  function fixNavigation() {
    const navElement = document.querySelector('[data-testid="stSidebarNav"]');
    if (navElement) {
      console.log('Navigation element found');
      const links = navElement.querySelectorAll('li');
      console.log('Found', links.length, 'navigation links');
      
      // Make sure all links are visible
      links.forEach((link, index) => {
        console.log(`Link ${index} current display:`, window.getComputedStyle(link).display);
        link.style.display = 'block';
        link.style.visibility = 'visible';
        link.style.opacity = '1';
        link.style.height = 'auto';
        link.style.width = 'auto';
        console.log(`Link ${index} after fix:`, window.getComputedStyle(link).display);
      });
    } else {
      console.log('Navigation element not found yet, retrying...');
      setTimeout(fixNavigation, 1000);
    }
  }
  
  // Initial call with delay to ensure Streamlit is loaded
  setTimeout(fixNavigation, 1000);
  
  // Continue checking periodically (in case of dynamic changes)
  setInterval(fixNavigation, 5000);
});
</script>
"""
st.markdown(fix_nav_js, unsafe_allow_html=True)

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

# Import navigation helper
from utils.navigation import display_navigation

# Sidebar for language selection and navigation
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
            
    # Add site description based on selected language
    st.title(TRANSLATIONS[st.session_state.language]['about'])
    
    # Display about text from translations
    st.markdown(TRANSLATIONS[st.session_state.language]['about_text'])

# Use session state language for content
language_code = st.session_state.language

# Header
subheader_text = TRANSLATIONS[language_code]['dashboard']

# Add some padding at the top
st.markdown("<div style='padding-top: 20px;'></div>", unsafe_allow_html=True)

# Add favicon to the page
add_favicon()

# Add custom loading animation
add_custom_loading_animation()

# Display the logo using our branding utility
display_logo(size="medium")

# Display the site header
st.markdown(f"""
    <div class="site-header">
        <h2>{subheader_text}</h2>
    </div>
""", unsafe_allow_html=True)



# Initialize database connection with improved session management
@st.cache_resource(ttl=60)  # Reduced cache to 1 minute to pick up database changes
def get_processor():
    """
    Get a cached data processor instance with a managed database session
    This helps improve performance by reusing the database connection
    while also ensuring the connection is periodically refreshed
    """
    db = next(get_db())
    processor = DataProcessor(db)
    return processor

# Get data processor with performance logging
start_time = time.time()
data_processor = get_processor()
processing_time = time.time() - start_time

# Get all sites with performance tracking
start_time = time.time()
sites = data_processor.get_sites()
site_load_time = time.time() - start_time
if site_load_time > 0.5:  # Only log if it's slow
    print(f"Site data loading took {site_load_time:.2f} seconds")

# Import from ui_helpers
from utils.ui_helpers import skeleton_text_placeholder

# Efficiently group sites by municipality
municipalities = {}
for site in sites:
    if site.municipality not in municipalities:
        municipalities[site.municipality] = []
    municipalities[site.municipality].append(site)

# Sort each group
for muni in municipalities:
    municipalities[muni] = sorted(municipalities[muni], key=lambda x: x.name)

# Function to create site card with translations
def create_site_card(site):
    # Get description based on language
    if language_code == 'en':
        description = site.description_en
    elif language_code == 'tl':
        description = site.description_fil  # Using Filipino description for Tagalog
    elif language_code == 'ceb':
        # Use dedicated Cebuano description, fallback to Filipino then English
        description = site.description_ceb or site.description_fil or site.description_en
    else:
        description = site.description_en
        
    # Default description if not available
    description = description or TRANSLATIONS[language_code]['site_desc_placeholder']
    
    # Truncate description to exactly 140 characters for uniform height
    truncated_description = description[:140] + "..." if len(description) > 140 else description
    
    # Get translations for labels
    municipality_label = TRANSLATIONS[language_code]['municipality']
    view_details_text = TRANSLATIONS[language_code]['view_details']

    st.markdown(f"""
        <div class="site-card">
            <div class="site-card-content">
                <h3 style="margin-top: 0; color: #2c3e50;">{site.name}</h3>
                <p style="margin: 8px 0; color: #666;"><strong>{municipality_label}:</strong> {site.municipality}</p>
                <p style="margin: 12px 0; line-height: 1.4; color: #333; flex-grow: 1;">{truncated_description}</p>
            </div>
            <div class="site-card-footer" style="margin-top: auto; padding-top: 15px;">
                <a href="Site_Dashboard?site={site.name}" target="_self" style="text-decoration: none;">
                    <button class="site-button" style="
                        background: #4CAF50; 
                        color: white; 
                        border: none; 
                        padding: 10px 20px; 
                        border-radius: 5px; 
                        cursor: pointer; 
                        width: 100%;
                        font-size: 14px;
                        transition: background 0.3s;
                    " onmouseover="this.style.background='#45a049'" onmouseout="this.style.background='#4CAF50'">
                        {view_details_text}
                    </button>
                </a>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Define municipality display names with translations
municipality_names = {
    "en": {
        "Zamboanguita": "Zamboanguita Sites",
        "Siaton": "Siaton Sites",
        "Santa Catalina": "Santa Catalina Sites"
    },
    "tl": {
        "Zamboanguita": "Mga Lugar sa Zamboanguita",
        "Siaton": "Mga Lugar sa Siaton",
        "Santa Catalina": "Mga Lugar sa Santa Catalina"
    },
    "ceb": {
        "Zamboanguita": "Mga Lugar sa Zamboanguita",
        "Siaton": "Mga Lugar sa Siaton",
        "Santa Catalina": "Mga Lugar sa Santa Catalina"
    }
}

# Define the order of municipalities for display
display_order = ["Zamboanguita", "Siaton", "Santa Catalina"]

# Performance improvement - render cards more efficiently
for municipality in display_order:
    if municipality in municipalities and municipalities[municipality]:
        with st.expander(municipality_names[language_code][municipality], expanded=True):
            # Create a grid layout for site cards
            cols = st.columns(3)
            for idx, site in enumerate(municipalities[municipality]):
                with cols[idx % 3]:
                    create_site_card(site)

# Clean up
db = next(get_db())
db.close()