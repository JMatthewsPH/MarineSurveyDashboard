import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import Site, Survey

class DataProcessor:
    def __init__(self, db: Session):
        self.db = db

    def get_sites(self):
        """Get all sites with their municipalities"""
        return self.db.query(Site).all()

    def get_metric_data(self, site_name: str, metric: str, start_date='2017-01-01'):
        """Process data for any metric"""
        print(f"Fetching {metric} data for site: {site_name}")

        # Map friendly names to database column names
        metric_map = {
            'fleshy_algae': 'fleshy_macro_algae_cover',
            'bleaching': 'bleaching',
            'herbivore': 'herbivore_density',
            'carnivore': 'carnivore_density',
            'omnivore': 'omnivore_density',
            'corallivore': 'corallivore_density'
        }

        column_name = metric_map.get(metric)
        if not column_name:
            print(f"Invalid metric: {metric}")
            return pd.DataFrame(columns=['date', metric])

        site = self.db.query(Site).filter(Site.name == site_name).first()
        if not site:
            print(f"Site not found: {site_name}")
            return pd.DataFrame(columns=['date', metric])

        surveys = (self.db.query(Survey.date, getattr(Survey, column_name))
                  .filter(Survey.site_id == site.id)
                  .filter(Survey.date >= start_date)
                  .order_by(Survey.date)
                  .all())

        print(f"Found {len(surveys)} {metric} surveys for {site_name}")
        return pd.DataFrame(surveys, columns=['date', metric])

    def get_average_metric_data(self, metric: str, exclude_site=None, start_date='2017-01-01'):
        """Calculate average metric data across all sites except the excluded one"""
        print(f"Calculating average {metric} (excluding {exclude_site})")

        metric_map = {
            'fleshy_algae': 'fleshy_macro_algae_cover',
            'bleaching': 'bleaching',
            'herbivore': 'herbivore_density',
            'carnivore': 'carnivore_density',
            'omnivore': 'omnivore_density',
            'corallivore': 'corallivore_density'
        }

        column_name = metric_map.get(metric)
        if not column_name:
            return pd.DataFrame(columns=['date', metric])

        # Get the site to exclude
        exclude_site_id = None
        if exclude_site:
            site = self.db.query(Site).filter(Site.name == exclude_site).first()
            if site:
                exclude_site_id = site.id

        # Query all surveys
        query = (self.db.query(
                Survey.date,
                func.avg(getattr(Survey, column_name)).label(metric))
                .filter(Survey.date >= start_date))

        # Exclude the selected site if specified
        if exclude_site_id:
            query = query.filter(Survey.site_id != exclude_site_id)

        # Group by date and order
        surveys = (query.group_by(Survey.date)
                  .order_by(Survey.date)
                  .all())

        return pd.DataFrame(surveys, columns=['date', metric])

    def get_biomass_data(self, site_name, start_date='2017-01-01'):
        """Process commercial fish biomass data"""
        print(f"Fetching biomass data for site: {site_name}")
        site = self.db.query(Site).filter(Site.name == site_name).first()
        if not site:
            print(f"Site not found: {site_name}")
            return pd.DataFrame(columns=['date', 'Commercial Biomass'])

        surveys = (self.db.query(Survey.date, Survey.commercial_biomass)
                  .filter(Survey.site_id == site.id)
                  .filter(Survey.date >= start_date)
                  .order_by(Survey.date)
                  .all())

        print(f"Found {len(surveys)} biomass surveys for {site_name}")
        return pd.DataFrame(surveys, columns=['date', 'Commercial Biomass'])

    def get_average_biomass_data(self, exclude_site=None, start_date='2017-01-01'):
        """Calculate average commercial fish biomass across all sites except the excluded one"""
        print(f"Calculating average biomass (excluding {exclude_site})")

        # Get the site to exclude
        exclude_site_id = None
        if exclude_site:
            site = self.db.query(Site).filter(Site.name == exclude_site).first()
            if site:
                exclude_site_id = site.id

        # Query all surveys
        query = (self.db.query(
                Survey.date,
                func.avg(Survey.commercial_biomass).label('Commercial Biomass'))
                .filter(Survey.date >= start_date))

        # Exclude the selected site if specified
        if exclude_site_id:
            query = query.filter(Survey.site_id != exclude_site_id)

        # Group by date and order
        surveys = (query.group_by(Survey.date)
                  .order_by(Survey.date)
                  .all())

        return pd.DataFrame(surveys, columns=['date', 'Commercial Biomass'])

    def get_coral_cover_data(self, site_name, start_date='2017-01-01'):
        """Process hard coral cover data"""
        print(f"Fetching coral cover data for site: {site_name}")
        site = self.db.query(Site).filter(Site.name == site_name).first()
        if not site:
            print(f"Site not found: {site_name}")
            return pd.DataFrame(columns=['date', 'Hard Coral Cover'])

        surveys = (self.db.query(Survey.date, Survey.hard_coral_cover)
                  .filter(Survey.site_id == site.id)
                  .filter(Survey.date >= start_date)
                  .order_by(Survey.date)
                  .all())

        print(f"Found {len(surveys)} coral cover surveys for {site_name}")
        return pd.DataFrame(surveys, columns=['date', 'Hard Coral Cover'])

    def get_average_coral_cover_data(self, exclude_site=None, start_date='2017-01-01'):
        """Calculate average hard coral cover across all sites except the excluded one"""
        print(f"Calculating average coral cover (excluding {exclude_site})")

        # Get the site to exclude
        exclude_site_id = None
        if exclude_site:
            site = self.db.query(Site).filter(Site.name == exclude_site).first()
            if site:
                exclude_site_id = site.id

        # Query all surveys
        query = (self.db.query(
                Survey.date,
                func.avg(Survey.hard_coral_cover).label('Hard Coral Cover'))
                .filter(Survey.date >= start_date))

        # Exclude the selected site if specified
        if exclude_site_id:
            query = query.filter(Survey.site_id != exclude_site_id)

        # Group by date and order
        surveys = (query.group_by(Survey.date)
                  .order_by(Survey.date)
                  .all())

        return pd.DataFrame(surveys, columns=['date', 'Hard Coral Cover'])

    def get_fish_length_data(self, site_name, species, start_date='2017-01-01'):
        """Process fish length data by species"""
        return pd.DataFrame(columns=['date', 'average_length'])

    def get_ecotourism_data(self, site_name, observation_type='percentage'):
        """Process eco-tourism data for the last 365 days"""
        return pd.Series(dtype='float64')