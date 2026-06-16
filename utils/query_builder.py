"""
Query Builder Module - Provides optimized database query construction

This module separates database query logic from the data processing layer, 
improving code organization and maintainability.
"""

from datetime import datetime
from sqlalchemy import func, and_, not_
from sqlalchemy.orm import Session
from .database import Site, Survey

COVID_START = datetime(2020, 4, 1)
COVID_END = datetime(2022, 3, 1)

class QueryBuilder:
    """
    Builds optimized database queries for marine conservation data
    
    This class centralizes all query construction logic, making it easier
    to maintain and optimize database access patterns.
    """
    
    @staticmethod
    def _exclude_covid_filter():
        """Returns a filter to exclude COVID period data (April 2020 - March 2022)"""
        return not_(and_(Survey.date >= COVID_START, Survey.date < COVID_END))
    
    @staticmethod
    def site_by_name(db: Session, site_name: str):
        """Get a site by name with query optimization"""
        return db.query(Site).filter(Site.name == site_name).first()
    
    @staticmethod
    def all_sites(db: Session):
        """Get all sites with eager loading of related data"""
        return db.query(Site).all()
    
    @staticmethod
    def metric_data(db: Session, site_id: int, column_name: str, start_date: str):
        """Build a query for metric data with time range filtering and statistical columns"""
        stat_columns = [
            getattr(Survey, column_name),
            getattr(Survey, f"{column_name}_n", None),
            getattr(Survey, f"{column_name}_sd", None),
            getattr(Survey, f"{column_name}_ci_low", None),
            getattr(Survey, f"{column_name}_ci_high", None),
            getattr(Survey, f"{column_name}_eb_low", None),
            getattr(Survey, f"{column_name}_eb_high", None)
        ]
        stat_columns = [col for col in stat_columns if col is not None]
        
        return (db.query(Survey.date, Survey.season, *stat_columns)
                .filter(Survey.site_id == site_id)
                .filter(Survey.date >= start_date)
                .filter(QueryBuilder._exclude_covid_filter())
                .order_by(Survey.date)
                .all())
                
    @staticmethod
    def batch_metric_data(db: Session, site_ids: list, column_name: str, start_date: str):
        """
        Build an optimized query to fetch metric data for multiple sites at once
        
        Args:
            db: Database session
            site_ids: List of site IDs to fetch data for
            column_name: Name of the metric column
            start_date: Start date for filtering (YYYY-MM-DD)
            
        Returns:
            Dictionary mapping site_id to list of tuples with (date, season, value, n, sd, ci_low, ci_high, eb_low, eb_high)
        """
        if not site_ids:
            return {}
        
        # Build list of statistical columns
        stat_columns = [
            getattr(Survey, column_name),
            getattr(Survey, f"{column_name}_n", None),
            getattr(Survey, f"{column_name}_sd", None),
            getattr(Survey, f"{column_name}_ci_low", None),
            getattr(Survey, f"{column_name}_ci_high", None),
            getattr(Survey, f"{column_name}_eb_low", None),
            getattr(Survey, f"{column_name}_eb_high", None)
        ]
        stat_columns = [col for col in stat_columns if col is not None]
            
        # Fetch all matching data in a single query
        query_results = (db.query(
                Survey.site_id, 
                Survey.date,
                Survey.season,
                *stat_columns)
            .filter(Survey.site_id.in_(site_ids))
            .filter(Survey.date >= start_date)
            .filter(QueryBuilder._exclude_covid_filter())
            .order_by(Survey.site_id, Survey.date)
            .all())
            
        # Organize results by site_id
        results_by_site = {}
        for row in query_results:
            site_id = row[0]
            if site_id not in results_by_site:
                results_by_site[site_id] = []
            results_by_site[site_id].append(row[1:])
            
        return results_by_site
    
    @staticmethod
    def average_metric_data(db: Session, column_name: str, exclude_site_id=None, 
                           municipality=None, start_date=None):
        """Build a query for average metric data across sites"""
        # Start with base query
        query = (db.query(
                Survey.date,
                func.avg(getattr(Survey, column_name)).label('average'))
                .join(Site))  # Join with Site table to access municipality
        
        # Apply filters conditionally
        if start_date:
            query = query.filter(Survey.date >= start_date)
            
        if exclude_site_id:
            query = query.filter(Survey.site_id != exclude_site_id)
            
        if municipality:
            query = query.filter(Site.municipality == municipality)
            
        # Apply COVID filter and group/order results
        query = query.filter(QueryBuilder._exclude_covid_filter())
        return (query.group_by(Survey.date)
                .order_by(Survey.date)
                .all())
                
    @staticmethod
    def biomass_data(db: Session, site_id: int, start_date: str):
        """Specialized query for biomass data with statistical columns"""
        return (db.query(
                Survey.date,
                Survey.season,
                Survey.commercial_biomass,
                Survey.commercial_biomass_n,
                Survey.commercial_biomass_sd,
                Survey.commercial_biomass_ci_low,
                Survey.commercial_biomass_ci_high,
                Survey.commercial_biomass_eb_low,
                Survey.commercial_biomass_eb_high)
                .filter(Survey.site_id == site_id)
                .filter(Survey.date >= start_date)
                .filter(QueryBuilder._exclude_covid_filter())
                .order_by(Survey.date)
                .all())
                
    @staticmethod
    def batch_biomass_data(db: Session, site_ids: list, start_date: str):
        """
        Build an optimized query to fetch biomass data for multiple sites at once
        
        Args:
            db: Database session
            site_ids: List of site IDs to fetch data for
            start_date: Start date for filtering (YYYY-MM-DD)
            
        Returns:
            Dictionary mapping site_id to list of tuples with (date, season, value, n, sd, ci_low, ci_high, eb_low, eb_high)
        """
        if not site_ids:
            return {}
            
        # Fetch all matching data in a single query
        query_results = (db.query(
                Survey.site_id, 
                Survey.date,
                Survey.season,
                Survey.commercial_biomass,
                Survey.commercial_biomass_n,
                Survey.commercial_biomass_sd,
                Survey.commercial_biomass_ci_low,
                Survey.commercial_biomass_ci_high,
                Survey.commercial_biomass_eb_low,
                Survey.commercial_biomass_eb_high)
            .filter(Survey.site_id.in_(site_ids))
            .filter(Survey.date >= start_date)
            .filter(QueryBuilder._exclude_covid_filter())
            .order_by(Survey.site_id, Survey.date)
            .all())
            
        # Organize results by site_id
        results_by_site = {}
        for row in query_results:
            site_id = row[0]
            if site_id not in results_by_site:
                results_by_site[site_id] = []
            results_by_site[site_id].append(row[1:])
            
        return results_by_site
                
    @staticmethod
    def coral_cover_data(db: Session, site_id: int, start_date: str):
        """Specialized query for coral cover data with statistical columns"""
        return (db.query(
                Survey.date,
                Survey.season,
                Survey.hard_coral_cover,
                Survey.hard_coral_cover_n,
                Survey.hard_coral_cover_sd,
                Survey.hard_coral_cover_ci_low,
                Survey.hard_coral_cover_ci_high,
                Survey.hard_coral_cover_eb_low,
                Survey.hard_coral_cover_eb_high)
                .filter(Survey.site_id == site_id)
                .filter(Survey.date >= start_date)
                .filter(QueryBuilder._exclude_covid_filter())
                .order_by(Survey.date)
                .all())
                
    @staticmethod
    def batch_coral_cover_data(db: Session, site_ids: list, start_date: str):
        """
        Build an optimized query to fetch coral cover data for multiple sites at once
        
        Args:
            db: Database session
            site_ids: List of site IDs to fetch data for
            start_date: Start date for filtering (YYYY-MM-DD)
            
        Returns:
            Dictionary mapping site_id to list of tuples with (date, season, value, n, sd, ci_low, ci_high, eb_low, eb_high)
        """
        if not site_ids:
            return {}
            
        # Fetch all matching data in a single query
        query_results = (db.query(
                Survey.site_id, 
                Survey.date,
                Survey.season,
                Survey.hard_coral_cover,
                Survey.hard_coral_cover_n,
                Survey.hard_coral_cover_sd,
                Survey.hard_coral_cover_ci_low,
                Survey.hard_coral_cover_ci_high,
                Survey.hard_coral_cover_eb_low,
                Survey.hard_coral_cover_eb_high)
            .filter(Survey.site_id.in_(site_ids))
            .filter(Survey.date >= start_date)
            .filter(QueryBuilder._exclude_covid_filter())
            .order_by(Survey.site_id, Survey.date)
            .all())
            
        # Organize results by site_id
        results_by_site = {}
        for row in query_results:
            site_id = row[0]
            if site_id not in results_by_site:
                results_by_site[site_id] = []
            results_by_site[site_id].append(row[1:])
            
        return results_by_site
                
    @staticmethod
    def average_biomass_data(db: Session, exclude_site_id=None, 
                            municipality=None, start_date=None):
        """Specialized query for average biomass data"""
        query = (db.query(
                Survey.date,
                func.min(Survey.season).label('season'),
                func.avg(Survey.commercial_biomass).label('average'),
                func.avg(Survey.commercial_biomass_n).label('n'),
                func.avg(Survey.commercial_biomass_sd).label('sd'),
                func.avg(Survey.commercial_biomass_ci_low).label('ci_low'),
                func.avg(Survey.commercial_biomass_ci_high).label('ci_high'),
                func.avg(Survey.commercial_biomass_eb_low).label('eb_low'),
                func.avg(Survey.commercial_biomass_eb_high).label('eb_high'))
                .join(Site))
                
        if start_date:
            query = query.filter(Survey.date >= start_date)
            
        if exclude_site_id:
            query = query.filter(Survey.site_id != exclude_site_id)
            
        if municipality:
            query = query.filter(Site.municipality == municipality)
        
        # Apply COVID filter
        query = query.filter(QueryBuilder._exclude_covid_filter())
            
        return (query.group_by(Survey.date)
                .order_by(Survey.date)
                .all())