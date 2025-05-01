"""
Query Builder Module - Provides optimized database query construction

This module separates database query logic from the data processing layer, 
improving code organization and maintainability.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session
from .database import Site, Survey

class QueryBuilder:
    """
    Builds optimized database queries for marine conservation data
    
    This class centralizes all query construction logic, making it easier
    to maintain and optimize database access patterns.
    """
    
    @staticmethod
    def site_by_name(db: Session, site_name: str):
        """Get a site by name with query optimization"""
        return db.query(Site).filter(Site.name == site_name).first()
    
    @staticmethod
    def all_sites(db: Session):
        """Get all sites with eager loading of related data
        
        Returns:
            List of dictionaries containing site data (serializable)
        """
        # Get site objects from the database
        sites = db.query(Site).all()
        
        # Convert to serializable dictionaries
        serializable_sites = []
        for site in sites:
            serializable_sites.append({
                'id': site.id,
                'name': site.name,
                'municipality': site.municipality,
                'image_url': site.image_url,
                'description_en': site.description_en,
                'description_fil': site.description_fil
            })
            
        return serializable_sites
    
    @staticmethod
    def metric_data(db: Session, site_id: int, column_name: str, start_date: str):
        """Build a query for metric data with time range filtering"""
        return (db.query(Survey.date, getattr(Survey, column_name))
                .filter(Survey.site_id == site_id)
                .filter(Survey.date >= start_date)
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
            Dictionary mapping site_id to list of (date, value) tuples
        """
        if not site_ids:
            return {}
            
        # Fetch all matching data in a single query
        query_results = (db.query(
                Survey.site_id, 
                Survey.date, 
                getattr(Survey, column_name))
            .filter(Survey.site_id.in_(site_ids))
            .filter(Survey.date >= start_date)
            .order_by(Survey.site_id, Survey.date)
            .all())
            
        # Organize results by site_id
        results_by_site = {}
        for site_id, date, value in query_results:
            if site_id not in results_by_site:
                results_by_site[site_id] = []
            results_by_site[site_id].append((date, value))
            
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
            
        # Group and order results
        return (query.group_by(Survey.date)
                .order_by(Survey.date)
                .all())
                
    @staticmethod
    def biomass_data(db: Session, site_id: int, start_date: str):
        """Specialized query for biomass data"""
        return (db.query(Survey.date, Survey.commercial_biomass)
                .filter(Survey.site_id == site_id)
                .filter(Survey.date >= start_date)
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
            Dictionary mapping site_id to list of (date, value) tuples
        """
        if not site_ids:
            return {}
            
        # Fetch all matching data in a single query
        query_results = (db.query(
                Survey.site_id, 
                Survey.date, 
                Survey.commercial_biomass)
            .filter(Survey.site_id.in_(site_ids))
            .filter(Survey.date >= start_date)
            .order_by(Survey.site_id, Survey.date)
            .all())
            
        # Organize results by site_id
        results_by_site = {}
        for site_id, date, value in query_results:
            if site_id not in results_by_site:
                results_by_site[site_id] = []
            results_by_site[site_id].append((date, value))
            
        return results_by_site
                
    @staticmethod
    def coral_cover_data(db: Session, site_id: int, start_date: str):
        """Specialized query for coral cover data"""
        return (db.query(Survey.date, Survey.hard_coral_cover)
                .filter(Survey.site_id == site_id)
                .filter(Survey.date >= start_date)
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
            Dictionary mapping site_id to list of (date, value) tuples
        """
        if not site_ids:
            return {}
            
        # Fetch all matching data in a single query
        query_results = (db.query(
                Survey.site_id, 
                Survey.date, 
                Survey.hard_coral_cover)
            .filter(Survey.site_id.in_(site_ids))
            .filter(Survey.date >= start_date)
            .order_by(Survey.site_id, Survey.date)
            .all())
            
        # Organize results by site_id
        results_by_site = {}
        for site_id, date, value in query_results:
            if site_id not in results_by_site:
                results_by_site[site_id] = []
            results_by_site[site_id].append((date, value))
            
        return results_by_site
                
    @staticmethod
    def average_biomass_data(db: Session, exclude_site_id=None, 
                            municipality=None, start_date=None):
        """Specialized query for average biomass data"""
        query = (db.query(
                Survey.date,
                func.avg(Survey.commercial_biomass).label('average'))
                .join(Site))
                
        if start_date:
            query = query.filter(Survey.date >= start_date)
            
        if exclude_site_id:
            query = query.filter(Survey.site_id != exclude_site_id)
            
        if municipality:
            query = query.filter(Site.municipality == municipality)
            
        return (query.group_by(Survey.date)
                .order_by(Survey.date)
                .all())