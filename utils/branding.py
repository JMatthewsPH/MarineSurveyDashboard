"""
Branding utilities for consistent logo and branding across the application
"""

import streamlit as st
import os
import base64

def display_logo(size="medium"):
    """
    Display the logo with consistent styling across all pages
    
    Args:
        size: Size of the logo - "small", "medium", or "large"
    """
    logo_path = "assets/branding/Logo Text Color.png"
    
    # Size configurations
    size_configs = {
        "small": {"width": 200, "columns": [1, 2, 1]},
        "medium": {"width": 300, "columns": [1, 3, 1]},
        "large": {"width": 400, "columns": [1, 4, 1]}
    }
    
    if os.path.exists(logo_path):
        config = size_configs.get(size, size_configs["medium"])
        cols = st.columns(config["columns"])
        with cols[1]:
            st.image(logo_path, width=config["width"])

def add_favicon():
    """
    Add favicon to the webpage
    """
    favicon_path = "assets/branding/favicon.ico"
    favicon_png_path = "assets/branding/favicon.png"
    favicon_icon_path = "assets/branding/logo_icon.png"
    
    # Try ico file first, then png, then the original logo
    if os.path.exists(favicon_path):
        favicon_html = """
        <link rel="shortcut icon" href="data:image/x-icon;base64,{0}">
        """.format(get_base64_encoded_image(favicon_path))
        st.markdown(favicon_html, unsafe_allow_html=True)
    elif os.path.exists(favicon_png_path):
        favicon_html = """
        <link rel="shortcut icon" href="data:image/png;base64,{0}">
        """.format(get_base64_encoded_image(favicon_png_path))
        st.markdown(favicon_html, unsafe_allow_html=True)
    elif os.path.exists(favicon_icon_path):
        favicon_html = """
        <link rel="shortcut icon" href="data:image/png;base64,{0}">
        """.format(get_base64_encoded_image(favicon_icon_path))
        st.markdown(favicon_html, unsafe_allow_html=True)

def add_custom_loading_animation():
    """
    Placeholder function - now using st.spinner() with custom text instead of CSS override
    """
    pass

def get_base64_encoded_image(image_path):
    """
    Get the base64 encoded image
    """
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return ""