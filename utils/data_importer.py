import os
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from .database import Site, Survey, get_db

def parse_season_to_date(season: str) -> datetime:
    """
    Convert season string to a date object using the first month of the season.
    For DEC-FEB seasons that span across years (e.g., 'DEC-FEB 2024/25'),
    uses December of the first year (2024) as the start date.
    Each season spans exactly 3 months.
    """
    try:
        # Split into month range and year part
        parts = season.strip().split()
        if len(parts) != 2:
            print(f"Invalid season format: {season}")
            return None

        months, year_part = parts
        month_range = months.split('-')
        if len(month_range) != 2:
            print(f"Invalid month range format: {months}")
            return None

        start_month = month_range[0]

        # Clean up the year part by removing all spaces
        year_part = year_part.replace(" ", "")

        # Handle the year part for cases like "2024/25"
        if '/' in year_part:
            # Split on slash and take first year
            year = year_part.split('/')[0]
        else:
            year = year_part

        # Map month abbreviations to numbers
        month_map = {
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }

        # Convert month name to number
        try:
            month_num = month_map[start_month]
        except KeyError:
            print(f"Invalid month abbreviation: {start_month}")
            return None

        # Convert year to integer
        try:
            year_num = int(year)
        except ValueError:
            print(f"Invalid year format: {year}")
            return None

        return datetime(year_num, month_num, 1)

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