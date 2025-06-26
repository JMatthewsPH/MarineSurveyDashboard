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
    
    # Get logo path - using the new Logo Text Color.png file
    logo_path = os.path.join("assets", "branding", "Logo Text Color.png")
    
    # Check if the logo exists
    if not os.path.exists(logo_path):
        st.error("Logo not found in assets folder")
        return
        
    # Use base64 encoding to preserve image quality and avoid Streamlit compression
    try:
        logo_base64 = get_base64_encoded_image(logo_path)
        
        # Create columns to center the logo
        cols = st.columns(config["columns"])
        with cols[1]:
            # Use HTML img tag with base64 data to preserve quality
            logo_html = f"""
            <div style="display: flex; justify-content: center; align-items: center;">
                <img src="data:image/png;base64,{logo_base64}" 
                     style="width: {config['width']}px; height: auto; image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges;"
                     alt="Marine Conservation Philippines Logo">
            </div>
            """
            st.markdown(logo_html, unsafe_allow_html=True)
    except Exception as e:
        # Fallback to regular st.image if base64 fails
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
    Replace Streamlit's default loading animation with custom AnimRun.gif
    """
    try:
        gif_path = "assets/branding/AnimRun.gif"
        if os.path.exists(gif_path):
            gif_b64 = get_base64_encoded_image(gif_path)
            st.markdown(f'''
                <style>
                /* Hide all default Streamlit spinners and running indicators */
                .stSpinner > div > div,
                .stSpinner > div > div > div,
                .stSpinner svg,
                div[data-testid="stStatusWidget"] svg,
                div[data-testid="stStatusWidget"] .stSpinner,
                .stApp [data-testid="stStatusWidget"] svg {{
                    display: none !important;
                    visibility: hidden !important;
                    opacity: 0 !important;
                }}
                
                /* Replace main spinner with custom GIF */
                .stSpinner > div {{
                    background-image: url("data:image/gif;base64,{gif_b64}") !important;
                    background-repeat: no-repeat !important;
                    background-position: center !important;
                    background-size: 50px 50px !important;
                    width: 50px !important;
                    height: 50px !important;
                    margin: 0 auto !important;
                    border: none !important;
                    animation: none !important;
                }}
                
                /* Replace status widget running indicator */
                div[data-testid="stStatusWidget"] {{
                    background-image: url("data:image/gif;base64,{gif_b64}") !important;
                    background-repeat: no-repeat !important;
                    background-position: center !important;
                    background-size: 20px 20px !important;
                    width: 30px !important;
                    height: 30px !important;
                }}
                
                /* Hide text in status widget and replace with custom animation */
                div[data-testid="stStatusWidget"] > div {{
                    background-image: url("data:image/gif;base64,{gif_b64}") !important;
                    background-repeat: no-repeat !important;
                    background-position: center !important;
                    background-size: 20px 20px !important;
                    color: transparent !important;
                    text-indent: -9999px !important;
                    width: 30px !important;
                    height: 30px !important;
                }}
                
                /* Target any other spinner patterns */
                .stApp .stSpinner,
                .stApp [class*="spinner"],
                .stApp [class*="loading"] {{
                    background-image: url("data:image/gif;base64,{gif_b64}") !important;
                    background-repeat: no-repeat !important;
                    background-position: center !important;
                    background-size: contain !important;
                }}
                </style>
            ''', unsafe_allow_html=True)
    except Exception as e:
        print(f"Error adding custom loading animation: {e}")

def get_base64_encoded_image(image_path):
    """
    Get the base64 encoded image
    """
    import base64
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()