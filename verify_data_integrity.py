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
    
    # Handle different year formats
    if '/' in year_part:
        # Format like "24/25" - use the first year and add 2000
        year = int(year_part.split('/')[0])
        if year < 50:
            year += 2000
        else:
            year += 1900
    else:
        # Format like "2024"
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

def verify_fish_data():
    """Verify fish data integrity between CSV files and database"""
    print("🔍 Verifying fish data integrity...")
    
    discrepancies = []
    fixes_applied = 0
    
    with get_db_session() as db:
        csv_path = "attached_assets/MCP_Data/new_data/fish/seasonal"
        
        for filename in os.listdir(csv_path):
            if not filename.endswith('.csv'):
                continue
                
            print(f"\n📊 Checking {filename}...")
            df = pd.read_csv(os.path.join(csv_path, filename))
            
            # Get site name from first row
            site_name_csv = df.iloc[0]['Site']
            site_name_db = SITE_NAME_MAPPING.get(site_name_csv, site_name_csv)
            
            # Get site from database
            site = db.query(Site).filter(Site.name == site_name_db).first()
            if not site:
                print(f"❌ Site not found: {site_name_db}")
                continue
            
            # Check each period
            for _, row in df.iterrows():
                period = row['Period']
                season = parse_period_to_season(period)
                
                # Get database record
                survey = db.query(Survey).filter(
                    Survey.site_id == site.id,
                    Survey.season == season
                ).first()
                
                if not survey:
                    print(f"❌ Survey not found: {site_name_db} {season}")
                    continue
                
                # Check commercial biomass
                csv_biomass = clean_numeric_value(row.get('Commercial Biomass Density'))
                db_biomass = survey.commercial_biomass
                
                if csv_biomass is not None and db_biomass is not None:
                    if abs(csv_biomass - db_biomass) > 0.001:  # Allow for small floating point differences
                        discrepancy = {
                            'site': site_name_db,
                            'season': season,
                            'metric': 'commercial_biomass',
                            'csv_value': csv_biomass,
                            'db_value': db_biomass
                        }
                        discrepancies.append(discrepancy)
                        print(f"❌ MISMATCH: {site_name_db} {season} - CSV: {csv_biomass}, DB: {db_biomass}")
                        
                        # Fix the discrepancy
                        survey.commercial_biomass = csv_biomass
                        fixes_applied += 1
                        print(f"✅ FIXED: Updated to {csv_biomass}")
                
                # Check fish densities
                density_checks = [
                    ('Corallivore Density', 'corallivore_density'),
                    ('Omnivore Density', 'omnivore_density'),
                    ('Carnivore Density', 'carnivore_density'),
                    ('Herbivore Density', 'herbivore_density'),
                    ('Commercial Density', 'commercial_density'),
                    ('Total Density', 'total_density')
                ]
                
                for csv_col, db_col in density_checks:
                    csv_val = clean_numeric_value(row.get(csv_col))
                    db_val = getattr(survey, db_col)
                    
                    if csv_val is not None and db_val is not None:
                        if abs(csv_val - db_val) > 0.001:
                            discrepancy = {
                                'site': site_name_db,
                                'season': season,
                                'metric': db_col,
                                'csv_value': csv_val,
                                'db_value': db_val
                            }
                            discrepancies.append(discrepancy)
                            print(f"❌ MISMATCH: {site_name_db} {season} {db_col} - CSV: {csv_val}, DB: {db_val}")
                            
                            # Fix the discrepancy
                            setattr(survey, db_col, csv_val)
                            fixes_applied += 1
                            print(f"✅ FIXED: Updated to {csv_val}")
        
        # Commit all fixes
        if fixes_applied > 0:
            db.commit()
            print(f"\n✅ Applied {fixes_applied} fixes to database")
        else:
            print(f"\n✅ No discrepancies found in fish data")
    
    return discrepancies

def verify_substrate_data():
    """Verify substrate data integrity"""
    print("\n🔍 Verifying substrate data integrity...")
    
    discrepancies = []
    fixes_applied = 0
    
    with get_db_session() as db:
        csv_path = "attached_assets/MCP_Data/new_data/subs/seasonal"
        
        if not os.path.exists(csv_path):
            print(f"❌ Substrate data folder not found: {csv_path}")
            return discrepancies
            
        for filename in os.listdir(csv_path):
            if not filename.endswith('.csv'):
                continue
                
            print(f"\n📊 Checking {filename}...")
            df = pd.read_csv(os.path.join(csv_path, filename))
            
            # Get site name from first row
            site_name_csv = df.iloc[0]['Site']
            site_name_db = SITE_NAME_MAPPING.get(site_name_csv, site_name_csv)
            
            # Get site from database
            site = db.query(Site).filter(Site.name == site_name_db).first()
            if not site:
                print(f"❌ Site not found: {site_name_db}")
                continue
            
            # Check each period
            for _, row in df.iterrows():
                period = row['Period']
                season = parse_period_to_season(period)
                
                # Get database record
                survey = db.query(Survey).filter(
                    Survey.site_id == site.id,
                    Survey.season == season
                ).first()
                
                if not survey:
                    print(f"❌ Survey not found: {site_name_db} {season}")
                    continue
                
                # Check substrate metrics
                substrate_checks = [
                    ('Hard Coral Cover', 'hard_coral_cover'),
                    ('Fresh Algae Cover', 'fleshy_macro_algae_cover'),
                    ('Rubble Cover', 'rubble'),
                    ('Bleaching', 'bleaching')
                ]
                
                for csv_col, db_col in substrate_checks:
                    csv_val = clean_numeric_value(row.get(csv_col))
                    db_val = getattr(survey, db_col)
                    
                    if csv_val is not None and db_val is not None:
                        if abs(csv_val - db_val) > 0.001:
                            discrepancy = {
                                'site': site_name_db,
                                'season': season,
                                'metric': db_col,
                                'csv_value': csv_val,
                                'db_value': db_val
                            }
                            discrepancies.append(discrepancy)
                            print(f"❌ MISMATCH: {site_name_db} {season} {db_col} - CSV: {csv_val}, DB: {db_val}")
                            
                            # Fix the discrepancy
                            setattr(survey, db_col, csv_val)
                            fixes_applied += 1
                            print(f"✅ FIXED: Updated to {csv_val}")
        
        # Commit all fixes
        if fixes_applied > 0:
            db.commit()
            print(f"\n✅ Applied {fixes_applied} substrate fixes to database")
        else:
            print(f"\n✅ No discrepancies found in substrate data")
    
    return discrepancies

def main():
    """Main verification function"""
    print("🔍 Starting comprehensive data integrity verification...")
    
    # Verify fish data
    fish_discrepancies = verify_fish_data()
    
    # Verify substrate data
    substrate_discrepancies = verify_substrate_data()
    
    # Summary
    total_discrepancies = len(fish_discrepancies) + len(substrate_discrepancies)
    print(f"\n📋 VERIFICATION SUMMARY:")
    print(f"Fish data discrepancies: {len(fish_discrepancies)}")
    print(f"Substrate data discrepancies: {len(substrate_discrepancies)}")
    print(f"Total discrepancies found and fixed: {total_discrepancies}")
    
    if total_discrepancies == 0:
        print("✅ All data integrity checks passed!")
    else:
        print("✅ All discrepancies have been fixed!")
    
    return fish_discrepancies, substrate_discrepancies

if __name__ == "__main__":
    main()