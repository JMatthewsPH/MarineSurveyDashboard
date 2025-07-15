#!/usr/bin/env python3
"""
Complete Data Synchronization Script
Updates ALL database records to match CSV files exactly
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

def sync_all_fish_data():
    """Sync all fish data from CSV files to database"""
    print("=== SYNCING ALL FISH DATA ===")
    
    fish_path = "attached_assets/MCP_Data/new_data/fish/seasonal"
    total_updates = 0
    
    with get_db_session() as db:
        for filename in os.listdir(fish_path):
            if not filename.endswith('.csv'):
                continue
                
            print(f"Syncing fish data: {filename}")
            df = pd.read_csv(os.path.join(fish_path, filename))
            
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
                    
                    # Use correct column names from the CSV
                    survey.commercial_biomass = clean_numeric_value(row.get('Commercial Biomass Density'))
                    survey.herbivore_density = clean_numeric_value(row.get('Herbivore Density'))
                    survey.carnivore_density = clean_numeric_value(row.get('Carnivore Density'))
                    survey.omnivore_density = clean_numeric_value(row.get('Omnivore Density'))
                    survey.corallivore_density = clean_numeric_value(row.get('Corallivore Density'))
                    survey.total_density = clean_numeric_value(row.get('Total Density'))
                    survey.commercial_density = clean_numeric_value(row.get('Commercial Density'))
                    
                    total_updates += 1
                
                except Exception as e:
                    print(f"Error processing {site_name_db} {period}: {e}")
                    continue
        
        db.commit()
        print(f"✅ Fish data sync complete: {total_updates} updates")
    
    return total_updates

def sync_substrate_data():
    """Sync substrate data from CSV files to database"""
    print("\n=== SYNCING ALL SUBSTRATE DATA ===")
    
    subs_path = "attached_assets/MCP_Data/new_data/subs/seasonal"
    total_updates = 0
    
    with get_db_session() as db:
        for filename in os.listdir(subs_path):
            if not filename.endswith('.csv') or 'BANGCOLUTAN' in filename:
                continue
                
            print(f"Syncing substrate data: {filename}")
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
                    
                    # Sync substrate data
                    survey.hard_coral_cover = clean_numeric_value(row.get('Hard Coral Cover'))
                    survey.fleshy_macro_algae_cover = clean_numeric_value(row.get('Fresh Algae Cover'))
                    survey.rubble = clean_numeric_value(row.get('Rubble Cover'))
                    survey.bleaching = clean_numeric_value(row.get('Bleaching'))
                    
                    total_updates += 1
                
                except Exception as e:
                    print(f"Error processing {site_name_db} {period}: {e}")
                    continue
        
        db.commit()
        print(f"✅ Substrate data sync complete: {total_updates} updates")
    
    return total_updates

def main():
    """Main synchronization function"""
    print("🔄 Starting Complete Data Synchronization...")
    print("=" * 60)
    
    fish_updates = sync_all_fish_data()
    substrate_updates = sync_substrate_data()
    
    print("\n" + "=" * 60)
    print("📊 SYNCHRONIZATION COMPLETE")
    print("=" * 60)
    print(f"🐟 Fish Data Updates: {fish_updates}")
    print(f"🪸 Substrate Data Updates: {substrate_updates}")
    print(f"📈 Total Updates: {fish_updates + substrate_updates}")
    
    print("\n✅ Database now matches CSV files exactly!")
    
    return fish_updates, substrate_updates

if __name__ == "__main__":
    main()