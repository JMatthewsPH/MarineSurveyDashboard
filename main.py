import streamlit as st
import os
from utils.data_processor import DataProcessor
from utils.database import get_db
from utils.translations import TRANSLATIONS
from utils.branding import display_logo, add_favicon

# Page configuration
st.set_page_config(
    page_title="Marine Conservation Philippines",
    page_icon="assets/branding/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
@st.cache_data
def load_css():
    with open('assets/site_styles.css') as f:
        css_content = f.read()
        return f'<style>{css_content}</style>'

# Include CSS for loading states and skeleton UI
from utils.ui_helpers import add_loading_css

st.markdown(load_css(), unsafe_allow_html=True)
st.markdown(add_loading_css(), unsafe_allow_html=True)

# Add JavaScript to hide "main" text (hidden in an HTML comment to prevent display)
hide_main_js = """
<script type="text/javascript">
    (function() {
        function hideMainText() {
            var sidebarNavs = document.querySelectorAll('[data-testid="stSidebarNav"]');
            if (sidebarNavs.length > 0) {
                var navItems = sidebarNavs[0].querySelectorAll('li');
                if (navItems.length > 0) {
                    navItems[0].style.display = 'none';
                }
            }
            setTimeout(hideMainText, 500);
        }
        
        window.addEventListener('load', hideMainText);
        hideMainText();
    })();
</script>
"""

# Use a div with display:none to hide the JS code from being shown
st.markdown(f'<div style="display:none">{hide_main_js}</div>', unsafe_allow_html=True)

# Initialize language in session state if not present
if 'language' not in st.session_state:
    st.session_state.language = "en"  # Default to English

# Language code mapping
LANGUAGE_DISPLAY = {
    "en": "English",
    "tl": "Tagalog",
    "ceb": "Cebuano"
}

# Initialize theme in session state if not present
if 'theme' not in st.session_state:
    # Default to light mode at first
    st.session_state.theme = "light"

# Define theme toggle callback
def toggle_theme():
    # Toggle between light and dark with debug output
    current_theme = st.session_state.theme
    st.session_state.theme = "light" if current_theme == "dark" else "dark"
    st.write(f"Theme changed from {current_theme} to {st.session_state.theme}")
    # Force rerun to apply theme change immediately
    st.rerun()

# Use custom CSS to enforce theme
if st.session_state.theme == "dark":
    # Apply dark theme
    custom_css = """
    <style>
    /* Force dark theme */
    :root {
        --primary-color: #4299e1 !important;
        --secondary-color: #68d391 !important;
        --background-color: #1a202c !important;
        --text-color: #e2e8f0 !important;
        --border-color: #4a5568 !important;
        --hover-color: #63b3ed !important;
        --box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
        --hover-shadow: 0 4px 8px rgba(0,0,0,0.4) !important;
        --card-bg-color: #2d3748 !important;
        --grid-line-color: #4a5568 !important;
        --tooltip-bg-color: #4a5568 !important;
        --tooltip-text-color: #e2e8f0 !important;
        --chart-bg-color: #2d3748 !important;
        --chart-line-color: #63b3ed !important;
        --chart-text-color: #e2e8f0 !important;
    }
    
    /* Dark mode overrides */
    body, .main, .stApp {
        background-color: #1a202c !important;
        color: #e2e8f0 !important;
    }
    
    /* Target sidebar specifically with stronger selectors in dark mode */
    [data-testid="stSidebar"], 
    [data-testid="stSidebar"] > div:first-child,
    div[data-testid="stSidebarUserContent"],
    .css-6qob1r.e1fqkh3o3,
    .css-10oheav.e1fqkh3o4,
    section[data-testid="stSidebar"] {
        background-color: #1a202c !important;
        color: #e2e8f0 !important;
    }
    
    /* Target sidebar elements in dark mode */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div,
    div[data-testid="stMarkdownContainer"],
    div[data-baseweb="select"] {
        color: #e2e8f0 !important;
    }
    
    .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6 {
        color: #e2e8f0 !important;
    }
    
    .js-plotly-plot .plotly .gridlayer path {
        stroke: #4a5568 !important;
    }
    
    .js-plotly-plot .plotly .xaxis .zerolinelayer path,
    .js-plotly-plot .plotly .yaxis .zerolinelayer path {
        stroke: #4a5568 !important;
    }
    
    .js-plotly-plot .plotly .gtitle, 
    .js-plotly-plot .plotly .xtitle, 
    .js-plotly-plot .plotly .ytitle,
    .js-plotly-plot .plotly .xtick text, 
    .js-plotly-plot .plotly .ytick text {
        fill: #e2e8f0 !important;
    }
    
    .site-header, .site-card, .site-description {
        background-color: #2d3748 !important;
        border-color: #4a5568 !important;
    }
    </style>
    """
else:
    # Apply light theme explicitly with !important flags
    custom_css = """
    <style>
    /* Force light theme */
    :root {
        --primary-color: #2b6cb0 !important;
        --secondary-color: #48bb78 !important;
        --background-color: #f7fafc !important;
        --text-color: #2d3748 !important;
        --border-color: #e2e8f0 !important;
        --hover-color: #4299e1 !important;
        --box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        --hover-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
        --card-bg-color: white !important;
        --grid-line-color: #e0e0e0 !important;
        --tooltip-bg-color: white !important;
        --tooltip-text-color: #333 !important;
        --chart-bg-color: white !important;
        --chart-line-color: #2b6cb0 !important;
        --chart-text-color: #2d3748 !important;
    }
    
    /* Light mode overrides */
    body, .main, .stApp {
        background-color: #f7fafc !important;
        color: #2d3748 !important;
    }
    
    /* Target sidebar specifically with stronger selectors */
    [data-testid="stSidebar"], 
    [data-testid="stSidebar"] > div:first-child,
    div[data-testid="stSidebarUserContent"],
    .css-6qob1r.e1fqkh3o3,
    .css-10oheav.e1fqkh3o4 {
        background-color: #f7fafc !important;
        color: #2d3748 !important;
    }
    
    /* Target sidebar elements */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: #2d3748 !important;
    }
    
    .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6 {
        color: #2d3748 !important;
    }
    
    .js-plotly-plot .plotly .gridlayer path {
        stroke: #e0e0e0 !important;
    }
    
    .js-plotly-plot .plotly .xaxis .zerolinelayer path,
    .js-plotly-plot .plotly .yaxis .zerolinelayer path {
        stroke: #e2e8f0 !important;
    }
    
    .js-plotly-plot .plotly .gtitle, 
    .js-plotly-plot .plotly .xtitle, 
    .js-plotly-plot .plotly .ytitle,
    .js-plotly-plot .plotly .xtick text, 
    .js-plotly-plot .plotly .ytick text {
        fill: #2d3748 !important;
    }
    
    .site-header, .site-card, .site-description {
        background-color: white !important;
        border-color: #e2e8f0 !important;
    }
    </style>
    """

# Apply the theme CSS
st.markdown(custom_css, unsafe_allow_html=True)

# Sidebar for language selection
with st.sidebar:
    # Create a container for the theme toggle at the top of sidebar
    theme_container = st.container()
    
    with theme_container:
        # Add a theme toggle button using Streamlit's built-in components
        toggle_label = "Switch to Light Mode" if st.session_state.theme == "dark" else "Switch to Dark Mode"
        st.button(toggle_label, key="theme_toggle", on_click=toggle_theme)
    
    st.title(TRANSLATIONS[st.session_state.language]['settings'])
    
    # Update session state when language changes
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

    # Add site description based on selected language
    st.markdown("---")  # Add a visual separator
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

# Display the logo using our branding utility
display_logo(size="medium")

# Display the site header
st.markdown(f"""
    <div class="site-header">
        <h2>{subheader_text}</h2>
    </div>
""", unsafe_allow_html=True)



# Initialize database connection
@st.cache_resource
def get_processor():
    db = next(get_db())
    return DataProcessor(db)

data_processor = get_processor()

# Get all sites
sites = data_processor.get_sites()

# Create ordered groups by municipality
zamboanguita_sites = sorted(
    [site for site in sites if site.municipality == "Zamboanguita"],
    key=lambda x: x.name
)
siaton_sites = sorted(
    [site for site in sites if site.municipality == "Siaton"],
    key=lambda x: x.name
)
santa_catalina_sites = sorted(
    [site for site in sites if site.municipality == "Santa Catalina"],
    key=lambda x: x.name
)

# Function to create site card with translations
def create_site_card(site):
    # Get description based on language
    if language_code == 'en':
        description = site.description_en
    elif language_code == 'tl':
        description = site.description_fil  # Using Filipino description for Tagalog
    else:  # Cebuano - fallback to English for now
        description = site.description_en
        
    # Default description if not available
    description = description or TRANSLATIONS[language_code]['site_desc_placeholder']
    
    # Truncate description to 200 characters and add ellipsis
    truncated_description = description[:200] + "..." if len(description) > 200 else description
    
    # Get translations for labels
    municipality_label = TRANSLATIONS[language_code]['municipality']
    view_details_text = TRANSLATIONS[language_code]['view_details']

    st.markdown(f"""
        <div class="site-card">
            <h3>{site.name}</h3>
            <p><strong>{municipality_label}</strong> {site.municipality}</p>
            <p>{truncated_description}</p>
            <a href="1_Site_Dashboard?site={site.name}" target="_self">
                <button class="site-button">{view_details_text}</button>
            </a>
        </div>
    """, unsafe_allow_html=True)

# Display sites by municipality with translations
# Add municipality headers to translations
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

if zamboanguita_sites:
    st.header(municipality_names[language_code]["Zamboanguita"])
    cols = st.columns(3)
    for idx, site in enumerate(zamboanguita_sites):
        with cols[idx % 3]:
            create_site_card(site)

if siaton_sites:
    st.header(municipality_names[language_code]["Siaton"])
    cols = st.columns(3)
    for idx, site in enumerate(siaton_sites):
        with cols[idx % 3]:
            create_site_card(site)

if santa_catalina_sites:
    st.header(municipality_names[language_code]["Santa Catalina"])
    cols = st.columns(3)
    for idx, site in enumerate(santa_catalina_sites):
        with cols[idx % 3]:
            create_site_card(site)

# Clean up
db = next(get_db())
db.close()