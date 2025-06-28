# Marine Conservation Philippines Platform

## Overview
The Marine Conservation Philippines Platform is a comprehensive data visualization and analysis tool for monitoring marine protected areas (MPAs) across different municipalities in the Philippines. The platform provides interactive dashboards to track ecological metrics including coral cover, fish biomass, biodiversity indices, and conservation effectiveness over time.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit-based web application with multi-page navigation
- **UI Components**: Interactive charts using Plotly, responsive layout with custom CSS
- **Branding**: Centralized logo and favicon management through utilities
- **Multi-language Support**: English, Tagalog, and Cebuano translations
- **Navigation**: Built-in Streamlit page navigation with custom JavaScript enhancements

### Backend Architecture
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Connection Management**: Connection pooling with health checks and SSL support
- **Data Processing**: Cached data processor with performance optimization
- **Query Optimization**: Batch queries and centralized query builder pattern

### Data Model
- **Sites Table**: Marine protected area information with municipality grouping
- **Surveys Table**: Time-series ecological measurements with foreign key relationships
- **Metrics**: Hard coral cover, fish densities by feeding group, biomass data, substrate composition

## Key Components

### Data Processing Layer
- **DataProcessor Class**: Centralized data retrieval and transformation with caching
- **QueryBuilder Class**: Optimized database query construction and batch operations
- **Performance Monitoring**: Timing measurements and logging for optimization

### Visualization Layer
- **GraphGenerator Class**: Creates interactive Plotly charts with COVID-19 gap detection
- **Timeline Management**: Quarter-based seasonal formatting (MAR-MAY, JUN-AUG, etc.)
- **Comparison Features**: Site-to-site comparisons and municipal averages

### Data Import System
- **Legacy Importer**: Handles original CSV format with seasonal naming
- **New Data Importer**: Processes structured fish/invertebrate/substrate data
- **Site Name Mapping**: Consistent site naming across different data sources

### UI/UX Features
- **Loading States**: Skeleton charts and loading spinners for improved UX
- **Export Capabilities**: CSV export and PDF report generation
- **Responsive Design**: Mobile-friendly layout with custom CSS styling

## Data Flow

1. **Data Import**: CSV files processed through importers with validation and transformation
2. **Database Storage**: Normalized data stored in PostgreSQL with relationship integrity
3. **Data Retrieval**: Cached queries through DataProcessor with performance optimization
4. **Visualization**: Interactive charts generated via GraphGenerator with real-time updates
5. **User Interaction**: Multi-language interface with site comparison and analysis tools

## External Dependencies

### Core Dependencies
- **Streamlit**: Web application framework (>=1.28.0)
- **PostgreSQL**: Primary database with psycopg2-binary driver
- **Plotly**: Interactive charting library (>=5.15.0)
- **Pandas**: Data manipulation and analysis (>=2.0.0)
- **SQLAlchemy**: Database ORM (>=2.0.0)

### Supporting Libraries
- **ReportLab**: PDF generation for export functionality
- **Matplotlib**: Additional charting capabilities
- **NumPy**: Numerical computations for data processing

### Infrastructure
- **Replit Environment**: PostgreSQL 16 module with Python 3.11
- **Docker Support**: Lightweight container with system dependencies
- **SSL Configuration**: Secure database connections with keepalive settings

## Deployment Strategy

### Replit Configuration
- **Auto-scaling Deployment**: Target configured for production scaling
- **Port Configuration**: Streamlit server on port 5000 with external port 80
- **Workflow Management**: Parallel execution with automatic restart capabilities

### Performance Optimization
- **Connection Pooling**: Database connection management with timeout settings
- **Caching Strategy**: Resource caching with TTL for data processor instances
- **Asset Optimization**: CSS/JS minification and image optimization

### Monitoring and Logging
- **Performance Timing**: Data processing and query execution monitoring
- **Error Handling**: Comprehensive exception handling with user-friendly messages
- **Health Checks**: Database connection validation and automatic recovery

## Changelog
- June 28, 2025: **SITE CARD STYLING RESTORATION** - Fixed site card uniform heights using 340px fixed height with flexbox layout. Restored brand-consistent blue color scheme (#2b6cb0) matching Marine Conservation Philippines logo for buttons and headers, replacing accidental green styling. Maintained professional appearance with proper shadows and hover effects.
- June 28, 2025: **INTERACTIVE BIOMASS HEATMAP IMPROVEMENTS** - Enhanced map visualization with: lighter sea-focused Ocean View tile layer, reduced heatmap transparency (0.15) and smaller radius (15px) to minimize land spillover, replaced large pin markers with tiny 4px circle markers matching site card style, added clean municipality labels (Santa Catalina, Siaton, Zamboanguita) without Google Maps clutter, hidden Streamlit settings menu (triple-dot) via CSS.
- June 28, 2025: **HARD CORAL COVER COMPARISON FIX** - Fixed ValueError in SimpleGraphGenerator where comparison labels were passed as lists but Plotly expected strings. Added robust label handling to prevent chart rendering errors during municipality comparisons.
- June 28, 2025: **ERROR BARS ANALYSIS COMPLETE** - Determined error bars cannot function with current data structure (one pre-aggregated seasonal mean per data point). Confidence intervals remain functional and valuable, showing between-season variability. Error bars would require raw survey data access for within-season calculations.
- June 28, 2025: **CHECKBOX FUNCTIONALITY FIX** - Resolved session state race conditions causing analysis option checkboxes to require multiple clicks. Removed conflicting session state management and implemented native Streamlit checkbox handling for Error Bars, Confidence Intervals, and Straight Line Graphs options. Cleaned up duplicate "Analysis Options" headers in sidebar.
- June 28, 2025: **SMOOTH CURVE IMPLEMENTATION** - Applied smooth/rounded line graphs as default across all charts site-wide. All Plotly scatter plots now use spline curves with smoothing=1.3 for improved visual appeal and data trend visualization.
- June 27, 2025: **DYNAMIC HEATMAP SCALING** - Implemented scalable legend and coloring system for biomass heatmap that automatically adapts to data distribution using percentile-based thresholds (66.67% and 33.33% for color divisions). Legend now displays actual calculated ranges instead of fixed values, preventing visualization issues when new data is added.
- June 27, 2025: **TREND ANALYSIS DISCLAIMER** - Added comprehensive data interpretation disclaimer below trend analysis section explaining that graphs show averages of surveyed sites, survey site changes over time, and potential data skewing effects from new MPA additions.
- June 27, 2025: **Y-AXIS DEFAULT RANGE FIX** - Fixed Y-axis default range for empty data cases to show [0,0] instead of [0,10], preventing misleading scale when no data is available.
- June 27, 2025: **GEOGRAPHIC DISTRIBUTION CHART REMOVAL** - Removed misleading Geographic Distribution chart from Summary Dashboard per user request. Dashboard now shows only relevant sections: Key Metrics, Site Comparison Matrix, and Trend Analysis.
- June 27, 2025: **LOGO CENTERING AND LINK REMOVAL FIX** - Fixed logo positioning by switching from Streamlit columns to HTML flexbox centering. Removed unwanted clickable link control using CSS pointer-events and base64 encoding for better display control.
- June 27, 2025: **SITE DASHBOARD COVID GAP DETECTION FIX** - Resolved critical issue where COVID period gap lines weren't appearing in Site Dashboard due to NaN values in post-COVID data points. SimpleGraphGenerator now properly handles missing data by validating both endpoints before creating gap lines. COVID gaps now display correctly for metrics with valid data (Bleaching, Rubble, Hard Coral, Fleshy Algae) while gracefully skipping gap lines for metrics with missing post-COVID values (fish densities, biomass).
- June 27, 2025: **CHART TITLE CENTERING FIX** - Resolved Plotly title positioning issue where titles defaulted to plot area coordinates instead of paper coordinates, causing misalignment with margins and legends. Now all chart titles are properly centered on charts using paper-relative positioning.
- June 27, 2025: **MOBILE-OPTIMIZED LAYOUT** - Removed redundant Streamlit titles above charts, keeping only centered Plotly titles on charts for cleaner mobile viewing experience
- June 27, 2025: **DATA CLEANUP** - Removed 6 erroneous survey records from MAR-MAY 2021 that fell within COVID gap period (Apr 2020 - Mar 2022). Total dataset now contains 255 surveys.
- June 27, 2025: **MAJOR DATA UPDATE** - Switched to comprehensive new_data dataset. Commercial biomass now available for ALL 15/15 sites (previously 8/15). Complete data coverage achieved. Dataset extends to April 2025.
- June 27, 2025: Created dedicated SummaryGraphGenerator for Summary Dashboard to resolve commercial biomass visualization issues - now displays properly in both Site Comparison Matrix and Trend Analysis sections
- June 27, 2025: Fixed COVID gap period to show correct timeframe (Apr 2020 - Mar 2022) to properly include SEP-NOV 2019 and Winter 19/20 data points before gap starts
- June 26, 2025: Fixed bar chart to display all 15 sites by replacing missing data with 0 values instead of dropping rows
- June 26, 2025: Added municipality-grouped bar chart for site comparison with red-yellow-green health indicators and Y-axis starting from 0
- June 26, 2025: Restored CSS-based AnimRun.gif animation after `st.spinner()` approach failed to show custom animation
- June 26, 2025: **ROLLBACK POINT** - CSS-based AnimRun.gif animation working for post-startup loading states
- June 26, 2025: Implemented custom loading animation using AnimRun.gif to replace Streamlit's default spinner with enhanced CSS targeting
- June 26, 2025: Fine-tuned PDF logo dimensions to 6" x 1.87" for perfect circular proportions after user feedback
- June 26, 2025: Fixed PDF logo quality issues with improved sizing (4" x 1.5") and proper aspect ratio
- June 26, 2025: Added branded logo ("Logo Text Color.png") to all PDF reports for professional appearance
- June 26, 2025: Enhanced PDF report format with international-friendly date (2025-JUNE-26) and descriptive text including site name and municipality
- June 26, 2025: Fixed PDF generation error with municipality data retrieval using improved error handling
- June 26, 2025: Updated PDF filename format to match content date format for consistency
- June 26, 2025: Refined anchor element hiding to preserve site card navigation buttons while removing unwanted header anchors
- June 26, 2025: Implemented true one-click PDF export - pre-generates PDFs for immediate download without additional clicks
- June 26, 2025: Fixed unwanted anchor elements throughout dashboard using native CSS approach targeting Streamlit's header anchors
- June 26, 2025: Updated logo to use "Logo Text Color.png" with base64 encoding for crisp display quality
- June 25, 2025: Initial setup

## Future Enhancement Suggestions
- **Per-Season Confidence Intervals**: Investigate accessing raw survey counts and within-season standard deviations to calculate proper confidence intervals around each seasonal mean estimate (showing precision of ~1000 surveys per season rather than between-season variability)

## User Preferences

Preferred communication style: Simple, everyday language.
Logo preferences: Use high-quality lossless display with base64 encoding to avoid compression, 4"x1.5" sizing for PDFs
UX preferences: Streamline user interactions - avoid unnecessary clicks (e.g., auto-download PDFs)
Development approach: Prefer native Streamlit solutions over complex JavaScript when possible
PDF quality: Professional appearance with proper logo sizing and aspect ratios