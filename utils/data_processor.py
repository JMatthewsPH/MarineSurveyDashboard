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

    def get_biomass_data(self, site_name, start_date='2017-01-01'):
        """Process commercial fish biomass data"""
        site = self.db.query(Site).filter(Site.name == site_name).first()
        if not site:
            return pd.DataFrame(columns=['date', 'Commercial Biomass'])

        surveys = (self.db.query(Survey.date, Survey.commercial_biomass)
                  .filter(Survey.site_id == site.id)
                  .filter(Survey.date >= start_date)
                  .order_by(Survey.date)
                  .all())

        return pd.DataFrame(surveys, columns=['date', 'Commercial Biomass'])

    def get_coral_cover_data(self, site_name, start_date='2017-01-01'):
        """Process hard coral cover data"""
        site = self.db.query(Site).filter(Site.name == site_name).first()
        if not site:
            return pd.DataFrame(columns=['date', 'Hard Coral Cover'])

        surveys = (self.db.query(Survey.date, Survey.hard_coral_cover)
                  .filter(Survey.site_id == site.id)
                  .filter(Survey.date >= start_date)
                  .order_by(Survey.date)
                  .all())

        return pd.DataFrame(surveys, columns=['date', 'Hard Coral Cover'])

    def get_fish_length_data(self, site_name, species, start_date='2017-01-01'):
        """Process fish length data by species"""
        # Note: This will need to be updated when fish species data is added
        return pd.DataFrame(columns=['date', 'average_length'])

    def get_ecotourism_data(self, site_name, observation_type='percentage'):
        """Process eco-tourism data for the last 365 days"""
        # Note: This will need to be updated when eco-tourism data is added
        return pd.Series(dtype='float64')