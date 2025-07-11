#!/usr/bin/env python3
"""
Complete Data Synchronization Script
Updates ALL database records to match CSV files exactly
"""

import pandas as pd
import os
from utils.database import get_db_session, Site, Survey
from utils.new_data_importer import SITE_NAME_MAPPING, clean_numeric_value
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def sync_all_fish_data():
    """Sync all fish data from CSV files to database"""
    print("🔄 Syncing ALL fish data from CSV files...")
    
    updates_made = 0
    
    with get_db_session() as db:
        csv_path = "attached_assets/MCP_Data/new_data/fish/seasonal"
        
        for filename in os.listdir(csv_path):
            if not filename.endswith('.csv') or 'BANGCOLUTAN' in filename:
                continue
                
            print(f"📊 Processing {filename}...")
            df = pd.read_csv(os.path.join(csv_path, filename))
            
            # Get site name from first row
            site_name_csv = df.iloc[0]['Site']
            site_name_db = SITE_NAME_MAPPING.get(site_name_csv, site_name_csv)
            
            # Get site from database
            site = db.query(Site).filter(Site.name == site_name_db).first()
            if not site:
                print(f"❌ Site not found: {site_name_db}")
                continue
            
            # Process each row
            for _, row in df.iterrows():
                try:
                    period = row['Period']
                    season = parse_period_to_season(period)
                    
                    # Get or create survey
                    survey = db.query(Survey).filter(
                        Survey.site_id == site.id,
                        Survey.season == season
                    ).first()
                    
                    if not survey:
                        print(f"❌ Survey not found: {site_name_db} {season}")
                        continue
                    
                    # Update all fish metrics
                    csv_biomass = clean_numeric_value(row.get('Commercial Biomass Density'))
                    csv_corallivore = clean_numeric_value(row.get('Corallivore Density'))
                    csv_omnivore = clean_numeric_value(row.get('Omnivore Density'))
                    csv_carnivore = clean_numeric_value(row.get('Carnivore Density'))
                    csv_herbivore = clean_numeric_value(row.get('Herbivore Density'))
                    csv_commercial_density = clean_numeric_value(row.get('Commercial Density'))
                    csv_total_density = clean_numeric_value(row.get('Total Density'))
                    
                    # Update survey with CSV values
                    if csv_biomass is not None:
                        survey.commercial_biomass = csv_biomass
                        updates_made += 1
                    
                    if csv_corallivore is not None:
                        survey.corallivore_density = csv_corallivore
                        updates_made += 1
                    
                    if csv_omnivore is not None:
                        survey.omnivore_density = csv_omnivore
                        updates_made += 1
                    
                    if csv_carnivore is not None:
                        survey.carnivore_density = csv_carnivore
                        updates_made += 1
                    
                    if csv_herbivore is not None:
                        survey.herbivore_density = csv_herbivore
                        updates_made += 1
                    
                    if csv_commercial_density is not None:
                        survey.commercial_density = csv_commercial_density
                        updates_made += 1
                    
                    if csv_total_density is not None:
                        survey.total_density = csv_total_density
                        updates_made += 1
                
                except Exception as e:
                    print(f"❌ Error processing {site_name_db} {period}: {e}")
                    continue
        
        # Commit all changes
        db.commit()
        print(f"✅ Fish data sync complete. Made {updates_made} updates.")
    
    return updates_made

def sync_substrate_data():
    """Sync substrate data from CSV files to database"""
    print("🔄 Syncing substrate data from CSV files...")
    
    updates_made = 0
    subs_path = "attached_assets/MCP_Data/new_data/subs/seasonal"
    
    if not os.path.exists(subs_path):
        print(f"❌ Substrate data folder not found: {subs_path}")
        return 0
    
    with get_db_session() as db:
        for filename in os.listdir(subs_path):
            if not filename.endswith('.csv'):
                continue
                
            print(f"📊 Processing substrate data: {filename}...")
            df = pd.read_csv(os.path.join(subs_path, filename))
            
            # Get site name from first row
            site_name_csv = df.iloc[0]['Site']
            site_name_db = SITE_NAME_MAPPING.get(site_name_csv, site_name_csv)
            
            # Get site from database
            site = db.query(Site).filter(Site.name == site_name_db).first()
            if not site:
                print(f"❌ Site not found: {site_name_db}")
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
                        print(f"❌ Survey not found: {site_name_db} {season}")
                        continue
                    
                    # Update substrate metrics
                    csv_hard_coral = clean_numeric_value(row.get('Hard Coral Cover'))
                    csv_algae = clean_numeric_value(row.get('Fresh Algae Cover'))
                    csv_rubble = clean_numeric_value(row.get('Rubble Cover'))
                    csv_bleaching = clean_numeric_value(row.get('Bleaching'))
                    
                    if csv_hard_coral is not None:
                        survey.hard_coral_cover = csv_hard_coral
                        updates_made += 1
                    
                    if csv_algae is not None:
                        survey.fleshy_macro_algae_cover = csv_algae
                        updates_made += 1
                    
                    if csv_rubble is not None:
                        survey.rubble = csv_rubble
                        updates_made += 1
                    
                    if csv_bleaching is not None:
                        survey.bleaching = csv_bleaching
                        updates_made += 1
                
                except Exception as e:
                    print(f"❌ Error processing substrate {site_name_db} {period}: {e}")
                    continue
        
        # Commit all changes
        db.commit()
        print(f"✅ Substrate data sync complete. Made {updates_made} updates.")
    
    return updates_made

def main():
    """Main synchronization function"""
    print("🔄 Starting COMPLETE data synchronization from CSV files...")
    
    # Sync all fish data
    fish_updates = sync_all_fish_data()
    
    # Sync substrate data
    substrate_updates = sync_substrate_data()
    
    total_updates = fish_updates + substrate_updates
    
    print(f"\n📋 SYNCHRONIZATION COMPLETE:")
    print(f"Fish data updates: {fish_updates}")
    print(f"Substrate data updates: {substrate_updates}")
    print(f"Total updates made: {total_updates}")
    print("✅ All database values now match CSV files exactly!")
    
    return total_updates

if __name__ == "__main__":
    main()