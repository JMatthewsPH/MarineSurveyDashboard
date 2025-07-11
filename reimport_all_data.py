#!/usr/bin/env python3
"""
Reimport all data from CSV files to database
"""

import sys
import os
sys.path.append('.')

from utils.new_data_importer import import_new_dataset
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Reimport all data from CSV files"""
    logger.info("Starting fresh import of all CSV data...")
    
    try:
        # Import all new data
        import_new_dataset("attached_assets/MCP_Data/new_data")
        logger.info("✅ All data imported successfully!")
        print("✅ All data imported successfully!")
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        print(f"❌ Import failed: {e}")
        raise

if __name__ == "__main__":
    main()