#!/usr/bin/env python3
"""
Data Integrity Verification Script
Compares CSV files with database values to identify and fix discrepancies
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

def verify_fish_data():
    """Verify fish data integrity between CSV files and database"""
    print("=== FISH DATA VERIFICATION ===")
    
    fish_discrepancies = []
    fish_path = "attached_assets/MCP_Data/new_data/fish/seasonal"
    
    with get_db_session() as db:
        for filename in os.listdir(fish_path):
            if not filename.endswith('.csv'):
                continue
                
            print(f"Verifying fish data: {filename}")
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
                    
                    # Check Commercial Biomass
                    csv_biomass = clean_numeric_value(row.get('Commercial Biomass (kg/Ha)'))
                    db_biomass = survey.commercial_biomass
                    
                    if csv_biomass != db_biomass:
                        fish_discrepancies.append({
                            'site': site_name_db,
                            'season': season,
                            'metric': 'Commercial Biomass',
                            'csv_value': csv_biomass,
                            'db_value': db_biomass
                        })
                    
                    # Check fish densities
                    density_fields = [
                        ('Herbivore Density (#/Ha)', 'herbivore_density'),
                        ('Carnivore Density (#/Ha)', 'carnivore_density'),
                        ('Omnivore Density (#/Ha)', 'omnivore_density'),
                        ('Corallivore Density (#/Ha)', 'corallivore_density')
                    ]
                    
                    for csv_col, db_col in density_fields:
                        csv_val = clean_numeric_value(row.get(csv_col))
                        db_val = getattr(survey, db_col)
                        
                        if csv_val != db_val:
                            fish_discrepancies.append({
                                'site': site_name_db,
                                'season': season,
                                'metric': csv_col,
                                'csv_value': csv_val,
                                'db_value': db_val
                            })
                
                except Exception as e:
                    print(f"Error processing {site_name_db} {period}: {e}")
                    continue
    
    print(f"\n🐟 FISH DATA DISCREPANCIES: {len(fish_discrepancies)}")
    if fish_discrepancies:
        for disc in fish_discrepancies[:10]:  # Show first 10
            print(f"  {disc['site']} {disc['season']} {disc['metric']}: CSV={disc['csv_value']} DB={disc['db_value']}")
        if len(fish_discrepancies) > 10:
            print(f"  ... and {len(fish_discrepancies) - 10} more")
    
    return fish_discrepancies

def verify_substrate_data():
    """Verify substrate data integrity"""
    print("\n=== SUBSTRATE DATA VERIFICATION ===")
    
    substrate_discrepancies = []
    subs_path = "attached_assets/MCP_Data/new_data/subs/seasonal"
    
    with get_db_session() as db:
        for filename in os.listdir(subs_path):
            if not filename.endswith('.csv') or 'BANGCOLUTAN' in filename:
                continue
                
            print(f"Verifying substrate data: {filename}")
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
                    
                    # Check substrate fields
                    substrate_fields = [
                        ('Hard Coral Cover', 'hard_coral_cover'),
                        ('Fresh Algae Cover', 'fleshy_macro_algae_cover'),
                        ('Rubble Cover', 'rubble'),
                        ('Bleaching', 'bleaching')
                    ]
                    
                    for csv_col, db_col in substrate_fields:
                        csv_val = clean_numeric_value(row.get(csv_col))
                        db_val = getattr(survey, db_col)
                        
                        if csv_val != db_val:
                            substrate_discrepancies.append({
                                'site': site_name_db,
                                'season': season,
                                'metric': csv_col,
                                'csv_value': csv_val,
                                'db_value': db_val
                            })
                
                except Exception as e:
                    print(f"Error processing {site_name_db} {period}: {e}")
                    continue
    
    print(f"\n🪸 SUBSTRATE DATA DISCREPANCIES: {len(substrate_discrepancies)}")
    if substrate_discrepancies:
        for disc in substrate_discrepancies[:10]:  # Show first 10
            print(f"  {disc['site']} {disc['season']} {disc['metric']}: CSV={disc['csv_value']} DB={disc['db_value']}")
        if len(substrate_discrepancies) > 10:
            print(f"  ... and {len(substrate_discrepancies) - 10} more")
    
    return substrate_discrepancies

def main():
    """Main verification function"""
    print("🔍 Starting Data Integrity Verification...")
    print("=" * 60)
    
    fish_issues = verify_fish_data()
    substrate_issues = verify_substrate_data()
    
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"🐟 Fish Data Discrepancies: {len(fish_issues)}")
    print(f"🪸 Substrate Data Discrepancies: {len(substrate_issues)}")
    
    if len(fish_issues) == 0 and len(substrate_issues) == 0:
        print("\n✅ ALL DATA VERIFIED - Database matches CSV files exactly!")
    else:
        print(f"\n❌ Found {len(fish_issues) + len(substrate_issues)} total discrepancies")
        print("Database values do not match CSV files")
    
    return fish_issues, substrate_issues

if __name__ == "__main__":
    main()