"""
Navigation utilities for consistent menu across pages
"""
import streamlit as st
from utils.translations import TRANSLATIONS

def display_navigation(current_page=None):
    """
    Display a navigation title in the sidebar
    This function is now simplified since we're using Streamlit's built-in navigation
    
    Args:
        current_page: The current page name (used only for compatibility with existing code)
    """
    # Get language from session state
    lang = st.session_state.language if 'language' in st.session_state else "en"
    
    # Translation mapping for navigation title
    menu_translations = {
        "en": {"nav_title": "Navigation"},
        "tl": {"nav_title": "Nabigasyon"},
        "ceb": {"nav_title": "Nabigasyon"}
    }
    
    # Display navigation title
    st.markdown(f"### {menu_translations[lang]['nav_title']}")
    
    # Add a separator
    st.markdown("---")

def add_back_to_main_button(lang="en"):
    """
    Add a Back to Main button with proper translation
    
    Note: This function is kept for backward compatibility but now simplified
    since we're using Streamlit's built-in navigation
    
    Args:
        lang: Language code (en, tl, ceb)
    """
    # This functionality is now handled by Streamlit's built-in navigation
    pass