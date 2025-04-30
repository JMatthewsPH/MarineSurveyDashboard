"""
Navigation utilities for consistent menu across pages
"""
import streamlit as st
from utils.translations import TRANSLATIONS

def display_navigation(current_page=None):
    """
    Display a modern, consistent navigation menu in the sidebar
    
    Args:
        current_page: The current page name to highlight in the menu
    """
    # Navigation dictionary with page names and icons
    navigation = {
        "Main": {
            "url": "/",
            "icon": "🏠"
        },
        "Site Dashboard": {
            "url": "/Site_Dashboard",
            "icon": "📊"
        },
        "Summary Dashboard": {
            "url": "/Summary_Dashboard",
            "icon": "📈"
        }
    }
    
    # Get language from session state
    lang = st.session_state.language if 'language' in st.session_state else "en"
    
    # Translation mapping for menu items
    menu_translations = {
        "en": {
            "Main": "Main Dashboard",
            "Site Dashboard": "Site Dashboard",
            "Summary Dashboard": "Summary Dashboard",
            "nav_title": "Navigation"
        },
        "tl": {
            "Main": "Pangunahing Dashboard",
            "Site Dashboard": "Dashboard ng Site",
            "Summary Dashboard": "Dashboard ng Buod",
            "nav_title": "Nabigasyon"
        },
        "ceb": {
            "Main": "Pangunang Dashboard",
            "Site Dashboard": "Dashboard sa Dapit",
            "Summary Dashboard": "Dashboard sa Katingban",
            "nav_title": "Nabigasyon"
        }
    }
    
    # Display navigation title
    st.markdown(f"### {menu_translations[lang]['nav_title']}")
    
    # Create navigation container
    st.markdown('<div class="navigation-container">', unsafe_allow_html=True)
    st.markdown('<ul class="nav-menu">', unsafe_allow_html=True)
    
    # Add each navigation item
    for page_name, page_info in navigation.items():
        # Determine if this is the current page
        is_active = current_page == page_name
        active_class = "active" if is_active else ""
        
        # Get translated page name
        translated_name = menu_translations[lang].get(page_name, page_name)
        
        # Render the navigation item
        st.markdown(
            f"""
            <li class="nav-item">
                <a href="{page_info['url']}" class="nav-link {active_class}">
                    <span class="nav-icon">{page_info['icon']}</span>
                    {translated_name}
                </a>
            </li>
            """,
            unsafe_allow_html=True
        )
    
    # Close navigation container
    st.markdown('</ul>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add a separator
    st.markdown("---")

def add_back_to_main_button(lang="en"):
    """
    Add a Back to Main button with proper translation
    
    Args:
        lang: Language code (en, tl, ceb)
    """
    # Translation for button text
    button_text = {
        "en": "Back to Main Dashboard",
        "tl": "Bumalik sa Pangunahing Dashboard",
        "ceb": "Balik sa Pangunang Dashboard"
    }
    
    # Get correct translation
    text = button_text.get(lang, button_text["en"])
    
    # Create the button
    st.markdown(
        f"""
        <a href="/" class="back-to-main-btn">
            <span class="back-arrow">←</span>
            {text}
        </a>
        """,
        unsafe_allow_html=True
    )