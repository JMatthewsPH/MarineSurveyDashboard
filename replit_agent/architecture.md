# Architecture Overview

## 1. Overview

The Marine Conservation Philippines (MCP) Dashboard is a data visualization application designed to monitor and analyze marine protected areas (MPAs) in the Philippines. The application provides interactive dashboards to track key marine conservation metrics such as coral health, fish populations, and ecosystem resilience across different sites.

The system follows a modern web application architecture using Streamlit for the frontend/visualization layer and PostgreSQL for data storage. It's designed to be both user-friendly for conservation stakeholders and scientifically rigorous for researchers.

## 2. System Architecture

The application follows a layered architecture:

1. **Presentation Layer**: Streamlit web interface with interactive dashboards and visualizations
2. **Business Logic Layer**: Data processing and transformation modules written in Python
3. **Data Access Layer**: Database interaction via SQLAlchemy ORM
4. **Storage Layer**: PostgreSQL database storing marine conservation data

### Tech Stack

- **Frontend Framework**: Streamlit
- **Backend Language**: Python 3.11
- **Database**: PostgreSQL 16
- **ORM**: SQLAlchemy
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, Matplotlib
- **PDF Generation**: ReportLab, FPDF
- **Deployment**: Replit hosting with autoscaling

## 3. Key Components

### 3.1. Frontend Components

The application is organized into multiple pages using Streamlit's multi-page app architecture:

- **Home.py**: Landing page with application overview
- **Site_Dashboard.py**: Detailed view of individual marine conservation sites
- **Summary_Dashboard.py**: Aggregated metrics across all sites
- **Live_Data_Explorer.py**: Tool for exploring new survey data formats

### 3.2. Backend Components

The application's backend is organized into utility modules:

#### Data Layer
- **database.py**: Database connection management and ORM model definitions
- **query_builder.py**: SQL query construction and optimization

#### Processing Layer
- **data_processor.py**: Core data transformation and analysis logic
- **data_importer.py**: Import functionality for CSV data files

#### Visualization Layer
- **graph_generator.py**: Creates Plotly visualizations for the dashboards
- **export_utils.py**: Enables exporting of data and visualizations

#### UI Helpers
- **ui_helpers.py**: Streamlit UI component utilities and loading states
- **branding.py**: Consistent branding across the application
- **translations.py**: Internationalization support for multiple languages
- **navigation.py**: Site navigation utilities

### 3.3. Database Schema

The database consists of two primary tables:

1. **sites**: Stores information about marine protected areas
   - id (PK)
   - name
   - municipality
   - image_url
   - description_en (English description)
   - description_fil (Filipino description)

2. **surveys**: Stores survey data collected from each site
   - id (PK)
   - site_id (FK to sites)
   - date
   - hard_coral_cover
   - fleshy_macro_algae_cover
   - bleaching
   - herbivore_density
   - carnivore_density
   - omnivore_density
   - corallivore_density
   - rubble
   - commercial_biomass
   - (and other survey metrics)

## 4. Data Flow

1. **Data Collection**: Marine conservation data is collected by divers using a standardized methodology
2. **Data Import**: Survey data is imported into the system through CSV files or direct database entry
3. **Data Processing**: The `DataProcessor` class transforms raw data into analysis-ready datasets
4. **Visualization**: The `GraphGenerator` creates interactive visualizations from the processed data
5. **User Interaction**: Users interact with the dashboards, selecting sites, metrics, and date ranges
6. **Data Export**: Results can be exported to various formats (CSV, images, PDF reports)

### Key Patterns

- **Caching**: Extensive use of Streamlit's caching to optimize performance for data-heavy operations
- **Lazy Loading**: Database connections are created on-demand and pooled for efficiency
- **Repository Pattern**: `DataProcessor` serves as a repository layer between the UI and database

## 5. External Dependencies

### Core Dependencies
- **streamlit**: Web application framework
- **pandas/numpy**: Data processing and analysis
- **plotly**: Interactive visualizations
- **sqlalchemy**: ORM for database access
- **psycopg2-binary**: PostgreSQL adapter

### Supporting Libraries
- **openai**: Possibly used for AI-assisted data analysis
- **reportlab/fpdf**: PDF report generation
- **matplotlib**: Alternative visualization library
- **twilio**: Likely used for notifications or alerts

## 6. Deployment Strategy

The application is deployed on Replit with the following configuration:

- **Runtime**: Python 3.11 with PostgreSQL 16
- **Deployment Target**: Autoscale (handles varying loads automatically)
- **Entry Point**: `streamlit run Home.py --server.port 5000`
- **Port Configuration**: Internal port 5000 mapped to external port 80

### Deployment Considerations

- The application uses connection pooling with retry mechanisms for database resilience
- Environment variables are used for configuration (e.g., `DATABASE_URL`)
- The application supports SSL mode for secure database connections
- Custom Nix configuration ensures all system dependencies are available

## 7. Design Decisions and Tradeoffs

### Use of Streamlit

**Decision**: Using Streamlit as the primary framework rather than a traditional web framework like Flask/Django with a separate frontend.

**Rationale**: 
- Allows rapid development of data-focused applications
- Simplifies deployment by combining frontend and backend
- Well-suited for scientific and data visualization applications

**Tradeoffs**:
- Less flexible than a separate frontend/backend architecture
- Limited customization of UI components compared to React or Vue
- Higher resource usage compared to lightweight API + SPA approach

### SQLAlchemy ORM

**Decision**: Using SQLAlchemy as an ORM rather than direct SQL queries.

**Rationale**:
- Provides database-agnostic interface
- Simplifies query construction and management
- Handles connection pooling and safety features

**Tradeoffs**:
- Additional overhead compared to raw SQL queries
- Learning curve for complex query optimization

### Data Caching Strategy

**Decision**: Heavy use of caching for database queries and data processing.

**Rationale**:
- Reduces database load for repeated queries
- Improves user experience with faster page loads
- Essential for handling large datasets efficiently

**Tradeoffs**:
- Increased memory usage on the server
- Potential for stale data if not managed carefully
- Added complexity in cache invalidation logic