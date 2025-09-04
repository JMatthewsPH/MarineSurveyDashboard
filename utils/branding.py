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
        "small": {"width": 200},
        "medium": {"width": 300},
        "large": {"width": 400}
    }
    
    if os.path.exists(logo_path):
        config = size_configs.get(size, size_configs["medium"])
        
        # Convert logo to base64 for better control
        logo_b64 = get_base64_encoded_image(logo_path)
        
        # Create centered logo using HTML to avoid clickable behavior
        st.markdown(f'''
            <div style="display: flex; justify-content: center; align-items: center; margin: 5px auto 15px auto; width: 100%; text-align: center;">
                <img src="data:image/png;base64,{logo_b64}" 
                     width="{config["width"]}" 
                     style="max-width: 100%; height: auto; pointer-events: none; margin: 0 auto; display: block;">
            </div>
        ''', unsafe_allow_html=True)
        
        # Add CSS to remove any unwanted anchor elements around images
        st.markdown("""
            <style>
            /* Remove anchor elements around logo images */
            .stApp a[href="#"]:has(img),
            .stApp a[href=""]:has(img),
            .stApp a:not([href]):has(img) {
                pointer-events: none !important;
                text-decoration: none !important;
                color: inherit !important;
            }
            
            /* Ensure logo images are not clickable */
            .stApp img {
                pointer-events: none !important;
            }
            
            /* Center logo container */
            .stApp .element-container:has(img[src*="Logo"]) {
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
            }
            </style>
        """, unsafe_allow_html=True)

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
                /* Completely hide and override all Streamlit loading elements */
                .stSpinner,
                .stSpinner *,
                div[data-testid="stStatusWidget"] svg,
                div[data-testid="stStatusWidget"] [class*="spinner"],
                .element-container .stSpinner,
                .stApp svg[class*="spinner"],
                .stApp svg[class*="loading"],
                .stApp div[class*="spinner"] svg {{
                    display: none !important;
                    visibility: hidden !important;
                    opacity: 0 !important;
                    width: 0 !important;
                    height: 0 !important;
                }}
                
                /* Replace ALL spinner containers with custom GIF */
                .stSpinner::before,
                .element-container .stSpinner::before {{
                    content: "" !important;
                    display: block !important;
                    width: 50px !important;
                    height: 50px !important;
                    background-image: url("data:image/gif;base64,{gif_b64}") !important;
                    background-repeat: no-repeat !important;
                    background-position: center !important;
                    background-size: contain !important;
                    margin: 0 auto !important;
                    position: absolute !important;
                    top: 50% !important;
                    left: 50% !important;
                    transform: translate(-50%, -50%) !important;
                    z-index: 9999 !important;
                }}
                
                .stSpinner {{
                    position: relative !important;
                    width: 50px !important;
                    height: 50px !important;
                    margin: 0 auto !important;
                }}
                
                /* Status widget complete override */
                div[data-testid="stStatusWidget"] {{
                    background-image: url("data:image/gif;base64,{gif_b64}") !important;
                    background-repeat: no-repeat !important;
                    background-position: center !important;
                    background-size: 20px 20px !important;
                    width: 30px !important;
                    height: 30px !important;
                    text-indent: -9999px !important;
                    color: transparent !important;
                    overflow: hidden !important;
                }}
                
                div[data-testid="stStatusWidget"] * {{
                    display: none !important;
                }}
                </style>
                
                <script>
                // JavaScript to aggressively replace any remaining spinners
                function replaceSpinners() {{
                    const gifSrc = "data:image/gif;base64,{gif_b64}";
                    
                    // Find all spinner elements
                    const spinners = document.querySelectorAll('.stSpinner, [class*="spinner"], [data-testid="stStatusWidget"]');
                    
                    spinners.forEach(spinner => {{
                        // Hide all children
                        Array.from(spinner.children).forEach(child => {{
                            child.style.display = 'none';
                        }});
                        
                        // Replace with custom GIF
                        spinner.innerHTML = `<img src="${{gifSrc}}" style="width: 30px; height: 30px; display: block; margin: 0 auto;">`;
                    }});
                    
                    // Also target SVG elements specifically
                    const svgs = document.querySelectorAll('svg[class*="spinner"], svg[class*="loading"]');
                    svgs.forEach(svg => {{
                        const img = document.createElement('img');
                        img.src = gifSrc;
                        img.style.width = '30px';
                        img.style.height = '30px';
                        svg.parentNode.replaceChild(img, svg);
                    }});
                }}
                
                // Run immediately and set up observers
                replaceSpinners();
                
                // Watch for new elements
                const observer = new MutationObserver(replaceSpinners);
                observer.observe(document.body, {{ childList: true, subtree: true }});
                
                // Also run periodically
                setInterval(replaceSpinners, 1000);
                </script>
            ''', unsafe_allow_html=True)
    except Exception as e:
        # Silently handle errors to avoid breaking the app
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