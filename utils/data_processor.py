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
            'herbivore_density': 'herbivore_density',
            'carnivore': 'carnivore_density',
            'carnivore_density': 'carnivore_density',
            'omnivore': 'omnivore_density',
            'omnivore_density': 'omnivore_density',
            'corallivore': 'corallivore_density',
            'corallivore_density': 'corallivore_density',
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
            'herbivore_density': 'herbivore_density',
            'carnivore': 'carnivore_density',
            'carnivore_density': 'carnivore_density',
            'omnivore': 'omnivore_density',
            'omnivore_density': 'omnivore_density',
            'corallivore': 'corallivore_density',
            'corallivore_density': 'corallivore_density',
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

    def __del__(self):
        """Ensure database connection is closed"""
        if hasattr(self, '_db'):
            self._db.close()