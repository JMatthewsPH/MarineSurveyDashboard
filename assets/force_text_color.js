// Force text color to pure black in light mode
(function() {
    function forceTextColor() {
        // Check if we're in light mode
        const isLightMode = !document.body.classList.contains('dark-mode');
        
        if (isLightMode) {
            // Apply to all text elements
            const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div, label, .stMarkdown, .stText');
            textElements.forEach(el => {
                el.style.color = '#000000';
                el.style.opacity = '1';
            });
            
            // Apply to all chart text
            const chartTexts = document.querySelectorAll('.js-plotly-plot .plotly text, .gtitle, .xtitle, .ytitle, .xtick text, .ytick text');
            chartTexts.forEach(el => {
                el.style.fill = '#000000';
            });
            
            // Apply to site descriptions
            const siteDesc = document.querySelectorAll('.site-description, .site-description p, .site-card p');
            siteDesc.forEach(el => {
                el.style.color = '#000000';
                el.style.opacity = '1';
            });
        }
        
        // Run again after a short delay to catch dynamically loaded content
        setTimeout(forceTextColor, 1000);
    }
    
    // Run on page load
    window.addEventListener('load', forceTextColor);
    // Start immediately
    forceTextColor();
})();