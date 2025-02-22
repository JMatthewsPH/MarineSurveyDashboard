import streamlit as st
import os
from utils.data_processor import DataProcessor
from utils.database import get_db

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

# Header
st.markdown("""
    <div class="site-header">
        <h1>Marine Conservation Philippines</h1>
        <h2>Site Explorer</h2>
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
zamboanguita_sites = sorted([site for site in sites if site.municipality == "Zamboanguita"])
siaton_sites = sorted([site for site in sites if site.municipality == "Siaton"])
santa_catalina_sites = sorted([site for site in sites if site.municipality == "Santa Catalina"])

# Function to create site card
def create_site_card(site):
    st.markdown(f"""
        <div class="site-card">
            <h3>{site.name}</h3>
            <p><strong>Municipality:</strong> {site.municipality}</p>
            <p>{site.description_en[:200]}...</p>
            <a href="Site_Dashboard?site={site.name}" target="_self">
                <button class="site-button">View Details</button>
            </a>
        </div>
    """, unsafe_allow_html=True)

# Add new CSS for site cards
st.markdown("""
    <style>
    .site-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .site-card:hover {
        transform: translateY(-5px);
    }
    .site-button {
        background: #2b6cb0;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        cursor: pointer;
        margin-top: 1rem;
    }
    .site-button:hover {
        background: #4299e1;
    }
    .municipality-section {
        margin: 2rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Display sites by municipality
if zamboanguita_sites:
    st.header("Zamboanguita Sites")
    cols = st.columns(3)
    for idx, site in enumerate(zamboanguita_sites):
        with cols[idx % 3]:
            create_site_card(site)

if siaton_sites:
    st.header("Siaton Sites")
    cols = st.columns(3)
    for idx, site in enumerate(siaton_sites):
        with cols[idx % 3]:
            create_site_card(site)

if santa_catalina_sites:
    st.header("Santa Catalina Sites")
    cols = st.columns(3)
    for idx, site in enumerate(santa_catalina_sites):
        with cols[idx % 3]:
            create_site_card(site)

# Clean up
db = next(get_db())
db.close()