#!/bin/bash
set -e

echo "Running post-merge setup..."

# Reimport all data categories from updated CSV files
python3 -c "
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
from utils.new_data_importer import import_new_dataset
import_new_dataset()
"

echo "Post-merge setup complete."
