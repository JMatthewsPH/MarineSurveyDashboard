import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import Site, Survey
import streamlit as st
from contextlib import contextmanager

class DataProcessor:
    def __init__(self, db: Session):
        self._db = db

    @property
    def db(self) -> Session:
        """Ensures db session is active"""
        if not self._db.is_active:
            self._db = next(get_db()) # Assuming get_db is defined elsewhere and yields database sessions.
        return self._db

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_sites(_self):  # Added underscore to ignore self in caching
        """Get all sites with their municipalities"""
        return _self.db.query(Site).all()

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_metric_data(_self, site_name: str, metric: str, start_date='2017-01-01'):
        """Process data for any metric"""
        print(f"Fetching {metric} data for site: {site_name}")

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
            print(f"Invalid metric: {metric}")
            return pd.DataFrame(columns=['date', metric])

        try:
            site = _self.db.query(Site).filter(Site.name == site_name).first()
            if not site:
                print(f"Site not found: {site_name}")
                return pd.DataFrame(columns=['date', metric])

            surveys = (_self.db.query(Survey.date, getattr(Survey, column_name))
                      .filter(Survey.site_id == site.id)
                      .filter(Survey.date >= start_date)
                      .order_by(Survey.date)
                      .all())

            print(f"Found {len(surveys)} {metric} surveys for {site_name}")
            return pd.DataFrame(surveys, columns=['date', metric])
        except Exception as e:
            print(f"Error fetching metric data: {str(e)}")
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
            site = _self.db.query(Site).filter(Site.name == exclude_site).first()
            if site:
                exclude_site_id = site.id

        try:
            # Start with base query
            query = (_self.db.query(
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
            site = _self.db.query(Site).filter(Site.name == exclude_site).first()
            if site:
                exclude_site_id = site.id

        try:
            query = (_self.db.query(
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
            site = _self.db.query(Site).filter(Site.name == exclude_site).first()
            if site:
                exclude_site_id = site.id

        try:
            query = (_self.db.query(
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
        print(f"Fetching biomass data for site: {site_name}")
        try:
            site = _self.db.query(Site).filter(Site.name == site_name).first()
            if not site:
                print(f"Site not found: {site_name}")
                return pd.DataFrame(columns=['date', 'Commercial Biomass'])

            surveys = (_self.db.query(Survey.date, Survey.commercial_biomass)
                      .filter(Survey.site_id == site.id)
                      .filter(Survey.date >= start_date)
                      .order_by(Survey.date)
                      .all())

            print(f"Found {len(surveys)} biomass surveys for {site_name}")
            return pd.DataFrame(surveys, columns=['date', 'Commercial Biomass'])
        except Exception as e:
            print(f"Error fetching biomass data: {str(e)}")
            return pd.DataFrame(columns=['date', 'Commercial Biomass'])

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_coral_cover_data(_self, site_name, start_date='2017-01-01'):
        """Process hard coral cover data"""
        print(f"Fetching coral cover data for site: {site_name}")
        try:
            site = _self.db.query(Site).filter(Site.name == site_name).first()
            if not site:
                print(f"Site not found: {site_name}")
                return pd.DataFrame(columns=['date', 'Hard Coral Cover'])

            surveys = (_self.db.query(Survey.date, Survey.hard_coral_cover)
                      .filter(Survey.site_id == site.id)
                      .filter(Survey.date >= start_date)
                      .order_by(Survey.date)
                      .all())

            print(f"Found {len(surveys)} coral cover surveys for {site_name}")
            return pd.DataFrame(surveys, columns=['date', 'Hard Coral Cover'])
        except Exception as e:
            print(f"Error fetching coral cover data: {str(e)}")
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