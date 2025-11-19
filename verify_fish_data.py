"""
Verify fish and biomass data across all sites
"""
import pandas as pd
import os
from utils.database import get_db_session, Site, Survey
from utils.new_data_importer import SITE_NAME_MAPPING, parse_period_to_date, parse_period_to_season

def verify_fish_data():
    """Compare fish CSV data with database data for all sites"""
    
    mismatches = []
    verified_sites = []
    
    with get_db_session() as db:
        # Check fish data
        fish_path = 'attached_assets/MCP_Data/new_data/fish/seasonal'
        
        for filename in os.listdir(fish_path):
            if not filename.endswith('.csv'):
                continue
            
            # Skip BANGCOLUTAN
            if 'BANGCOLUTAN' in filename:
                continue
            
            site_name_from_file = filename.replace('.csv', '')
            mapped_site_name = SITE_NAME_MAPPING.get(site_name_from_file)
            
            if not mapped_site_name:
                continue
            
            # Get site from database
            site = db.query(Site).filter(Site.name == mapped_site_name).first()
            if not site:
                continue
            
            # Read CSV file
            csv_path = os.path.join(fish_path, filename)
            df = pd.read_csv(csv_path)
            
            # Check the last 3 entries
            for i in range(min(3, len(df))):
                row = df.iloc[-(i+1)]
                
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
                csv_commercial_biomass = row.get('Commercial Biomass Density')
                csv_herbivore = row.get('Herbivore Density')
                csv_carnivore = row.get('Carnivore Density')
                csv_omnivore = row.get('Omnivore Density')
                csv_corallivore = row.get('Corallivore Density')
                
                if db_survey:
                    # Compare values
                    tolerance = 0.001
                    checks = []
                    
                    if csv_commercial_biomass is not None and pd.notna(csv_commercial_biomass):
                        if db_survey.commercial_biomass is None or abs(float(csv_commercial_biomass) - float(db_survey.commercial_biomass)) > tolerance:
                            checks.append(f"Commercial Biomass: CSV={csv_commercial_biomass:.3f}, DB={db_survey.commercial_biomass}")
                    
                    if csv_herbivore is not None and pd.notna(csv_herbivore):
                        if db_survey.herbivore_density is None or abs(float(csv_herbivore) - float(db_survey.herbivore_density)) > tolerance:
                            checks.append(f"Herbivore: CSV={csv_herbivore:.3f}, DB={db_survey.herbivore_density}")
                    
                    if csv_carnivore is not None and pd.notna(csv_carnivore):
                        if db_survey.carnivore_density is None or abs(float(csv_carnivore) - float(db_survey.carnivore_density)) > tolerance:
                            checks.append(f"Carnivore: CSV={csv_carnivore:.3f}, DB={db_survey.carnivore_density}")
                    
                    if csv_omnivore is not None and pd.notna(csv_omnivore):
                        if db_survey.omnivore_density is None or abs(float(csv_omnivore) - float(db_survey.omnivore_density)) > tolerance:
                            checks.append(f"Omnivore: CSV={csv_omnivore:.3f}, DB={db_survey.omnivore_density}")
                    
                    if csv_corallivore is not None and pd.notna(csv_corallivore):
                        if db_survey.corallivore_density is None or abs(float(csv_corallivore) - float(db_survey.corallivore_density)) > tolerance:
                            checks.append(f"Corallivore: CSV={csv_corallivore:.3f}, DB={db_survey.corallivore_density}")
                    
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
    print("FISH & BIOMASS DATA VERIFICATION REPORT")
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
        print("\n✅ All fish and biomass data matches CSV files!")
    
    print("=" * 80)
    
    return mismatches

if __name__ == "__main__":
    verify_fish_data()
