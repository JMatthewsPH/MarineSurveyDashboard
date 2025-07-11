#!/usr/bin/env python3
"""
Complete import for substrate and invertebrate data
"""

import pandas as pd
import os
from utils.database import get_db_session, Site, Survey
from utils.new_data_importer import SITE_NAME_MAPPING, clean_numeric_value

def parse_period_to_season(period: str) -> str:
    """Convert period string to season format used in database"""
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

def import_all_missing_data():
    """Import substrate and invertebrate data"""
    print("Importing substrate and invertebrate data...")
    
    substrate_updates = 0
    invert_updates = 0
    
    with get_db_session() as db:
        # Import substrate data
        subs_path = "attached_assets/MCP_Data/new_data/subs/seasonal"
        for filename in os.listdir(subs_path):
            if not filename.endswith('.csv') or 'BANGCOLUTAN' in filename:
                continue
                
            print(f"Processing substrate: {filename}")
            df = pd.read_csv(os.path.join(subs_path, filename))
            
            site_name_csv = df.iloc[0]['Site']
            site_name_db = SITE_NAME_MAPPING.get(site_name_csv, site_name_csv)
            
            site = db.query(Site).filter(Site.name == site_name_db).first()
            if not site:
                continue
            
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
                    if pd.notna(row.get('Hard Coral Cover')):
                        survey.hard_coral_cover = clean_numeric_value(row.get('Hard Coral Cover'))
                        substrate_updates += 1
                    
                    if pd.notna(row.get('Fresh Algae Cover')):
                        survey.fleshy_macro_algae_cover = clean_numeric_value(row.get('Fresh Algae Cover'))
                        substrate_updates += 1
                    
                    if pd.notna(row.get('Rubble Cover')):
                        survey.rubble = clean_numeric_value(row.get('Rubble Cover'))
                        substrate_updates += 1
                    
                    if pd.notna(row.get('Bleaching')):
                        survey.bleaching = clean_numeric_value(row.get('Bleaching'))
                        substrate_updates += 1
                
                except Exception as e:
                    print(f"Error: {e}")
                    continue
        
        # Import invertebrate data  
        inverts_path = "attached_assets/MCP_Data/new_data/inverts/seasonal"
        for filename in os.listdir(inverts_path):
            if not filename.endswith('.csv'):
                continue
                
            print(f"Processing inverts: {filename}")
            df = pd.read_csv(os.path.join(inverts_path, filename))
            
            site_name_csv = df.iloc[0]['Site']
            site_name_db = SITE_NAME_MAPPING.get(site_name_csv, site_name_csv)
            
            site = db.query(Site).filter(Site.name == site_name_db).first()
            if not site:
                continue
            
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
                    
                    # Note: Invertebrate data columns don't directly map to our current schema
                    # This is supplementary data that can be logged
                    invert_total = clean_numeric_value(row.get('Total Density'))
                    if invert_total is not None:
                        invert_updates += 1
                
                except Exception as e:
                    print(f"Error: {e}")
                    continue
        
        # Commit all changes
        db.commit()
        print(f"Import complete: {substrate_updates} substrate updates, {invert_updates} invertebrate records processed")
    
    return substrate_updates, invert_updates

if __name__ == "__main__":
    import_all_missing_data()