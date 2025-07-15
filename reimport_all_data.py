#!/usr/bin/env python3
"""
Reimport all data from CSV files to database
"""

import pandas as pd
import os
from utils.database import get_db_session, Site, Survey
from utils.new_data_importer import SITE_NAME_MAPPING, clean_numeric_value
from datetime import datetime

def parse_period_to_season(period: str) -> str:
    parts = period.strip().split()
    season = parts[0]
    year_part = parts[1]
    
    if '/' in year_part:
        year = int(year_part.split('/')[0])
        if year < 50:
            year += 2000
        else:
            year += 1900
    else:
        year = int(year_part)
    
    season_mapping = {
        'Spring': 'MAR-MAY',
        'Summer': 'JUN-AUG', 
        'Autumn': 'SEP-NOV',
        'Winter': 'DEC-FEB'
    }
    
    if season == 'Winter' and '/' in year_part:
        year = int(year_part.split('/')[1])
        if year < 50:
            year += 2000
        else:
            year += 1900
    
    season_str = season_mapping.get(season, season)
    return f"{season_str} {year}"

def main():
    """Reimport all data from CSV files"""
    print("Starting complete data reimport...")
    
    # Process fish data
    fish_path = "attached_assets/MCP_Data/new_data/fish/seasonal"
    fish_files = [f for f in os.listdir(fish_path) if f.endswith('.csv')]
    
    for i, filename in enumerate(fish_files):
        print(f"Processing fish file {i+1}/{len(fish_files)}: {filename}")
        
        with get_db_session() as db:
            try:
                df = pd.read_csv(os.path.join(fish_path, filename))
                
                site_name_csv = df.iloc[0]['Site']
                site_name_db = SITE_NAME_MAPPING.get(site_name_csv, site_name_csv)
                
                site = db.query(Site).filter(Site.name == site_name_db).first()
                if not site:
                    continue
                
                updates = 0
                for _, row in df.iterrows():
                    try:
                        period = row['Period']
                        season = parse_period_to_season(period)
                        
                        survey = db.query(Survey).filter(
                            Survey.site_id == site.id,
                            Survey.season == season
                        ).first()
                        
                        if not survey:
                            continue
                        
                        # Update with correct CSV column names
                        survey.commercial_biomass = clean_numeric_value(row.get('Commercial Biomass Density'))
                        survey.herbivore_density = clean_numeric_value(row.get('Herbivore Density'))
                        survey.carnivore_density = clean_numeric_value(row.get('Carnivore Density'))
                        survey.omnivore_density = clean_numeric_value(row.get('Omnivore Density'))
                        survey.corallivore_density = clean_numeric_value(row.get('Corallivore Density'))
                        survey.total_density = clean_numeric_value(row.get('Total Density'))
                        survey.commercial_density = clean_numeric_value(row.get('Commercial Density'))
                        
                        updates += 1
                        
                    except Exception as e:
                        print(f"Error processing {site_name_db} {period}: {e}")
                        continue
                
                db.commit()
                print(f"  Updated {updates} fish records for {site_name_db}")
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                db.rollback()
    
    # Process substrate data
    subs_path = "attached_assets/MCP_Data/new_data/subs/seasonal"
    subs_files = [f for f in os.listdir(subs_path) if f.endswith('.csv') and 'BANGCOLUTAN' not in f]
    
    for i, filename in enumerate(subs_files):
        print(f"Processing substrate file {i+1}/{len(subs_files)}: {filename}")
        
        with get_db_session() as db:
            try:
                df = pd.read_csv(os.path.join(subs_path, filename))
                
                site_name_csv = df.iloc[0]['Site']
                site_name_db = SITE_NAME_MAPPING.get(site_name_csv, site_name_csv)
                
                site = db.query(Site).filter(Site.name == site_name_db).first()
                if not site:
                    continue
                
                updates = 0
                for _, row in df.iterrows():
                    try:
                        period = row['Period']
                        season = parse_period_to_season(period)
                        
                        survey = db.query(Survey).filter(
                            Survey.site_id == site.id,
                            Survey.season == season
                        ).first()
                        
                        if not survey:
                            continue
                        
                        # Update substrate data
                        survey.hard_coral_cover = clean_numeric_value(row.get('Hard Coral Cover'))
                        survey.fleshy_macro_algae_cover = clean_numeric_value(row.get('Fresh Algae Cover'))
                        survey.rubble = clean_numeric_value(row.get('Rubble Cover'))
                        survey.bleaching = clean_numeric_value(row.get('Bleaching'))
                        
                        updates += 1
                        
                    except Exception as e:
                        print(f"Error processing {site_name_db} {period}: {e}")
                        continue
                
                db.commit()
                print(f"  Updated {updates} substrate records for {site_name_db}")
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                db.rollback()
    
    print("Complete data reimport finished!")

if __name__ == "__main__":
    main()