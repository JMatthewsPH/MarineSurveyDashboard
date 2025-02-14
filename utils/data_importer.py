import os
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from .database import Site, Survey, get_db

def parse_season_to_date(season: str) -> datetime:
    """Convert season string to a date object using the middle month of the season."""
    parts = season.replace('/', '-').split()
    if len(parts) == 2:  # Format: "SEP-NOV 2017"
        months, year = parts
        start_month = months.split('-')[0]
    else:  # Format: "DEC-FEB 2017/18"
        months, years = parts[0], parts[1]
        start_month = months.split('-')[0]
        year = years.split('/')[0]
    
    month_map = {
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }
    
    return datetime(int(year), month_map[start_month], 1)

def import_csv_data(csv_folder_path: str, db: Session):
    """Import data from all CSV files in the specified folder."""
    for filename in os.listdir(csv_folder_path):
        if not filename.endswith('.csv'):
            continue
            
        # Extract site name from filename
        municipality, site_name = filename.replace('.csv', '').split(' - ')
        
        # Get or create site
        site = db.query(Site).filter(Site.name == site_name).first()
        if not site:
            print(f"Site not found: {site_name}")
            continue
            
        # Read CSV file
        file_path = os.path.join(csv_folder_path, filename)
        df = pd.read_csv(file_path)
        
        # Process each row
        for _, row in df.iterrows():
            survey_date = parse_season_to_date(row['Season'])
            
            # Create new survey
            survey = Survey(
                site_id=site.id,
                date=survey_date,
                season=row['Season'],
                hard_coral_cover=row['Hard Coral Cover'],
                fleshy_macro_algae_cover=row['Fleshy Macro Algae Cover'],
                rubble=row['Rubble'],
                bleaching=row['Bleaching'],
                total_density=row['Total Denisty'],  # Note: Keeping original column name with typo
                commercial_density=row['Commercial Denisty'],
                commercial_biomass=row['Commercial Biomass'],
                herbivore_density=row['Herbivore Denisty'],
                carnivore_density=row['Carnivore Density'],
                omnivore_density=row['Omnivore Density'],
                corallivore_density=row['Corallivore Denisty']
            )
            
            # Add survey to database
            db.add(survey)
        
        try:
            db.commit()
            print(f"Successfully imported data for {site_name}")
        except Exception as e:
            print(f"Error importing data for {site_name}: {str(e)}")
            db.rollback()

def run_import():
    """Run the data import process."""
    csv_folder_path = "attached_assets/MCP_Data"
    db = next(get_db())
    try:
        import_csv_data(csv_folder_path, db)
        print("Data import completed successfully")
    except Exception as e:
        print(f"Error during import: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    run_import()
