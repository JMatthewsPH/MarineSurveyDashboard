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
    
    # Centralized metric mapping for reuse across methods
    METRIC_MAP = {
        'hard_coral': 'hard_coral_cover',
        'fleshy_algae': 'fleshy_macro_algae_cover',
        'bleaching': 'bleaching',
        'herbivore': 'herbivore_density',
        'carnivore': 'carnivore_density',
        'omnivore': 'omnivore_density',
        'corallivore': 'corallivore_density',
        'rubble': 'rubble'
    }
    
    # Readable display names for metrics
    DISPLAY_NAMES = {
        'hard_coral_cover': 'Hard Coral Cover',
        'fleshy_macro_algae_cover': 'Fleshy Algae Cover',
        'bleaching': 'Bleaching',
        'herbivore_density': 'Herbivore Density',
        'carnivore_density': 'Carnivore Density',
        'omnivore_density': 'Omnivore Density',
        'corallivore_density': 'Corallivore Density',
        'rubble': 'Rubble Cover',
        'commercial_biomass': 'Commercial Biomass'
    }
    
    def __init__(self, db: Session):
        """Initialize with a database session"""
        self._db = db
        logger.info("DataProcessor initialized")

    @property
    def db(self) -> Session:
        """Ensures db session is active"""
        if not self._db.is_active:
            logger.info("Refreshing inactive database session")
            with get_db_session() as new_db:
                self._db = new_db
        return self._db
        
    def _get_session(self):
        """
        Get an active database session, either the existing one or a new one
        
        This is a helper method to ensure we're always using an active session
        with proper error handling and transaction management
        """
        try:
            # Check if we have a valid active session
            if hasattr(self, '_db') and self._db and self._db.is_active:
                try:
                    # Test the connection with a simple query
                    from sqlalchemy import text
                    self._db.execute(text("SELECT 1"))
                    return self._db
                except Exception as conn_err:
                    # Connection error occurred, try to safely roll back any pending transaction
                    logger.warning(f"Database connection error: {conn_err}. Rolling back...")
                    try:
                        self._db.rollback()
                    except Exception:
                        # If rollback fails, just continue with getting a new session
                        pass
                    
                    # Close the problematic connection
                    try:
                        self._db.close()
                    except Exception:
                        pass
                    
                    # Connection is bad, set to None so we'll create a new one
                    self._db = None
            
            # If we reached here, we need a new session
            logger.info("Creating new database session")
            with get_db_session() as db:
                # Store the reference
                self._db = db
                return db
                
        except Exception as e:
            # For any other error, log and create a fresh session
            logger.warning(f"Error managing database session: {e}. Creating new session.")
            with get_db_session() as db:
                self._db = db
                return db

    @st.cache_data(ttl=24*3600, show_spinner=False)  # Cache for 24 hours - site data rarely changes
    def get_sites(_self):  # Added underscore to ignore self in caching
        """Get all sites with their municipalities"""
        try:
            db = _self._get_session()
            logger.info("Fetching all sites from database")
            # Use the query builder to get sites
            sites = QueryBuilder.all_sites(db)
            logger.info(f"Successfully fetched {len(sites)} sites from database")
            return sites
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

        # Use centralized metric mapping
        column_name = DataProcessor.METRIC_MAP.get(metric)
        if not column_name:
            logger.error(f"Invalid metric requested: {metric}")
            return pd.DataFrame(columns=['date', metric])

        try:
            # Use common session management
            db = _self._get_session()
                
            # Get site using query builder
            site = QueryBuilder.site_by_name(db, site_name)
            if not site:
                logger.warning(f"Site not found: {site_name}")
                return pd.DataFrame(columns=['date', metric])

            # Get metric data from database
            surveys = QueryBuilder.metric_data(db, site.id, column_name, start_date)

            # Log results
            logger.info(f"Found {len(surveys)} {metric} surveys for {site_name}")
            
            print(f"DEBUG - Metric name: {_self.DISPLAY_NAMES.get(column_name, metric)}")
            
            # Process results
            return pd.DataFrame(surveys, columns=['date', metric])
        except Exception as e:
            logger.error(f"Error fetching metric data: {str(e)}")
            # Return empty DataFrame to prevent application crashes
            return pd.DataFrame(columns=['date', metric])
            
    @st.cache_data(ttl=3600, show_spinner=False)
    def batch_get_metric_data(_self, site_names: list, metric: str, start_date='2017-01-01'):
        """
        Efficiently fetch metric data for multiple sites in a single database query
        
        Args:
            site_names: List of site names to fetch data for
            metric: Metric type ('hard_coral', 'fleshy_algae', etc.)
            start_date: Start date for filtering data (YYYY-MM-DD format)
            
        Returns:
            Dictionary mapping site names to DataFrames with date and metric columns
        """
        if not site_names:
            return {}
            
        logger.info(f"Batch fetching {metric} data for {len(site_names)} sites")
        
        # Use centralized metric mapping
        column_name = DataProcessor.METRIC_MAP.get(metric)
        if not column_name:
            logger.error(f"Invalid metric requested: {metric}")
            return {site: pd.DataFrame(columns=['date', metric]) for site in site_names}
            
        try:
            # Use common session management
            db = _self._get_session()
            
            # First, get all site IDs in a single query
            site_name_to_id = {}
            site_id_to_name = {}
            
            # Query all sites at once rather than one at a time
            sites = db.query(Site).filter(Site.name.in_(site_names)).all()
            for site in sites:
                site_name_to_id[site.name] = site.id
                site_id_to_name[site.id] = site.name
                
            # Handle case where some sites aren't found
            missing_sites = set(site_names) - set(site_name_to_id.keys())
            if missing_sites:
                logger.warning(f"Sites not found: {missing_sites}")
                
            # Get all site IDs we found
            site_ids = list(site_id_to_name.keys())
            
            # Fetch all metric data in a single query
            results_by_site_id = QueryBuilder.batch_metric_data(
                db, site_ids, column_name, start_date
            )
            
            # Convert results to DataFrames by site name
            results = {}
            for site_id, data in results_by_site_id.items():
                site_name = site_id_to_name[site_id]
                df = pd.DataFrame(data, columns=['date', metric])
                logger.info(f"Found {len(df)} {metric} surveys for {site_name}")
                results[site_name] = df
                
            # Add empty DataFrames for sites with no data
            for site_name in site_names:
                if site_name not in results and site_name in site_name_to_id:
                    logger.info(f"No {metric} surveys found for {site_name}")
                    results[site_name] = pd.DataFrame(columns=['date', metric])
                    
            print(f"DEBUG - Batch loaded {metric} data for {len(results)} sites")
            return results
            
        except Exception as e:
            logger.error(f"Error batch fetching metric data: {str(e)}")
            # Return empty DataFrames to prevent application crashes
            return {site: pd.DataFrame(columns=['date', metric]) for site in site_names}

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_average_metric_data(_self, metric: str, exclude_site=None, municipality=None, start_date='2017-01-01'):
        """Calculate average metric data across sites with optional municipality filter"""
        logger.info(f"Calculating average {metric} (excluding {exclude_site}, municipality filter: {municipality})")

        # Use centralized metric mapping
        column_name = DataProcessor.METRIC_MAP.get(metric)
        if not column_name:
            logger.error(f"Invalid metric requested: {metric}")
            return pd.DataFrame(columns=['date', metric])

        exclude_site_id = None
        if exclude_site:
            try:
                # Use common session management
                db = _self._get_session()
                site = QueryBuilder.site_by_name(db, exclude_site)
                if site:
                    exclude_site_id = site.id
            except Exception as e:
                logger.error(f"Error looking up exclude site: {str(e)}")

        try:
            # Use common session management
            db = _self._get_session()
            
            # Use QueryBuilder's average_metric_data method
            surveys = QueryBuilder.average_metric_data(
                db, column_name, exclude_site_id, municipality, start_date
            )

            logger.info(f"Found {len(surveys)} average {metric} data points")
            
            return pd.DataFrame(surveys, columns=['date', metric])
        except Exception as e:
            logger.error(f"Error calculating average metric data: {str(e)}")
            return pd.DataFrame(columns=['date', metric])

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_average_biomass_data(_self, exclude_site=None, municipality=None, start_date='2017-01-01'):
        """Calculate average commercial fish biomass with optional municipality filter"""
        logger.info(f"Calculating average biomass (excluding {exclude_site}, municipality filter: {municipality})")
        
        # Use the consistent display name from the class constants
        display_name = _self.DISPLAY_NAMES.get('commercial_biomass', 'Commercial Biomass')
        
        exclude_site_id = None
        if exclude_site:
            try:
                # Use common session management
                db = _self._get_session()
                site = QueryBuilder.site_by_name(db, exclude_site)
                if site:
                    exclude_site_id = site.id
            except Exception as e:
                logger.error(f"Error looking up exclude site: {str(e)}")

        try:
            # Use common session management
            db = _self._get_session()
            
            # Use QueryBuilder's average_biomass_data method
            surveys = QueryBuilder.average_biomass_data(
                db, exclude_site_id, municipality, start_date
            )

            logger.info(f"Found {len(surveys)} average biomass data points")
            
            return pd.DataFrame(surveys, columns=['date', display_name])
        except Exception as e:
            logger.error(f"Error calculating average biomass data: {str(e)}")
            return pd.DataFrame(columns=['date', display_name])

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_average_coral_cover_data(_self, exclude_site=None, municipality=None, start_date='2017-01-01'):
        """Calculate average hard coral cover with optional municipality filter"""
        logger.info(f"Calculating average coral cover (excluding {exclude_site}, municipality filter: {municipality})")
        
        # Use the consistent display name from the class constants
        display_name = _self.DISPLAY_NAMES.get('hard_coral_cover', 'Hard Coral Cover')
        
        exclude_site_id = None
        if exclude_site:
            try:
                # Use common session management
                db = _self._get_session()
                site = QueryBuilder.site_by_name(db, exclude_site)
                if site:
                    exclude_site_id = site.id
            except Exception as e:
                logger.error(f"Error looking up exclude site: {str(e)}")
        
        try:
            # Use common session management
            db = _self._get_session()
            
            # Using the column name directly from class constants
            column_name = 'hard_coral_cover'
            
            # Use general average_metric_data from QueryBuilder
            surveys = QueryBuilder.average_metric_data(
                db, column_name, exclude_site_id, municipality, start_date
            )
            
            logger.info(f"Found {len(surveys)} average coral cover data points")
            
            return pd.DataFrame(surveys, columns=['date', display_name])
        except Exception as e:
            logger.error(f"Error calculating average coral cover data: {str(e)}")
            return pd.DataFrame(columns=['date', display_name])

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_biomass_data(_self, site_name, start_date='2017-01-01'):
        """Process commercial fish biomass data"""
        logger.info(f"Fetching biomass data for site: {site_name}")
        
        # Use the consistent display name from the class constants
        display_name = _self.DISPLAY_NAMES.get('commercial_biomass', 'Commercial Biomass')
        
        try:
            # Use common session management
            db = _self._get_session()
                
            # Get site using QueryBuilder
            site = QueryBuilder.site_by_name(db, site_name)
            if not site:
                logger.warning(f"Site not found: {site_name}")
                return pd.DataFrame(columns=['date', display_name])

            # Use specialized biomass query
            surveys = QueryBuilder.biomass_data(db, site.id, start_date)

            logger.info(f"Found {len(surveys)} biomass surveys for {site_name}")
            print(f"DEBUG - Metric name: {display_name}")
            
            return pd.DataFrame(surveys, columns=['date', display_name])
        except Exception as e:
            logger.error(f"Error fetching biomass data: {str(e)}")
            return pd.DataFrame(columns=['date', display_name])
            
    @st.cache_data(ttl=3600, show_spinner=False)
    def batch_get_biomass_data(_self, site_names: list, start_date='2017-01-01'):
        """
        Efficiently fetch biomass data for multiple sites in a single database query
        
        Args:
            site_names: List of site names to fetch data for
            start_date: Start date for filtering data (YYYY-MM-DD format)
            
        Returns:
            Dictionary mapping site names to DataFrames with date and biomass columns
        """
        if not site_names:
            return {}
            
        logger.info(f"Batch fetching biomass data for {len(site_names)} sites")
        
        # Use the consistent display name from the class constants
        display_name = _self.DISPLAY_NAMES.get('commercial_biomass', 'Commercial Biomass')
            
        try:
            # Use common session management
            db = _self._get_session()
            
            # First, get all site IDs in a single query
            site_name_to_id = {}
            site_id_to_name = {}
            
            # Query all sites at once rather than one at a time
            sites = db.query(Site).filter(Site.name.in_(site_names)).all()
            for site in sites:
                site_name_to_id[site.name] = site.id
                site_id_to_name[site.id] = site.name
                
            # Handle case where some sites aren't found
            missing_sites = set(site_names) - set(site_name_to_id.keys())
            if missing_sites:
                logger.warning(f"Sites not found: {missing_sites}")
                
            # Get all site IDs we found
            site_ids = list(site_id_to_name.keys())
            
            # Fetch all biomass data in a single query
            results_by_site_id = QueryBuilder.batch_biomass_data(
                db, site_ids, start_date
            )
            
            # Convert results to DataFrames by site name
            results = {}
            for site_id, data in results_by_site_id.items():
                site_name = site_id_to_name[site_id]
                df = pd.DataFrame(data, columns=['date', display_name])
                logger.info(f"Found {len(df)} biomass surveys for {site_name}")
                results[site_name] = df
                
            # Add empty DataFrames for sites with no data
            for site_name in site_names:
                if site_name not in results and site_name in site_name_to_id:
                    logger.info(f"No biomass surveys found for {site_name}")
                    results[site_name] = pd.DataFrame(columns=['date', display_name])
                    
            print(f"DEBUG - Batch loaded biomass data for {len(results)} sites")
            return results
            
        except Exception as e:
            logger.error(f"Error batch fetching biomass data: {str(e)}")
            # Return empty DataFrames to prevent application crashes
            return {site: pd.DataFrame(columns=['date', display_name]) for site in site_names}

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_coral_cover_data(_self, site_name, start_date='2017-01-01'):
        """Process hard coral cover data"""
        logger.info(f"Fetching coral cover data for site: {site_name}")
        
        # Use the consistent display name from the class constants
        display_name = _self.DISPLAY_NAMES.get('hard_coral_cover', 'Hard Coral Cover')
        
        try:
            # Use common session management
            db = _self._get_session()
                
            # Get site using QueryBuilder
            site = QueryBuilder.site_by_name(db, site_name)
            if not site:
                logger.warning(f"Site not found: {site_name}")
                return pd.DataFrame(columns=['date', display_name])

            # Use specialized coral cover query
            surveys = QueryBuilder.coral_cover_data(db, site.id, start_date)

            logger.info(f"Found {len(surveys)} coral cover surveys for {site_name}")
            print(f"DEBUG - Metric name: {display_name}")
            
            return pd.DataFrame(surveys, columns=['date', display_name])
        except Exception as e:
            logger.error(f"Error fetching coral cover data: {str(e)}")
            return pd.DataFrame(columns=['date', display_name])
            
    @st.cache_data(ttl=3600, show_spinner=False)
    def batch_get_coral_cover_data(_self, site_names: list, start_date='2017-01-01'):
        """
        Efficiently fetch coral cover data for multiple sites in a single database query
        
        Args:
            site_names: List of site names to fetch data for
            start_date: Start date for filtering data (YYYY-MM-DD format)
            
        Returns:
            Dictionary mapping site names to DataFrames with date and coral cover columns
        """
        if not site_names:
            return {}
            
        logger.info(f"Batch fetching coral cover data for {len(site_names)} sites")
        
        # Use the consistent display name from the class constants
        display_name = _self.DISPLAY_NAMES.get('hard_coral_cover', 'Hard Coral Cover')
            
        try:
            # Use common session management
            db = _self._get_session()
            
            # First, get all site IDs in a single query
            site_name_to_id = {}
            site_id_to_name = {}
            
            # Query all sites at once rather than one at a time
            sites = db.query(Site).filter(Site.name.in_(site_names)).all()
            for site in sites:
                site_name_to_id[site.name] = site.id
                site_id_to_name[site.id] = site.name
                
            # Handle case where some sites aren't found
            missing_sites = set(site_names) - set(site_name_to_id.keys())
            if missing_sites:
                logger.warning(f"Sites not found: {missing_sites}")
                
            # Get all site IDs we found
            site_ids = list(site_id_to_name.keys())
            
            # Fetch all coral cover data in a single query
            results_by_site_id = QueryBuilder.batch_coral_cover_data(
                db, site_ids, start_date
            )
            
            # Convert results to DataFrames by site name
            results = {}
            for site_id, data in results_by_site_id.items():
                site_name = site_id_to_name[site_id]
                df = pd.DataFrame(data, columns=['date', display_name])
                logger.info(f"Found {len(df)} coral cover surveys for {site_name}")
                results[site_name] = df
                
            # Add empty DataFrames for sites with no data
            for site_name in site_names:
                if site_name not in results and site_name in site_name_to_id:
                    logger.info(f"No coral cover surveys found for {site_name}")
                    results[site_name] = pd.DataFrame(columns=['date', display_name])
                    
            print(f"DEBUG - Batch loaded coral cover data for {len(results)} sites")
            return results
            
        except Exception as e:
            logger.error(f"Error batch fetching coral cover data: {str(e)}")
            # Return empty DataFrames to prevent application crashes
            return {site: pd.DataFrame(columns=['date', display_name]) for site in site_names}

    def get_fish_length_data(self, site_name, species, start_date='2017-01-01'):
        """Process fish length data by species"""
        return pd.DataFrame(columns=['date', 'average_length'])

    def get_ecotourism_data(self, site_name, observation_type='percentage'):
        """Process eco-tourism data for the last 365 days"""
        return pd.Series(dtype='float64')
            
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_all_sites_summary_metrics(_self):
        """Get summary statistics for all sites combined using optimized batch loading"""
        sites = _self.get_sites()
        site_count = len(sites)
        
        if not sites:
            return {
                "site_count": 0,
                "survey_count": 0,
                "start_date": None,
                "end_date": None,
                "avg_survey_frequency": 0,
                "avg_hard_coral": 0,
                "avg_biomass": 0,
                "avg_fleshy_algae": 0,
            }
        
        # Get site names for batch loading
        site_names = [site.name for site in sites]
        
        # Use batch loading for biomass data
        biomass_data_by_site = _self.batch_get_biomass_data(site_names, start_date='2017-01-01')
        
        # Get the display names for consistency
        biomass_display_name = _self.DISPLAY_NAMES.get('commercial_biomass', 'Commercial Biomass')
        coral_display_name = _self.DISPLAY_NAMES.get('hard_coral_cover', 'Hard Coral Cover')
        
        # Filter out empty dataframes and combine data
        biomass_dfs = [df for df in biomass_data_by_site.values() if not df.empty]
        
        if not biomass_dfs:
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
        combined_biomass_data = pd.concat(biomass_dfs)
        
        # Calculate basic stats
        survey_count = len(combined_biomass_data)
        start_date = pd.to_datetime(combined_biomass_data['date'].min())
        end_date = pd.to_datetime(combined_biomass_data['date'].max())
        date_range = (end_date - start_date).days
        
        # Average survey frequency (surveys per site per year)
        if date_range > 0:
            years = date_range / 365.25
            avg_survey_frequency = survey_count / (site_count * years)
        else:
            avg_survey_frequency = 0
            
        # Batch load coral cover data
        coral_data_by_site = _self.batch_get_coral_cover_data(site_names, start_date='2017-01-01')
        
        # Filter out empty dataframes and combine data
        coral_dfs = [df for df in coral_data_by_site.values() if not df.empty]
        
        avg_hard_coral = 0
        if coral_dfs:
            combined_coral = pd.concat(coral_dfs)
            avg_hard_coral = combined_coral[coral_display_name].mean()
            
        # Calculate average commercial fish biomass
        avg_biomass = combined_biomass_data[biomass_display_name].mean()
        
        # Batch load algae data
        algae_data_by_site = _self.batch_get_metric_data(site_names, 'fleshy_algae', start_date='2017-01-01')
        
        # Filter out empty dataframes and combine data
        algae_dfs = [df for df in algae_data_by_site.values() if not df.empty]
        
        avg_fleshy_algae = 0
        if algae_dfs:
            combined_algae = pd.concat(algae_dfs)
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
        """Generate matrix of all sites vs key metrics with latest values using optimized batch loading"""
        sites = _self.get_sites()
        
        if not sites:
            return pd.DataFrame()
            
        # Get site names for batch loading
        site_names = [site.name for site in sites]
        
        # Create a mapping from site name to municipality for use in the final matrix
        site_municipalities = {site.name: site.municipality for site in sites}
        
        # Use batch loading for all metrics
        biomass_data_by_site = _self.batch_get_biomass_data(site_names, start_date='2017-01-01')
        coral_data_by_site = _self.batch_get_coral_cover_data(site_names, start_date='2017-01-01')
        algae_data_by_site = _self.batch_get_metric_data(site_names, 'fleshy_algae', start_date='2017-01-01')
        herbivore_data_by_site = _self.batch_get_metric_data(site_names, 'herbivore', start_date='2017-01-01')
        omnivore_data_by_site = _self.batch_get_metric_data(site_names, 'omnivore', start_date='2017-01-01')
        corallivore_data_by_site = _self.batch_get_metric_data(site_names, 'corallivore', start_date='2017-01-01')
        
        # Get display names for consistency
        biomass_display_name = _self.DISPLAY_NAMES.get('commercial_biomass', 'Commercial Biomass')
        coral_display_name = _self.DISPLAY_NAMES.get('hard_coral_cover', 'Hard Coral Cover')
        
        # Create a dataframe with one row per site
        matrix_data = []
        
        # Process each site using the batch-loaded data
        for site_name in site_names:
            # Extract the latest values for each metric
            latest_biomass = (
                biomass_data_by_site[site_name][biomass_display_name].iloc[-1] 
                if site_name in biomass_data_by_site and not biomass_data_by_site[site_name].empty 
                else None
            )
            
            latest_coral = (
                coral_data_by_site[site_name][coral_display_name].iloc[-1]
                if site_name in coral_data_by_site and not coral_data_by_site[site_name].empty
                else None
            )
            
            latest_algae = (
                algae_data_by_site[site_name]['fleshy_algae'].iloc[-1]
                if site_name in algae_data_by_site and not algae_data_by_site[site_name].empty
                else None
            )
            
            latest_herbivore = (
                herbivore_data_by_site[site_name]['herbivore'].iloc[-1]
                if site_name in herbivore_data_by_site and not herbivore_data_by_site[site_name].empty
                else None
            )
            
            latest_omnivore = (
                omnivore_data_by_site[site_name]['omnivore'].iloc[-1]
                if site_name in omnivore_data_by_site and not omnivore_data_by_site[site_name].empty
                else None
            )
            
            latest_corallivore = (
                corallivore_data_by_site[site_name]['corallivore'].iloc[-1]
                if site_name in corallivore_data_by_site and not corallivore_data_by_site[site_name].empty
                else None
            )
            
            # Add to matrix
            matrix_data.append({
                'site': site_name,
                'municipality': site_municipalities[site_name],
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
        """Get time series data for all sites for specified metric using optimized batch loading"""
        sites = _self.get_sites()
        
        if not sites:
            return pd.DataFrame()
            
        # Set default dates if not provided
        if start_date is None:
            start_date = '2017-01-01'
            
        # Get site names for batch loading
        site_names = [site.name for site in sites]
        
        # Create a mapping from site name to municipality for use in the final dataset
        site_municipalities = {site.name: site.municipality for site in sites}
        
        # Use batch loading based on the metric type
        if metric == 'biomass':
            data_by_site = _self.batch_get_biomass_data(site_names, start_date=start_date)
            metric_column = _self.DISPLAY_NAMES.get('commercial_biomass', 'Commercial Biomass')
        elif metric == 'hard_coral':
            data_by_site = _self.batch_get_coral_cover_data(site_names, start_date=start_date)
            metric_column = _self.DISPLAY_NAMES.get('hard_coral_cover', 'Hard Coral Cover')
        else:
            data_by_site = _self.batch_get_metric_data(site_names, metric, start_date=start_date)
            metric_column = metric
        
        # Process each site's data and add site/municipality columns
        enhanced_data_frames = []
        
        for site_name, df in data_by_site.items():
            if not df.empty:
                # Make a copy to avoid modifying the cached data
                site_df = df.copy()
                
                # Add site and municipality columns
                site_df['site'] = site_name
                site_df['municipality'] = site_municipalities.get(site_name, '')
                
                # Filter by date range if specified
                if end_date:
                    site_df = site_df[(site_df['date'] >= pd.to_datetime(start_date)) & 
                                     (site_df['date'] <= pd.to_datetime(end_date))]
                
                enhanced_data_frames.append(site_df)
        
        # Combine all site data
        if enhanced_data_frames:
            return pd.concat(enhanced_data_frames)
        else:
            return pd.DataFrame()

    def __del__(self):
        """Ensure database connection is closed and resources are released properly"""
        try:
            if hasattr(self, '_db') and self._db:
                # First try to safely rollback any incomplete transaction
                try:
                    self._db.rollback()
                except Exception as e:
                    logger.warning(f"Error rolling back transaction during cleanup: {e}")
                
                # Then close the connection
                try:
                    self._db.close()
                    logger.info("Database connection closed properly")
                except Exception as e:
                    logger.warning(f"Error closing database connection: {e}")
        except Exception as e:
            logger.error(f"Error in database cleanup: {e}")