import streamlit as st
import os
from utils.data_processor import DataProcessor
from utils.database import get_db
from utils.translations import TRANSLATIONS

# Page configuration
st.set_page_config(
    page_title="Marine Conservation Philippines",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
@st.cache_data
def load_css():
    with open('assets/site_styles.css') as f:
        return f'<style>{f.read()}</style>'

st.markdown(load_css(), unsafe_allow_html=True)

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

# Use session state language for content
language = st.session_state.language

# Header
subheader_text = "Marine Monitoring Dashboard" if language == "English" else "Dashboard ng Pagsubaybay sa Karagatan"

# Get logo path
logo_path = os.path.join("attached_assets", "MCP_Data", "Logo Text Color.png")

# Debug information
st.write("Current working directory:", os.getcwd())
st.write("Looking for logo at:", os.path.abspath(logo_path))
if os.path.exists(logo_path):
    # Create columns to center and resize the logo
    cols = st.columns([2, 1, 2])  # This creates a smaller center column
    with cols[1]:
        st.image(logo_path, use_column_width=True)

    st.markdown(f"""
        <div class="site-header">
            <h2>{subheader_text}</h2>
        </div>
    """, unsafe_allow_html=True)
else:
    # List directory contents for debugging
    st.error(f"Logo not found at path: {logo_path}")
    st.write("Contents of attached_assets/MCP_Data:")
    try:
        mcp_data_path = os.path.join("attached_assets", "MCP_Data")
        if os.path.exists(mcp_data_path):
            st.write(os.listdir(mcp_data_path))
        else:
            st.error(f"Directory not found: {mcp_data_path}")
    except Exception as e:
        st.error(f"Error checking directory: {str(e)}")

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