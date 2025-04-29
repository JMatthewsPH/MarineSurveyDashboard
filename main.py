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

st.markdown(load_css(), unsafe_allow_html=True)

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

    # Add site description based on selected language
    st.markdown("---")  # Add a visual separator
    st.title("About")
    if st.session_state.language == "English":
        st.markdown("""
        The Marine Conservation Dashboard provides a comprehensive visualization platform for monitoring marine protected areas (MPAs) across different municipalities. It displays critical ecological data including coral cover, fish biomass, and various marine species density measurements.

        Users can compare data between sites or against municipal averages, track changes over time, and analyze the impact of conservation efforts. The interactive graphs include markers for significant events like the COVID-19 period, helping researchers and conservationists understand long-term ecological trends.
        """)
    else:
        st.markdown("""
        Ang Dashboard ng Pangangalaga sa Karagatan ay nagbibigay ng komprehensibong plataporma para sa pagsubaybay sa mga Protected Marine Areas (MPAs) sa iba't ibang munisipyo. Ipinapakita nito ang mahahalagang datos tungkol sa ecological system tulad ng saklaw ng coral, dami ng isda, at iba't ibang sukat ng densidad ng mga species sa dagat.

        Maaaring ihambing ang datos sa pagitan ng mga lugar o sa average ng munisipyo, subaybayan ang mga pagbabago sa paglipas ng panahon, at suriin ang epekto ng mga pagsisikap sa pangangalaga. Ang mga interactive na graph ay may marka para sa mahahalagang pangyayari tulad ng panahon ng COVID-19, na tumutulong sa mga mananaliksik at conservationist na maintindihan ang pangmatagalang ecological trends.
        """)

# Use session state language for content
language = st.session_state.language

# Header
subheader_text = "Marine Monitoring Dashboard" if language == "English" else "Dashboard ng Pagsubaybay sa Karagatan"

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
    description = site.description_fil if language == "Filipino" else site.description_en
    description = description or ("Paglalarawan ng lugar ay darating sa lalong madaling panahon..." 
                                 if language == "Filipino" else "Site description coming soon...")
    # Truncate description to 200 characters and add ellipsis
    truncated_description = description[:200] + "..." if len(description) > 200 else description
    municipality_label = "Munisipyo:" if language == "Filipino" else "Municipality:"
    view_details_text = "Tingnan ang Detalye" if language == "Filipino" else "View Details"

    st.markdown(f"""
        <div class="site-card">
            <h3>{site.name}</h3>
            <p><strong>{municipality_label}</strong> {site.municipality}</p>
            <p>{truncated_description}</p>
            <a href="Site_Dashboard?site={site.name}" target="_self">
                <button class="site-button">{view_details_text}</button>
            </a>
        </div>
    """, unsafe_allow_html=True)

# Display sites by municipality with translations
municipality_headers = {
    "Zamboanguita": {
        "English": "Zamboanguita Sites",
        "Filipino": "Mga Lugar sa Zamboanguita"
    },
    "Siaton": {
        "English": "Siaton Sites",
        "Filipino": "Mga Lugar sa Siaton"
    },
    "Santa Catalina": {
        "English": "Santa Catalina Sites",
        "Filipino": "Mga Lugar sa Santa Catalina"
    }
}

if zamboanguita_sites:
    st.header(municipality_headers["Zamboanguita"][language])
    cols = st.columns(3)
    for idx, site in enumerate(zamboanguita_sites):
        with cols[idx % 3]:
            create_site_card(site)

if siaton_sites:
    st.header(municipality_headers["Siaton"][language])
    cols = st.columns(3)
    for idx, site in enumerate(siaton_sites):
        with cols[idx % 3]:
            create_site_card(site)

if santa_catalina_sites:
    st.header(municipality_headers["Santa Catalina"][language])
    cols = st.columns(3)
    for idx, site in enumerate(santa_catalina_sites):
        with cols[idx % 3]:
            create_site_card(site)

# Clean up
db = next(get_db())
db.close()