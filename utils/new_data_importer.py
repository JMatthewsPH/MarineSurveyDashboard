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

def extract_metric_with_stats(row, metric_name, convert_to_decimal=False):
    """
    Extract a metric and all its statistical measures from a row.
    Returns a dict with keys: value, n, sd, se, ci_low, ci_high, eb_low, eb_high
    
    Args:
        row: DataFrame row
        metric_name: Name of the metric column
        convert_to_decimal: If True, divide percentage values by 100 for storage as decimals
    """
    divisor = 100.0 if convert_to_decimal else 1.0
    
    value = clean_numeric_value(row.get(metric_name))
    sd = clean_numeric_value(row.get(f'{metric_name}_SD'))
    se = clean_numeric_value(row.get(f'{metric_name}_SE'))
    ci_low = clean_numeric_value(row.get(f'{metric_name}_CI_low'))
    ci_high = clean_numeric_value(row.get(f'{metric_name}_CI_high'))
    eb_low = clean_numeric_value(row.get(f'{metric_name}_EB_low'))
    eb_high = clean_numeric_value(row.get(f'{metric_name}_EB_high'))
    
    return {
        'value': value / divisor if value is not None else None,
        'n': clean_numeric_value(row.get(f'{metric_name}_N')),  # n stays as count
        'sd': sd / divisor if sd is not None else None,
        'se': se / divisor if se is not None else None,
        'ci_low': ci_low / divisor if ci_low is not None else None,
        'ci_high': ci_high / divisor if ci_high is not None else None,
        'eb_low': eb_low / divisor if eb_low is not None else None,
        'eb_high': eb_high / divisor if eb_high is not None else None
    }

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
                    # Corallivore Density
                    corallivore = extract_metric_with_stats(row, 'Corallivore Density')
                    survey.corallivore_density = corallivore['value']
                    survey.corallivore_density_n = corallivore['n']
                    survey.corallivore_density_sd = corallivore['sd']
                    survey.corallivore_density_se = corallivore['se']
                    survey.corallivore_density_ci_low = corallivore['ci_low']
                    survey.corallivore_density_ci_high = corallivore['ci_high']
                    survey.corallivore_density_eb_low = corallivore['eb_low']
                    survey.corallivore_density_eb_high = corallivore['eb_high']
                    
                    # Detritivore Density
                    detritivore = extract_metric_with_stats(row, 'Detritivore Density')
                    survey.detritivore_density = detritivore['value']
                    survey.detritivore_density_n = detritivore['n']
                    survey.detritivore_density_sd = detritivore['sd']
                    survey.detritivore_density_se = detritivore['se']
                    survey.detritivore_density_ci_low = detritivore['ci_low']
                    survey.detritivore_density_ci_high = detritivore['ci_high']
                    survey.detritivore_density_eb_low = detritivore['eb_low']
                    survey.detritivore_density_eb_high = detritivore['eb_high']
                    
                    # Omnivore Density
                    omnivore = extract_metric_with_stats(row, 'Omnivore Density')
                    survey.omnivore_density = omnivore['value']
                    survey.omnivore_density_n = omnivore['n']
                    survey.omnivore_density_sd = omnivore['sd']
                    survey.omnivore_density_se = omnivore['se']
                    survey.omnivore_density_ci_low = omnivore['ci_low']
                    survey.omnivore_density_ci_high = omnivore['ci_high']
                    survey.omnivore_density_eb_low = omnivore['eb_low']
                    survey.omnivore_density_eb_high = omnivore['eb_high']
                    
                    # Carnivore Density
                    carnivore = extract_metric_with_stats(row, 'Carnivore Density')
                    survey.carnivore_density = carnivore['value']
                    survey.carnivore_density_n = carnivore['n']
                    survey.carnivore_density_sd = carnivore['sd']
                    survey.carnivore_density_se = carnivore['se']
                    survey.carnivore_density_ci_low = carnivore['ci_low']
                    survey.carnivore_density_ci_high = carnivore['ci_high']
                    survey.carnivore_density_eb_low = carnivore['eb_low']
                    survey.carnivore_density_eb_high = carnivore['eb_high']
                    
                    # Herbivore Density
                    herbivore = extract_metric_with_stats(row, 'Herbivore Density')
                    survey.herbivore_density = herbivore['value']
                    survey.herbivore_density_n = herbivore['n']
                    survey.herbivore_density_sd = herbivore['sd']
                    survey.herbivore_density_se = herbivore['se']
                    survey.herbivore_density_ci_low = herbivore['ci_low']
                    survey.herbivore_density_ci_high = herbivore['ci_high']
                    survey.herbivore_density_eb_low = herbivore['eb_low']
                    survey.herbivore_density_eb_high = herbivore['eb_high']
                    
                    # Total Density
                    total_density = extract_metric_with_stats(row, 'Total Density')
                    survey.total_density = total_density['value']
                    survey.total_density_n = total_density['n']
                    survey.total_density_sd = total_density['sd']
                    survey.total_density_se = total_density['se']
                    survey.total_density_ci_low = total_density['ci_low']
                    survey.total_density_ci_high = total_density['ci_high']
                    survey.total_density_eb_low = total_density['eb_low']
                    survey.total_density_eb_high = total_density['eb_high']
                    
                    # Commercial Density
                    commercial_density = extract_metric_with_stats(row, 'Commercial Density')
                    survey.commercial_density = commercial_density['value']
                    survey.commercial_density_n = commercial_density['n']
                    survey.commercial_density_sd = commercial_density['sd']
                    survey.commercial_density_se = commercial_density['se']
                    survey.commercial_density_ci_low = commercial_density['ci_low']
                    survey.commercial_density_ci_high = commercial_density['ci_high']
                    survey.commercial_density_eb_low = commercial_density['eb_low']
                    survey.commercial_density_eb_high = commercial_density['eb_high']
                    
                    # Total Biomass Density
                    total_biomass = extract_metric_with_stats(row, 'Total Biomass Density')
                    survey.total_biomass = total_biomass['value']
                    survey.total_biomass_n = total_biomass['n']
                    survey.total_biomass_sd = total_biomass['sd']
                    survey.total_biomass_se = total_biomass['se']
                    survey.total_biomass_ci_low = total_biomass['ci_low']
                    survey.total_biomass_ci_high = total_biomass['ci_high']
                    survey.total_biomass_eb_low = total_biomass['eb_low']
                    survey.total_biomass_eb_high = total_biomass['eb_high']
                    
                    # Commercial Biomass Density
                    commercial_biomass = extract_metric_with_stats(row, 'Commercial Biomass Density')
                    survey.commercial_biomass = commercial_biomass['value']
                    survey.commercial_biomass_n = commercial_biomass['n']
                    survey.commercial_biomass_sd = commercial_biomass['sd']
                    survey.commercial_biomass_se = commercial_biomass['se']
                    survey.commercial_biomass_ci_low = commercial_biomass['ci_low']
                    survey.commercial_biomass_ci_high = commercial_biomass['ci_high']
                    survey.commercial_biomass_eb_low = commercial_biomass['eb_low']
                    survey.commercial_biomass_eb_high = commercial_biomass['eb_high']
                    
                elif category_name == 'inverts':
                    # Corallivore Density (from invertebrates)
                    corallivore = extract_metric_with_stats(row, 'Corallivore Density')
                    if corallivore['value'] is not None:
                        survey.corallivore_density = corallivore['value']
                        survey.corallivore_density_n = corallivore['n']
                        survey.corallivore_density_sd = corallivore['sd']
                        survey.corallivore_density_se = corallivore['se']
                        survey.corallivore_density_ci_low = corallivore['ci_low']
                        survey.corallivore_density_ci_high = corallivore['ci_high']
                        survey.corallivore_density_eb_low = corallivore['eb_low']
                        survey.corallivore_density_eb_high = corallivore['eb_high']
                    
                    logger.debug(f"Processed invertebrate data for {mapped_site_name} {season}")
                    
                elif category_name == 'subs':
                    # Hard Coral Cover (convert percentages to decimals for storage)
                    hard_coral = extract_metric_with_stats(row, 'Hard Coral Cover', convert_to_decimal=True)
                    survey.hard_coral_cover = hard_coral['value']
                    survey.hard_coral_cover_n = hard_coral['n']
                    survey.hard_coral_cover_sd = hard_coral['sd']
                    survey.hard_coral_cover_se = hard_coral['se']
                    survey.hard_coral_cover_ci_low = hard_coral['ci_low']
                    survey.hard_coral_cover_ci_high = hard_coral['ci_high']
                    survey.hard_coral_cover_eb_low = hard_coral['eb_low']
                    survey.hard_coral_cover_eb_high = hard_coral['eb_high']
                    
                    # Soft Coral Cover (convert percentages to decimals for storage)
                    soft_coral = extract_metric_with_stats(row, 'Soft Coral Cover', convert_to_decimal=True)
                    survey.soft_coral_cover = soft_coral['value']
                    survey.soft_coral_cover_n = soft_coral['n']
                    survey.soft_coral_cover_sd = soft_coral['sd']
                    survey.soft_coral_cover_se = soft_coral['se']
                    survey.soft_coral_cover_ci_low = soft_coral['ci_low']
                    survey.soft_coral_cover_ci_high = soft_coral['ci_high']
                    survey.soft_coral_cover_eb_low = soft_coral['eb_low']
                    survey.soft_coral_cover_eb_high = soft_coral['eb_high']
                    
                    # Fresh Algae Cover (convert percentages to decimals for storage)
                    algae = extract_metric_with_stats(row, 'Fresh Algae Cover', convert_to_decimal=True)
                    survey.fleshy_macro_algae_cover = algae['value']
                    survey.fleshy_macro_algae_cover_n = algae['n']
                    survey.fleshy_macro_algae_cover_sd = algae['sd']
                    survey.fleshy_macro_algae_cover_se = algae['se']
                    survey.fleshy_macro_algae_cover_ci_low = algae['ci_low']
                    survey.fleshy_macro_algae_cover_ci_high = algae['ci_high']
                    survey.fleshy_macro_algae_cover_eb_low = algae['eb_low']
                    survey.fleshy_macro_algae_cover_eb_high = algae['eb_high']
                    
                    # Rubble Cover (convert percentages to decimals for storage)
                    rubble = extract_metric_with_stats(row, 'Rubble Cover', convert_to_decimal=True)
                    survey.rubble = rubble['value']
                    survey.rubble_n = rubble['n']
                    survey.rubble_sd = rubble['sd']
                    survey.rubble_se = rubble['se']
                    survey.rubble_ci_low = rubble['ci_low']
                    survey.rubble_ci_high = rubble['ci_high']
                    survey.rubble_eb_low = rubble['eb_low']
                    survey.rubble_eb_high = rubble['eb_high']
                    
                    # Bleaching (convert percentages to decimals for storage)
                    bleaching = extract_metric_with_stats(row, 'Bleaching', convert_to_decimal=True)
                    survey.bleaching = bleaching['value']
                    survey.bleaching_n = bleaching['n']
                    survey.bleaching_sd = bleaching['sd']
                    survey.bleaching_se = bleaching['se']
                    survey.bleaching_ci_low = bleaching['ci_low']
                    survey.bleaching_ci_high = bleaching['ci_high']
                    survey.bleaching_eb_low = bleaching['eb_low']
                    survey.bleaching_eb_high = bleaching['eb_high']
            
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