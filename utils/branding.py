"""
Branding utilities for consistent logo and branding across the application
"""

import streamlit as st
import os

def display_logo(size="medium"):
    """
    Display the logo with consistent styling across all pages
    
    Args:
        size: Size of the logo - "small", "medium", or "large"
    """
    # Size configurations
    sizes = {
        "small": {"width": 150, "columns": [2, 1, 2]},
        "medium": {"width": 200, "columns": [1.5, 1, 1.5]},
        "large": {"width": 300, "columns": [1, 2, 1]}
    }
    
    config = sizes.get(size, sizes["medium"])
    
    # Get logo path
    logo_text_path = os.path.join("assets", "branding", "logo_text.png")
    fallback_logo_path = os.path.join("attached_assets", "MCP_Data", "Logo Text Color.png")
    
    # Try to use the asset in the branding folder, or fall back to attached_assets
    if os.path.exists(logo_text_path):
        logo_path = logo_text_path
    elif os.path.exists(fallback_logo_path):
        logo_path = fallback_logo_path
    else:
        st.error("Logo not found in assets folder")
        return
        
    # Create columns to center and resize the logo
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

def get_base64_encoded_image(image_path):
    """
    Get the base64 encoded image
    """
    import base64
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()