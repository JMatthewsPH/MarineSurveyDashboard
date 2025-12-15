# Marine Conservation Philippines Platform

## Overview
The Marine Conservation Philippines Platform is a comprehensive data visualization and analysis tool for monitoring marine protected areas (MPAs) across different municipalities in the Philippines. The platform provides interactive dashboards to track ecological metrics including coral cover, fish biomass, biodiversity indices, and conservation effectiveness over time. Features an advanced biomass heatmap with ocean-constrained radiation effects and comprehensive trend analysis capabilities. Its business vision is to empower marine conservation efforts through accessible and insightful data.

## User Preferences
Preferred communication style: Simple, everyday language.
Logo preferences: Use high-quality lossless display with base64 encoding to avoid compression, 4"x1.5" sizing for PDFs
UX preferences: Streamline user interactions - avoid unnecessary clicks (e.g., auto-download PDFs)
Development approach: Prefer native Streamlit solutions over complex JavaScript when possible
PDF quality: Professional appearance with proper logo sizing and aspect ratios

## System Architecture

### UI/UX Decisions
- **Framework**: Streamlit-based web application with multi-page navigation.
- **UI Components**: Interactive charts using Plotly, responsive layout with custom CSS, skeleton charts and loading spinners.
- **Branding**: Centralized logo and favicon management, brand-consistent blue color scheme.
- **Navigation**: Built-in Streamlit page navigation with custom JavaScript enhancements.
- **Multi-language Support**: English, Tagalog, and Cebuano translations.
- **Export Capabilities**: CSV export and PDF report generation with professional branding.
- **Responsive Design**: Mobile-friendly layout.

### Technical Implementations
- **Data Processing Layer**: Centralized data retrieval and transformation with caching, optimized database query construction and batch operations, performance monitoring.
- **Visualization Layer**: Interactive Plotly charts with COVID-19 gap detection, quarter-based seasonal formatting, site-to-site comparisons and municipal averages.
- **Data Import System**: Handles original CSV format and structured fish/invertebrate/substrate data, consistent site naming.
- **Query Optimization**: Batch queries and centralized query builder pattern.
- **Performance Optimization**: Connection pooling, resource caching with TTL, asset optimization (CSS/JS minification).
- **Error Handling**: Comprehensive exception handling with user-friendly messages.

### Feature Specifications
- **Data Metrics**: Hard coral cover, fish densities by feeding group, biomass data, substrate composition.
- **Comparison Features**: Site-to-site comparisons and municipal averages.
- **Trend Analysis**: Municipal-level averaging system for broad overview (All Municipalities, Zamboanguita, Siaton, Santa Catalina), "All Sites" grouping option for overall average across all monitored sites.
- **Biomass Heatmap**: Interactive map visualization with scalable legend and coloring system.
- **Data Integrity**: Robust data validation during import, consistent site name mapping.

### System Design Choices
- **Frontend Framework**: Streamlit chosen for rapid development and data app focus.
- **Backend Database**: PostgreSQL for relational data storage and integrity.
- **ORM**: SQLAlchemy for robust database interaction.
- **Data Flow**: Structured import, normalized storage, cached retrieval, interactive visualization, and user interaction.

## External Dependencies

### Core Dependencies
- **Streamlit**: Web application framework.
- **PostgreSQL**: Primary database (via psycopg2-binary driver).
- **Plotly**: Interactive charting library.
- **Pandas**: Data manipulation and analysis.
- **SQLAlchemy**: Database ORM.

### Supporting Libraries
- **ReportLab**: PDF generation for export functionality.
- **Matplotlib**: Additional charting capabilities.
- **NumPy**: Numerical computations for data processing.

### Infrastructure
- **Replit Environment**: PostgreSQL 16 module with Python 3.11.
- **Docker Support**: Lightweight container with system dependencies.
- **SSL Configuration**: Secure database connections with keepalive settings.

## Data Maintenance

### Data Format Standards
- **CSV Storage**: Values stored as decimals (0.19 = 19%)
- **Database Storage**: Values stored as decimals (0.19)
- **Display Conversion**: Multiplied by 100 for percentage display (0.19 → 19%)

### Data Reimport Process
When CSV data doesn't match displayed values:
1. Verify CSV shows decimal format (e.g., 0.19 for 19%)
2. Check database values with SQL query
3. Reimport specific category: `python3 -c "from utils.new_data_importer import import_category_data; from utils.database import get_db_session; import logging; logging.basicConfig(level=logging.INFO); with get_db_session() as db: import_category_data('attached_assets/MCP_Data/new_data/[category]', db)"`
4. Categories: 'subs' (substrate/coral), 'fish', 'inverts'
5. Verify fix with SQL query after reimport

### Recent Fixes
- **2025-11-19 (Latest)**: Major data corruption cleanup
  - Deleted 11 phantom database entries for 2025-10-01 (Autumn 2025) with corrupted data
  - Sites affected: Latason (352% → 23%), Antulang (2833% → 26%), Dalakit (1500% → 15%), and 8 others
  - Root cause: Phantom entries for non-existent Autumn 2025 period (CSV files only go to Summer 2025)
  - Fixed chart generators (SimpleGraphGenerator and SummaryGraphGenerator) to properly convert decimals to percentages
  - All 15 sites verified - database now matches CSV files perfectly
  - All data values now correctly <= 1.0 in database (display as 0-100%)
- **2025-11-19**: Fixed fish biomass discrepancies
  - Andulay Winter 24/25: 6.85 → 7.18 kg/150m²
  - Lutoban North Winter 24/25: 5.68 → 5.67 kg/150m²
- **2025-11-19**: Fixed hard coral cover data mismatch for Basak (showed 3.05% instead of 19%). Reimported substrate data to correct all sites.
- **2025-12-15**: Added COVID period data filtering
  - All data queries now exclude dates from April 2020 to March 2022
  - COVID data was inaccurate due to pandemic restrictions affecting monitoring
  - Filter implemented in QueryBuilder (_exclude_covid_filter) for all metric, biomass, and coral cover queries
  - Data still exists in database but is hidden from all visualizations and exports
- **2025-12-15**: Fixed corallivore density display bug
  - Chart generators were incorrectly multiplying corallivore_density by 100 (showed ~4000 instead of ~40 ind/ha)
  - Root cause: Code checked for 'coral' in metric name, which matched 'corallivore_density'
  - Fix: Changed all checks to use 'coral_cover' instead of 'coral' in simple_graph_generator.py, graph_generator.py, and summary_graph_generator.py
  - Only true percentage metrics (hard_coral_cover, soft_coral_cover, algae, bleaching, rubble) are now multiplied by 100