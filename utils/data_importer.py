import os
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from .database import Site, Survey, get_db

def parse_season_to_date(season: str) -> datetime:
    """
    Convert season string to a date object using the first month of the season.
    Format: "<year>Q<1-4>" where:
    Q1 = MAR-MAY
    Q2 = JUN-AUG
    Q3 = SEP-NOV
    Q4 = DEC-FEB
    Returns the date of the first month in the season.
    """
    try:
        if not season or not isinstance(season, str):
            print(f"Invalid season format: {season}")
            return None

        # Clean up the season string
        clean_season = season.strip().split('/')[0]  # Handle cases like "2022Q4/ 23"

        if 'Q' not in clean_season:
            print(f"Invalid season format (missing Q): {season}")
            return None

        year_str = clean_season[:4]
        quarter_str = clean_season[5:6]

        try:
            year = int(year_str)
            quarter = int(quarter_str)
        except ValueError:
            print(f"Invalid year or quarter format: {season}")
            return None

        # Validate year and quarter
        if not (2000 <= year <= 2100) or not (1 <= quarter <= 4):
            print(f"Year or quarter out of valid range: {season}")
            return None

        # Map quarter to starting month
        quarter_to_month = {
            1: 3,  # Q1: March
            2: 6,  # Q2: June
            3: 9,  # Q3: September
            4: 12  # Q4: December
        }

        month = quarter_to_month[quarter]
        return datetime(year, month, 1)

    except Exception as e:
        print(f"Error parsing date from season '{season}': {str(e)}")
        return None

def clean_numeric_value(value):
    """Convert string numbers with commas to float, handling invalid values."""
    try:
        if isinstance(value, str):
            if value == '#REF!' or value.strip() == '':
                return None
            return float(value.replace(',', ''))
        return float(value) if pd.notnull(value) else None
    except Exception as e:
        print(f"Error converting value '{value}' to float: {str(e)}")
        return None

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
            valid_surveys = 0
            for _, row in df.iterrows():
                survey_date = parse_season_to_date(row['Season'])
                if survey_date is None:
                    print(f"Skipping row with invalid date: {row['Season']}")
                    continue

                try:
                    # Skip rows where all numeric values are None
                    if all(pd.isna(row[col]) for col in numeric_columns if col in df.columns):
                        print(f"Skipping row with all null values in {filename}")
                        continue

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
                        valid_surveys += 1

                except Exception as e:
                    print(f"Error processing row in {filename}: {str(e)}")
                    continue

            try:
                db.commit()
                print(f"Successfully imported {valid_surveys} surveys for {site_name}")
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
        # Clear existing data to avoid duplicates
        db.query(Survey).delete()
        db.commit()

        import_csv_data(csv_folder_path, db)
        print("Data import completed successfully")
    except Exception as e:
        print(f"Error during import: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    run_import()