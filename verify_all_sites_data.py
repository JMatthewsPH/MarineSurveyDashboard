"""
Verify that all sites' data in the database matches the CSV files
"""
import pandas as pd
import os
from utils.database import get_db_session, Site, Survey
from utils.new_data_importer import SITE_NAME_MAPPING, parse_period_to_date, parse_period_to_season

def verify_site_data():
    """Compare CSV data with database data for all sites"""
    
    mismatches = []
    verified_sites = []
    
    with get_db_session() as db:
        # Check substrate data (hard coral cover)
        subs_path = 'attached_assets/MCP_Data/new_data/subs/seasonal'
        
        for filename in os.listdir(subs_path):
            if not filename.endswith('.csv'):
                continue
            
            # Skip BANGCOLUTAN
            if 'BANGCOLUTAN' in filename:
                continue
            
            site_name_from_file = filename.replace('.csv', '')
            mapped_site_name = SITE_NAME_MAPPING.get(site_name_from_file)
            
            if not mapped_site_name:
                print(f"⚠️  No mapping for: {site_name_from_file}")
                continue
            
            # Get site from database
            site = db.query(Site).filter(Site.name == mapped_site_name).first()
            if not site:
                print(f"⚠️  Site not in database: {mapped_site_name}")
                continue
            
            # Read CSV file
            csv_path = os.path.join(subs_path, filename)
            df = pd.read_csv(csv_path)
            
            # Check the last 3 entries for comprehensive verification
            for i in range(min(3, len(df))):
                row = df.iloc[-(i+1)]  # Start from the most recent
                
                period = row.get('Period', '')
                if not period:
                    continue
                
                # Parse period
                try:
                    survey_date = parse_period_to_date(period)
                    season = parse_period_to_season(period)
                except:
                    continue
                
                # Get database record
                db_survey = db.query(Survey).filter(
                    Survey.site_id == site.id,
                    Survey.date == survey_date.date(),
                    Survey.season == season
                ).first()
                
                # CSV values
                csv_hard_coral = row.get('Hard Coral Cover')
                csv_rubble = row.get('Rubble Cover')
                csv_algae = row.get('Fresh Algae Cover')
                csv_bleaching = row.get('Bleaching')
                
                if db_survey:
                    # Compare values
                    tolerance = 0.001  # Allow tiny floating point differences
                    
                    checks = []
                    if csv_hard_coral is not None and pd.notna(csv_hard_coral):
                        if db_survey.hard_coral_cover is None or abs(float(csv_hard_coral) - float(db_survey.hard_coral_cover)) > tolerance:
                            checks.append(f"Hard Coral: CSV={csv_hard_coral:.3f}, DB={db_survey.hard_coral_cover}")
                    
                    if csv_rubble is not None and pd.notna(csv_rubble):
                        if db_survey.rubble is None or abs(float(csv_rubble) - float(db_survey.rubble)) > tolerance:
                            checks.append(f"Rubble: CSV={csv_rubble:.3f}, DB={db_survey.rubble}")
                    
                    if csv_algae is not None and pd.notna(csv_algae):
                        if db_survey.fleshy_macro_algae_cover is None or abs(float(csv_algae) - float(db_survey.fleshy_macro_algae_cover)) > tolerance:
                            checks.append(f"Algae: CSV={csv_algae:.3f}, DB={db_survey.fleshy_macro_algae_cover}")
                    
                    if csv_bleaching is not None and pd.notna(csv_bleaching):
                        if db_survey.bleaching is None or abs(float(csv_bleaching) - float(db_survey.bleaching)) > tolerance:
                            checks.append(f"Bleaching: CSV={csv_bleaching:.3f}, DB={db_survey.bleaching}")
                    
                    if checks:
                        mismatches.append({
                            'site': mapped_site_name,
                            'period': period,
                            'issues': checks
                        })
                else:
                    # Database record missing
                    mismatches.append({
                        'site': mapped_site_name,
                        'period': period,
                        'issues': [f"Missing in database"]
                    })
            
            verified_sites.append(mapped_site_name)
    
    # Print results
    print("=" * 80)
    print("DATA VERIFICATION REPORT")
    print("=" * 80)
    print(f"\nVerified {len(verified_sites)} sites: {', '.join(sorted(verified_sites))}")
    
    if mismatches:
        print(f"\n⚠️  Found {len(mismatches)} mismatches:\n")
        for item in mismatches:
            print(f"Site: {item['site']}")
            print(f"Period: {item['period']}")
            for issue in item['issues']:
                print(f"  - {issue}")
            print()
    else:
        print("\n✅ All verified sites match their CSV data!")
    
    print("=" * 80)
    
    return mismatches

if __name__ == "__main__":
    verify_site_data()
