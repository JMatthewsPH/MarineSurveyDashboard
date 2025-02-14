import os
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from .database import Site, Survey, get_db

def parse_season_to_date(season: str) -> datetime:
    """Convert season string to a date object using the middle month of the season."""
    try:
        parts = season.replace('/', '-').split()
        if len(parts) == 2:  # Format: "SEP-NOV 2017"
            months, year = parts
            start_month = months.split('-')[0]
            year = year
        else:  # Format: "DEC-FEB 2017/18"
            months, years = parts[0], parts[1]
            start_month = months.split('-')[0]
            year = years.split('/')[0]

        month_map = {
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }

        month = month_map[start_month]
        return datetime(int(year), month, 1)
    except Exception as e:
        print(f"Error parsing date from season '{season}': {str(e)}")
        return None

def clean_numeric_value(value):
    """Convert string numbers with commas to float"""
    if isinstance(value, str):
        return float(value.replace(',', ''))
    return value

def import_csv_data(csv_folder_path: str, db: Session):
    """Import data from all CSV files in the specified folder."""
    print("Starting data import process...")

    for filename in os.listdir(csv_folder_path):
        if not filename.endswith('.csv'):
            continue

        print(f"Processing file: {filename}")

        # Extract site name from filename
        try:
            municipality, site_name = filename.replace('.csv', '').split(' - ')
        except ValueError:
            print(f"Invalid filename format: {filename}")
            continue

        # Get or create site
        site = db.query(Site).filter(Site.name == site_name).first()
        if not site:
            print(f"Site not found: {site_name}")
            continue

        # Read CSV file
        file_path = os.path.join(csv_folder_path, filename)
        try:
            df = pd.read_csv(file_path)
            print(f"Successfully read CSV file {filename} with {len(df)} rows")

            # Clean numeric columns
            numeric_columns = [
                'Hard Coral Cover', 'Fleshy Macro Algae Cover', 'Rubble',
                'Bleaching', 'Total Denisty', 'Commercial Denisty',
                'Commercial Biomass', 'Herbivore Denisty', 'Carnivore Density',
                'Omnivore Density', 'Corallivore Denisty'
            ]

            for col in numeric_columns:
                if col in df.columns:
                    df[col] = df[col].apply(clean_numeric_value)

            # Process each row
            for _, row in df.iterrows():
                survey_date = parse_season_to_date(row['Season'])
                if survey_date is None:
                    print(f"Skipping row with invalid date in file {filename}")
                    continue

                try:
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

                    # Check if survey for this site and date already exists
                    existing_survey = (
                        db.query(Survey)
                        .filter(Survey.site_id == site.id, Survey.date == survey_date)
                        .first()
                    )

                    if not existing_survey:
                        db.add(survey)
                        print(f"Added survey for {site_name} on {survey_date}")
                except Exception as e:
                    print(f"Error processing row in {filename}: {str(e)}")
                    continue

            try:
                db.commit()
                print(f"Successfully imported data for {site_name}")
            except Exception as e:
                print(f"Error committing data for {site_name}: {str(e)}")
                db.rollback()

        except Exception as e:
            print(f"Error reading file {filename}: {str(e)}")
            continue

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