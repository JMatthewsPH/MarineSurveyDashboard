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