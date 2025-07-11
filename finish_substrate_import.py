#!/usr/bin/env python3
"""
Complete substrate data import for remaining sites
"""

import pandas as pd
import os
from utils.database import get_db_session, Site, Survey
from utils.new_data_importer import SITE_NAME_MAPPING, clean_numeric_value

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

def import_remaining_sites():
    """Import substrate data for remaining sites"""
    total_updates = 0
    
    # Remaining sites to process
    remaining_sites = [
        "Lutoban North MPA.csv",
        "Lutoban Pier.csv", 
        "Lutoban South MPA.csv",
        "Maluay Malatapay MPA.csv",
        "Mojon MPA.csv",
        "Salag MPA.csv",
        "Santa Catalina Cawitan.csv",
        "Santa Catalina Manalongon.csv"
    ]
    
    subs_path = "attached_assets/MCP_Data/new_data/subs/seasonal"
    
    for filename in remaining_sites:
        file_path = os.path.join(subs_path, filename)
        
        if not os.path.exists(file_path):
            print(f"File not found: {filename}")
            continue
        
        with get_db_session() as db:
            try:
                df = pd.read_csv(file_path)
                
                site_name_csv = df.iloc[0]['Site']
                site_name_db = SITE_NAME_MAPPING.get(site_name_csv, site_name_csv)
                
                site = db.query(Site).filter(Site.name == site_name_db).first()
                if not site:
                    print(f"Site not found: {site_name_db}")
                    continue
                
                site_updates = 0
                
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
                        hard_coral = clean_numeric_value(row.get('Hard Coral Cover'))
                        algae = clean_numeric_value(row.get('Fresh Algae Cover'))
                        rubble = clean_numeric_value(row.get('Rubble Cover'))
                        bleaching = clean_numeric_value(row.get('Bleaching'))
                        
                        if hard_coral is not None:
                            survey.hard_coral_cover = hard_coral
                            site_updates += 1
                        
                        if algae is not None:
                            survey.fleshy_macro_algae_cover = algae
                            site_updates += 1
                        
                        if rubble is not None:
                            survey.rubble = rubble
                            site_updates += 1
                        
                        if bleaching is not None:
                            survey.bleaching = bleaching
                            site_updates += 1
                    
                    except Exception as e:
                        print(f"Error processing {site_name_db} {period}: {e}")
                        continue
                
                db.commit()
                print(f"✅ {site_name_db}: {site_updates} substrate updates")
                total_updates += site_updates
                
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
                db.rollback()
    
    print(f"\n🎯 Remaining sites substrate import complete: {total_updates} updates")
    return total_updates

if __name__ == "__main__":
    import_remaining_sites()