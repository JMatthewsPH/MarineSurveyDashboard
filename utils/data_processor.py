import pandas as pd
from datetime import datetime, timedelta

class DataProcessor:
    def __init__(self, data):
        self.data = pd.DataFrame(data)
        
    def get_biomass_data(self, site_id, start_date='2017-01-01'):
        """Process commercial fish biomass data"""
        df = self.data[self.data['site_id'] == site_id].copy()
        df['date'] = pd.to_datetime(df['date'])
        return df[['date', 'Commercial Biomass']].sort_values('date')
    
    def get_coral_cover_data(self, site_id, start_date='2017-01-01'):
        """Process hard coral cover data"""
        df = self.data[self.data['site_id'] == site_id].copy()
        df['date'] = pd.to_datetime(df['date'])
        return df[['date', 'Hard Coral Cover']].sort_values('date')
    
    def get_fish_length_data(self, site_id, species, start_date='2017-01-01'):
        """Process fish length data by species"""
        df = self.data[
            (self.data['site_id'] == site_id) & 
            (self.data['species'] == species)
        ].copy()
        df['date'] = pd.to_datetime(df['date'])
        return df[['date', 'average_length']].sort_values('date')
    
    def get_ecotourism_data(self, site_id, observation_type='percentage'):
        """Process eco-tourism data for the last 365 days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        df = self.data[
            (self.data['site_id'] == site_id) &
            (self.data['date'] >= start_date)
        ].copy()
        
        if observation_type == 'percentage':
            return df.groupby('species')['observed'].mean() * 100
        else:
            return df.groupby('species')['count'].mean()
