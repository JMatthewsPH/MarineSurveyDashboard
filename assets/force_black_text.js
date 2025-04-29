// Force black text in light mode via JavaScript
(function() {
    function injectBlackTextCSS() {
        // Check if we're in light mode
        const isDarkMode = document.body.classList.contains('dark-mode') || 
                         document.body.getAttribute('data-theme') === 'dark';
                         
        if (!isDarkMode) {
            // Create a style element
            const style = document.createElement('style');
            style.id = 'force-black-text-style';
            style.textContent = `
                /* Force ALL text to be pure black */
                *, h1, h2, h3, h4, h5, h6, p, span, div, label, a, li {
                    color: #000000 !important;
                    opacity: 1 !important;
                }
                
                /* Target headings */
                .stHeading, .css-10trblm, .css-ulpx6n, h1, h2, h3, h4, h5, h6 {
                    color: #000000 !important;
                    opacity: 1 !important;
                    font-weight: 600 !important;
                }
                
                /* Target site descriptions */
                .site-description, .site-description-title, .site-description-text, 
                .site-metrics-title, .site-metrics-content {
                    color: #000000 !important;
                    opacity: 1 !important;
                }
                
                /* Target chart text */
                .js-plotly-plot .plotly text,
                .js-plotly-plot .plotly .gtitle,
                .js-plotly-plot .plotly .xtitle,
                .js-plotly-plot .plotly .ytitle,
                .js-plotly-plot .plotly .xtick text,
                .js-plotly-plot .plotly .ytick text {
                    fill: #000000 !important;
                }
                
                /* Target main content */
                main[data-testid="stAppViewContainer"] * {
                    color: #000000 !important;
                }
            `;
            
            // Remove existing style if present
            const existingStyle = document.getElementById('force-black-text-style');
            if (existingStyle) {
                existingStyle.remove();
            }
            
            // Add to document head
            document.head.appendChild(style);
            
            // Apply black color directly to text elements
            const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div, label');
            textElements.forEach(el => {
                el.style.setProperty('color', '#000000', 'important');
                el.style.setProperty('opacity', '1', 'important');
            });
            
            // Apply to SVG text elements
            const svgTextElements = document.querySelectorAll('svg text');
            svgTextElements.forEach(el => {
                el.style.setProperty('fill', '#000000', 'important');
            });
        }
    }
    
    // Run when DOM loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectBlackTextCSS);
    } else {
        injectBlackTextCSS();
    }
    
    // Run whenever content changes
    const observer = new MutationObserver(() => {
        injectBlackTextCSS();
    });
    
    // Start observing the document
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Also run periodically
    setInterval(injectBlackTextCSS, 1000);
})();