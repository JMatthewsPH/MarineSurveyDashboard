import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import Site, Survey, get_db_session
from .query_builder import QueryBuilder
import streamlit as st
from contextlib import contextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Processes marine conservation data from the database
    
    This class handles data retrieval, transformation, and caching for the 
    Marine Conservation Dashboard. It serves as an intermediary between the
    database and the visualization layer.
    """
    
    def __init__(self, db: Session):
        """Initialize with a database session"""
        self._db = db
        self.query_builder = QueryBuilder()
        logger.info("DataProcessor initialized")

    @property
    def db(self) -> Session:
        """Ensures db session is active"""
        if not self._db.is_active:
            logger.info("Refreshing inactive database session")
            with get_db_session() as new_db:
                self._db = new_db
        return self._db

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_sites(_self):  # Added underscore to ignore self in caching
        """Get all sites with their municipalities"""
        try:
            with get_db_session() as db:
                logger.info("Fetching all sites from database")
                # Use the query builder to get sites
                return QueryBuilder.all_sites(db)
        except Exception as e:
            logger.error(f"Error fetching sites: {str(e)}")
            # Return empty list on error to prevent app crashes
            return []

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_metric_data(_self, site_name: str, metric: str, start_date='2017-01-01'):
        """
        Process data for any metric
        
        Args:
            site_name: Name of the site to fetch data for
            metric: Metric type ('hard_coral', 'fleshy_algae', etc.)
            start_date: Start date for filtering data (YYYY-MM-DD format)
            
        Returns:
            DataFrame with date and metric columns
        """
        logger.info(f"Fetching {metric} data for site: {site_name}")

        # Define metric mapping for column names
        metric_map = {
            'hard_coral': 'hard_coral_cover',
            'fleshy_algae': 'fleshy_macro_algae_cover',
            'bleaching': 'bleaching',
            'herbivore': 'herbivore_density',
            'carnivore': 'carnivore_density',
            'omnivore': 'omnivore_density',
            'corallivore': 'corallivore_density',
            'rubble': 'rubble'
        }

        # Validate metric
        column_name = metric_map.get(metric)
        if not column_name:
            logger.error(f"Invalid metric requested: {metric}")
            return pd.DataFrame(columns=['date', metric])

        try:
            with get_db_session() as db:
                # Get site using query builder
                site = QueryBuilder.site_by_name(db, site_name)
                if not site:
                    logger.warning(f"Site not found: {site_name}")
                    return pd.DataFrame(columns=['date', metric])

                # Get metric data from database
                surveys = QueryBuilder.metric_data(db, site.id, column_name, start_date)

                # Log results
                logger.info(f"Found {len(surveys)} {metric} surveys for {site_name}")
                
                # Process results
                return pd.DataFrame(surveys, columns=['date', metric])
        except Exception as e:
            logger.error(f"Error fetching metric data: {str(e)}")
            # Return empty DataFrame to prevent application crashes
            return pd.DataFrame(columns=['date', metric])

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_average_metric_data(_self, metric: str, exclude_site=None, municipality=None, start_date='2017-01-01'):
        """Calculate average metric data across sites with optional municipality filter"""
        print(f"Calculating average {metric} (excluding {exclude_site}, municipality filter: {municipality})")

        metric_map = {
            'hard_coral': 'hard_coral_cover',
            'fleshy_algae': 'fleshy_macro_algae_cover',
            'bleaching': 'bleaching',
            'herbivore': 'herbivore_density',
            'carnivore': 'carnivore_density',
            'omnivore': 'omnivore_density',
            'corallivore': 'corallivore_density',
            'rubble': 'rubble'
        }

        column_name = metric_map.get(metric)
        if not column_name:
            return pd.DataFrame(columns=['date', metric])

        exclude_site_id = None
        if exclude_site:
            with get_db_session() as db:
                site = db.query(Site).filter(Site.name == exclude_site).first()
                if site:
                    exclude_site_id = site.id

        try:
            with get_db_session() as db:
                # Start with base query
                query = (db.query(
                        Survey.date,
                        func.avg(getattr(Survey, column_name)).label(metric))
                        .join(Site)  # Join with Site table to access municipality
                        .filter(Survey.date >= start_date))

                if exclude_site_id:
                    query = query.filter(Survey.site_id != exclude_site_id)

                if municipality:
                    query = query.filter(Site.municipality == municipality)

                surveys = (query.group_by(Survey.date)
                          .order_by(Survey.date)
                          .all())

                return pd.DataFrame(surveys, columns=['date', metric])
        except Exception as e:
            print(f"Error calculating average metric data: {str(e)}")
            return pd.DataFrame(columns=['date', metric])

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_average_biomass_data(_self, exclude_site=None, municipality=None, start_date='2017-01-01'):
        """Calculate average commercial fish biomass with optional municipality filter"""
        print(f"Calculating average biomass (excluding {exclude_site}, municipality filter: {municipality})")

        exclude_site_id = None
        if exclude_site:
            with get_db_session() as db:
                site = db.query(Site).filter(Site.name == exclude_site).first()
                if site:
                    exclude_site_id = site.id

        try:
            with get_db_session() as db:
                query = (db.query(
                        Survey.date,
                        func.avg(Survey.commercial_biomass).label('Commercial Biomass'))
                        .join(Site)  # Join with Site table
                        .filter(Survey.date >= start_date))

                if exclude_site_id:
                    query = query.filter(Survey.site_id != exclude_site_id)

                if municipality:
                    query = query.filter(Site.municipality == municipality)

                surveys = (query.group_by(Survey.date)
                          .order_by(Survey.date)
                          .all())

                return pd.DataFrame(surveys, columns=['date', 'Commercial Biomass'])
        except Exception as e:
            print(f"Error calculating average biomass data: {str(e)}")
            return pd.DataFrame(columns=['date', 'Commercial Biomass'])

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_average_coral_cover_data(_self, exclude_site=None, municipality=None, start_date='2017-01-01'):
        """Calculate average hard coral cover with optional municipality filter"""
        print(f"Calculating average coral cover (excluding {exclude_site}, municipality filter: {municipality})")

        exclude_site_id = None
        if exclude_site:
            with get_db_session() as db:
                site = db.query(Site).filter(Site.name == exclude_site).first()
                if site:
                    exclude_site_id = site.id

        try:
            with get_db_session() as db:
                query = (db.query(
                        Survey.date,
                        func.avg(Survey.hard_coral_cover).label('Hard Coral Cover'))
                        .join(Site)  # Join with Site table
                        .filter(Survey.date >= start_date))

                if exclude_site_id:
                    query = query.filter(Survey.site_id != exclude_site_id)

                if municipality:
                    query = query.filter(Site.municipality == municipality)

                surveys = (query.group_by(Survey.date)
                          .order_by(Survey.date)
                          .all())

                return pd.DataFrame(surveys, columns=['date', 'Hard Coral Cover'])
        except Exception as e:
            print(f"Error calculating average coral cover data: {str(e)}")
            return pd.DataFrame(columns=['date', 'Hard Coral Cover'])

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_biomass_data(_self, site_name, start_date='2017-01-01'):
        """Process commercial fish biomass data"""
        logger.info(f"Fetching biomass data for site: {site_name}")
        try:
            with get_db_session() as db:
                # Get site using QueryBuilder
                site = QueryBuilder.site_by_name(db, site_name)
                if not site:
                    logger.warning(f"Site not found: {site_name}")
                    return pd.DataFrame(columns=['date', 'Commercial Biomass'])

                # Use specialized biomass query
                surveys = QueryBuilder.biomass_data(db, site.id, start_date)

                logger.info(f"Found {len(surveys)} biomass surveys for {site_name}")
                return pd.DataFrame(surveys, columns=['date', 'Commercial Biomass'])
        except Exception as e:
            logger.error(f"Error fetching biomass data: {str(e)}")
            return pd.DataFrame(columns=['date', 'Commercial Biomass'])

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_coral_cover_data(_self, site_name, start_date='2017-01-01'):
        """Process hard coral cover data"""
        logger.info(f"Fetching coral cover data for site: {site_name}")
        try:
            with get_db_session() as db:
                # Get site using QueryBuilder
                site = QueryBuilder.site_by_name(db, site_name)
                if not site:
                    logger.warning(f"Site not found: {site_name}")
                    return pd.DataFrame(columns=['date', 'Hard Coral Cover'])

                # Use specialized coral cover query
                surveys = QueryBuilder.coral_cover_data(db, site.id, start_date)

                logger.info(f"Found {len(surveys)} coral cover surveys for {site_name}")
                return pd.DataFrame(surveys, columns=['date', 'Hard Coral Cover'])
        except Exception as e:
            logger.error(f"Error fetching coral cover data: {str(e)}")
            return pd.DataFrame(columns=['date', 'Hard Coral Cover'])

    def get_fish_length_data(self, site_name, species, start_date='2017-01-01'):
        """Process fish length data by species"""
        return pd.DataFrame(columns=['date', 'average_length'])

    def get_ecotourism_data(self, site_name, observation_type='percentage'):
        """Process eco-tourism data for the last 365 days"""
        return pd.Series(dtype='float64')
            
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_all_sites_summary_metrics(_self):
        """Get summary statistics for all sites combined"""
        sites = _self.get_sites()
        site_count = len(sites)
        
        all_surveys = []
        for site in sites:
            site_surveys = _self.get_biomass_data(site.name)
            if not site_surveys.empty:
                all_surveys.append(site_surveys)
                
        if not all_surveys:
            return {
                "site_count": site_count,
                "survey_count": 0,
                "start_date": None,
                "end_date": None,
                "avg_survey_frequency": 0,
                "avg_hard_coral": 0,
                "avg_biomass": 0,
                "avg_fleshy_algae": 0,
            }
            
        # Combine all survey data
        combined_data = pd.concat(all_surveys)
        
        # Calculate basic stats
        survey_count = len(combined_data)
        start_date = pd.to_datetime(combined_data['date'].min())
        end_date = pd.to_datetime(combined_data['date'].max())
        date_range = (end_date - start_date).days
        
        # Average survey frequency (surveys per site per year)
        if date_range > 0:
            years = date_range / 365.25
            avg_survey_frequency = survey_count / (site_count * years)
        else:
            avg_survey_frequency = 0
            
        # Calculate average coral cover
        all_coral_data = []
        for site in sites:
            coral_data = _self.get_coral_cover_data(site.name)
            if not coral_data.empty:
                all_coral_data.append(coral_data)
        
        avg_hard_coral = 0
        if all_coral_data:
            combined_coral = pd.concat(all_coral_data)
            avg_hard_coral = combined_coral['Hard Coral Cover'].mean()
            
        # Calculate average commercial fish biomass
        avg_biomass = combined_data['Commercial Biomass'].mean()
        
        # Calculate average fleshy algae
        all_algae_data = []
        for site in sites:
            algae_data = _self.get_metric_data(site.name, 'fleshy_algae')
            if not algae_data.empty:
                all_algae_data.append(algae_data)
                
        avg_fleshy_algae = 0
        if all_algae_data:
            combined_algae = pd.concat(all_algae_data)
            avg_fleshy_algae = combined_algae['fleshy_algae'].mean()
        
        return {
            "site_count": site_count,
            "survey_count": survey_count,
            "start_date": start_date,
            "end_date": end_date,
            "avg_survey_frequency": avg_survey_frequency,
            "avg_hard_coral": avg_hard_coral,
            "avg_biomass": avg_biomass,
            "avg_fleshy_algae": avg_fleshy_algae,
        }
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_site_comparison_matrix(_self):
        """Generate matrix of all sites vs key metrics with latest values"""
        sites = _self.get_sites()
        
        # Create a dataframe with one row per site
        matrix_data = []
        
        for site in sites:
            # Get the latest data for each metric
            biomass_data = _self.get_biomass_data(site.name)
            coral_data = _self.get_coral_cover_data(site.name)
            algae_data = _self.get_metric_data(site.name, 'fleshy_algae')
            herbivore_data = _self.get_metric_data(site.name, 'herbivore')
            omnivore_data = _self.get_metric_data(site.name, 'omnivore')
            corallivore_data = _self.get_metric_data(site.name, 'corallivore')
            
            # Extract the latest values
            latest_biomass = biomass_data['Commercial Biomass'].iloc[-1] if not biomass_data.empty else None
            latest_coral = coral_data['Hard Coral Cover'].iloc[-1] if not coral_data.empty else None
            latest_algae = algae_data['fleshy_algae'].iloc[-1] if not algae_data.empty else None
            latest_herbivore = herbivore_data['herbivore'].iloc[-1] if not herbivore_data.empty else None
            latest_omnivore = omnivore_data['omnivore'].iloc[-1] if not omnivore_data.empty else None
            latest_corallivore = corallivore_data['corallivore'].iloc[-1] if not corallivore_data.empty else None
            
            # Add to matrix
            matrix_data.append({
                'site': site.name,
                'municipality': site.municipality,
                'commercial_biomass': latest_biomass,
                'hard_coral_cover': latest_coral,
                'fleshy_algae_cover': latest_algae,
                'herbivore_density': latest_herbivore,
                'omnivore_density': latest_omnivore,
                'corallivore_density': latest_corallivore
            })
        
        return pd.DataFrame(matrix_data)
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_trend_analysis_data(_self, metric, start_date=None, end_date=None):
        """Get time series data for all sites for specified metric"""
        sites = _self.get_sites()
        
        # Set default dates if not provided
        if start_date is None:
            start_date = '2017-01-01'
        
        # Collect data for each site
        site_data_list = []
        
        for site in sites:
            data = _self.get_metric_data(site.name, metric, start_date)
            
            if not data.empty:
                # Add site name column and filter by date range if specified
                data['site'] = site.name
                data['municipality'] = site.municipality
                
                if end_date:
                    data = data[(data['date'] >= pd.to_datetime(start_date)) & 
                               (data['date'] <= pd.to_datetime(end_date))]
                
                site_data_list.append(data)
        
        # Combine all site data
        if site_data_list:
            return pd.concat(site_data_list)
        else:
            return pd.DataFrame()

    def __del__(self):
        """Ensure database connection is closed"""
        if hasattr(self, '_db'):
            self._db.close()