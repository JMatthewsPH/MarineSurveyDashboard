#!/usr/bin/env python3
"""
Import substrate data from CSV files
"""

import pandas as pd
import os
from utils.database import get_db_session, Site, Survey
from utils.new_data_importer import SITE_NAME_MAPPING, clean_numeric_value
import logging

def parse_period_to_season(period: str) -> str:
    """Convert period string to season format used in database"""
    parts = period.strip().split()
    season = parts[0]
    year_part = parts[1]
    
    # Handle different year formats
    if '/' in year_part:
        year = int(year_part.split('/')[0])
        if year < 50:
            year += 2000
        else:
            year += 1900
    else:
        year = int(year_part)
    
    # Map seasons to database format
    season_mapping = {
        'Spring': 'MAR-MAY',
        'Summer': 'JUN-AUG', 
        'Autumn': 'SEP-NOV',
        'Winter': 'DEC-FEB'
    }
    
    # For winter, if the format is "Winter 24/25", use the second year
    if season == 'Winter' and '/' in year_part:
        year = int(year_part.split('/')[1])
        if year < 50:
            year += 2000
        else:
            year += 1900
    
    season_str = season_mapping.get(season, season)
    return f"{season_str} {year}"

def import_substrate_data():
    """Import substrate data from CSV files"""
    print("Importing substrate data...")
    
    updates_made = 0
    subs_path = "attached_assets/MCP_Data/new_data/subs/seasonal"
    
    with get_db_session() as db:
        for filename in os.listdir(subs_path):
            if not filename.endswith('.csv') or 'BANGCOLUTAN' in filename:
                continue
                
            print(f"Processing substrate file: {filename}")
            df = pd.read_csv(os.path.join(subs_path, filename))
            
            # Get site name from first row
            site_name_csv = df.iloc[0]['Site']
            site_name_db = SITE_NAME_MAPPING.get(site_name_csv, site_name_csv)
            
            # Get site from database
            site = db.query(Site).filter(Site.name == site_name_db).first()
            if not site:
                print(f"Site not found: {site_name_db}")
                continue
            
            # Process each row
            for _, row in df.iterrows():
                try:
                    period = row['Period']
                    season = parse_period_to_season(period)
                    
                    # Get survey
                    survey = db.query(Survey).filter(
                        Survey.site_id == site.id,
                        Survey.season == season
                    ).first()
                    
                    if not survey:
                        print(f"Survey not found: {site_name_db} {season}")
                        continue
                    
                    # Update substrate metrics
                    hard_coral = clean_numeric_value(row.get('Hard Coral Cover'))
                    algae = clean_numeric_value(row.get('Fresh Algae Cover'))
                    rubble = clean_numeric_value(row.get('Rubble Cover'))
                    bleaching = clean_numeric_value(row.get('Bleaching'))
                    
                    if hard_coral is not None:
                        survey.hard_coral_cover = hard_coral
                        updates_made += 1
                    
                    if algae is not None:
                        survey.fleshy_macro_algae_cover = algae
                        updates_made += 1
                    
                    if rubble is not None:
                        survey.rubble = rubble
                        updates_made += 1
                    
                    if bleaching is not None:
                        survey.bleaching = bleaching
                        updates_made += 1
                
                except Exception as e:
                    print(f"Error processing {site_name_db} {period}: {e}")
                    continue
        
        # Commit all changes
        db.commit()
        print(f"Substrate data import complete. Made {updates_made} updates.")
    
    return updates_made

if __name__ == "__main__":
    import_substrate_data()