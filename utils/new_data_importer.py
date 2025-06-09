"""
New Data Importer for Marine Conservation Platform

This module handles importing the new structured data from fish, inverts, and substrate folders.
"""

import pandas as pd
import os
from datetime import datetime
from sqlalchemy.orm import Session
from utils.database import get_db_session, Site, Survey
import logging

logger = logging.getLogger(__name__)

# Site name mapping from new CSV names to existing database names
SITE_NAME_MAPPING = {
    'Andulay MPA': 'Andulay',
    'Antulang': 'Antulang',
    'Basak Can-Unsang MPA': 'Basak',
    'Dalakit MPA': 'Dalakit',
    'Guinsuan MPA': 'Guinsuan',
    'Kookoos': 'Kookoos',
    'Latason MPA': 'Latason',
    'Lutoban North MPA': 'Lutoban North',
    'Lutoban Pier': 'Lutoban Pier',
    'Lutoban South MPA': 'Lutoban South',
    'Maluay Malatapay MPA': 'Malatapay',
    'Mojon MPA': 'Mojon',
    'Salag MPA': 'Salag',
    'Santa Catalina Cawitan': 'Cawitan',
    'Santa Catalina Manalongon': 'Manalongon'
}

def parse_period_to_date(period: str) -> datetime:
    """
    Convert period string to a date object.
    Format examples: "Spring 2024", "Winter 24/25", "Autumn 2017"
    Returns the date of the first month in the season.
    """
    parts = period.strip().split()
    season = parts[0]
    year_part = parts[1]
    
    # Handle different year formats
    if '/' in year_part:
        # Format like "24/25" - use the first year and add 2000
        year = int(year_part.split('/')[0])
        if year < 50:  # Assume 2000s
            year += 2000
        else:  # Assume 1900s (shouldn't happen but safety)
            year += 1900
    else:
        # Format like "2024"
        year = int(year_part)
    
    # Map seasons to months (using middle month of season)
    season_months = {
        'Spring': 4,   # April (Mar-May)
        'Summer': 7,   # July (Jun-Aug)
        'Autumn': 10,  # October (Sep-Nov)
        'Winter': 1    # January (Dec-Feb, but use Jan of the year)
    }
    
    # For winter, if the format is "Winter 24/25", use the second year
    if season == 'Winter' and '/' in year_part:
        year = int(year_part.split('/')[1])
        if year < 50:
            year += 2000
        else:
            year += 1900
    
    month = season_months.get(season, 1)
    return datetime(year, month, 1)

def parse_period_to_season(period: str) -> str:
    """
    Convert period string to descriptive season format (Mar-May, Jun-Aug, etc.).
    """
    parts = period.strip().split()
    season = parts[0]
    year_part = parts[1]
    
    # Handle different year formats
    if '/' in year_part:
        year = int(year_part.split('/')[0])
        if year < 50:
            year += 2000
        else:
            year += 1900
    else:
        year = int(year_part)
    
    # Map seasons to descriptive format
    season_descriptions = {
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
    
    season_desc = season_descriptions.get(season, 'MAR-MAY')
    return f"{season_desc} {year}"

def clean_numeric_value(value):
    """Convert string numbers with commas to float, handling invalid values."""
    if pd.isna(value) or value == '' or value == '-':
        return None
    
    try:
        # Remove commas and convert to float
        if isinstance(value, str):
            value = value.replace(',', '')
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert value to float: {value}")
        return None

def import_category_data(category_path: str, db: Session):
    """Import data from a specific category folder (fish, inverts, or subs)."""
    seasonal_path = os.path.join(category_path, 'seasonal')
    
    if not os.path.exists(seasonal_path):
        logger.warning(f"Seasonal folder not found: {seasonal_path}")
        return
    
    category_name = os.path.basename(category_path)
    logger.info(f"Importing {category_name} data from {seasonal_path}")
    
    # Process each CSV file in the seasonal folder
    for filename in os.listdir(seasonal_path):
        if not filename.endswith('.csv'):
            continue
        
        # Skip BANGCOLUTAN as requested
        if 'BANGCOLUTAN' in filename or 'BANGCOLUTOBAN' in filename:
            logger.info(f"Skipping {filename} as requested")
            continue
        
        file_path = os.path.join(seasonal_path, filename)
        site_name_from_file = filename.replace('.csv', '')
        
        # Map to existing site name
        mapped_site_name = SITE_NAME_MAPPING.get(site_name_from_file)
        if not mapped_site_name:
            logger.warning(f"No mapping found for site: {site_name_from_file}")
            continue
        
        # Check if site exists in database
        site = db.query(Site).filter(Site.name == mapped_site_name).first()
        if not site:
            logger.warning(f"Site not found in database: {mapped_site_name}")
            continue
        
        logger.info(f"Processing {category_name} data for site: {mapped_site_name}")
        
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            if df.empty:
                logger.warning(f"Empty CSV file: {file_path}")
                continue
            
            # Process each row
            for _, row in df.iterrows():
                period = row.get('Period', '')
                if not period:
                    continue
                
                # Convert period to date and season
                try:
                    survey_date = parse_period_to_date(period)
                    season = parse_period_to_season(period)
                except (ValueError, IndexError) as e:
                    logger.warning(f"Could not parse period '{period}': {e}")
                    continue
                
                # Check if survey already exists for this site, date, and season
                existing_survey = db.query(Survey).filter(
                    Survey.site_id == site.id,
                    Survey.date == survey_date.date(),
                    Survey.season == season
                ).first()
                
                if existing_survey:
                    # Update existing survey with new data
                    survey = existing_survey
                    logger.debug(f"Updating existing survey for {mapped_site_name} {season}")
                else:
                    # Create new survey
                    survey = Survey(
                        site_id=site.id,
                        date=survey_date.date(),
                        season=season
                    )
                    db.add(survey)
                    logger.debug(f"Creating new survey for {mapped_site_name} {season}")
                
                # Update survey data based on category
                if category_name == 'fish':
                    survey.corallivore_density = clean_numeric_value(row.get('Corallivore Density'))
                    survey.omnivore_density = clean_numeric_value(row.get('Omnivore Density'))
                    survey.carnivore_density = clean_numeric_value(row.get('Carnivore Density'))
                    survey.herbivore_density = clean_numeric_value(row.get('Herbivore Density'))
                    survey.total_density = clean_numeric_value(row.get('Total Density'))
                    survey.commercial_density = clean_numeric_value(row.get('Commercial Density'))
                    survey.commercial_biomass = clean_numeric_value(row.get('Commercial Biomass Density'))
                    
                elif category_name == 'inverts':
                    # For invertebrates, we can store additional data if needed
                    # Current schema focuses on fish, so we'll log this for now
                    invert_total = clean_numeric_value(row.get('Total Density'))
                    logger.debug(f"Invertebrate total density for {mapped_site_name} {season}: {invert_total}")
                    
                elif category_name == 'subs':
                    survey.hard_coral_cover = clean_numeric_value(row.get('Hard Coral Cover'))
                    survey.fleshy_macro_algae_cover = clean_numeric_value(row.get('Fresh Algae Cover'))
                    survey.rubble = clean_numeric_value(row.get('Rubble Cover'))
                    survey.bleaching = clean_numeric_value(row.get('Bleaching'))
                    # Note: Soft Coral Cover doesn't have a direct mapping in current schema
            
            # Commit after processing each file
            db.commit()
            logger.info(f"Successfully imported {category_name} data for {mapped_site_name}")
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            db.rollback()
            continue

def import_new_dataset(base_path: str = "attached_assets/MCP_Data/new_data"):
    """Import the complete new dataset from all three categories."""
    logger.info(f"Starting import of new dataset from {base_path}")
    
    with get_db_session() as db:
        try:
            # Import data from each category
            categories = ['fish', 'inverts', 'subs']
            
            for category in categories:
                category_path = os.path.join(base_path, category)
                if os.path.exists(category_path):
                    import_category_data(category_path, db)
                else:
                    logger.warning(f"Category folder not found: {category_path}")
            
            logger.info("Successfully completed import of new dataset")
            
        except Exception as e:
            logger.error(f"Error during import: {e}")
            db.rollback()
            raise

def run_new_import():
    """Run the new data import process."""
    logger.info("Starting new data import process")
    
    try:
        import_new_dataset()
        logger.info("New data import completed successfully")
        print("✓ New data import completed successfully")
        
    except Exception as e:
        logger.error(f"New data import failed: {e}")
        print(f"✗ New data import failed: {e}")
        raise

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    run_new_import()