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
    Placeholder function - now using st.spinner() with custom text instead of CSS override
    """
    pass
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
        print(f"Error adding custom loading animation: {e}")

def get_base64_encoded_image(image_path):
    """
    Get the base64 encoded image
    """
    import base64
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()