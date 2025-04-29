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
    st.session_state.theme = "light"  # Default to light mode

# Add JavaScript for theme toggling
theme_toggle_js = """
<script>
    document.addEventListener('DOMContentLoaded', (event) => {
        // Apply the theme
        function applyTheme(theme) {
            if (theme === 'dark') {
                document.body.classList.add('dark-theme');
                document.body.classList.remove('light-theme');
            } else {
                document.body.classList.add('light-theme');
                document.body.classList.remove('dark-theme');
            }
        }
        
        // Monitor for theme changes in localStorage
        window.addEventListener('storage', function(e) {
            if (e.key === 'streamlit_theme') {
                applyTheme(e.newValue);
            }
        });
        
        // Initialize theme
        const currentTheme = localStorage.getItem('streamlit_theme') || 'light';
        applyTheme(currentTheme);
    });
    
    // Function to toggle theme
    function toggleTheme() {
        const currentTheme = localStorage.getItem('streamlit_theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        localStorage.setItem('streamlit_theme', newTheme);
        
        // Apply immediately for current window
        if (newTheme === 'dark') {
            document.body.classList.add('dark-theme');
            document.body.classList.remove('light-theme');
        } else {
            document.body.classList.add('light-theme');
            document.body.classList.remove('dark-theme');
        }
    }
</script>
"""

st.markdown(theme_toggle_js, unsafe_allow_html=True)

# Sidebar for language selection
with st.sidebar:
    # Create a container for the theme toggle at the top of sidebar
    theme_container = st.container()
    
    with theme_container:
        # Add a theme toggle button that uses JavaScript (with text instead of emojis)
        theme_toggle_html = """
        <div class="theme-toggle-wrapper">
            <button onclick="toggleTheme()" class="theme-toggle-button">
                <span class="light-icon">Light</span>
                <span class="dark-icon">Dark</span>
            </button>
        </div>
        """
        st.markdown(theme_toggle_html, unsafe_allow_html=True)
    
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