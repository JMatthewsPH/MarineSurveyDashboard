"""
Export Utilities for Marine Conservation Platform

This module provides functions for exporting data and charts in various formats.
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime
import json
import base64

def create_download_link(data, filename, link_text="Download data"):
    """
    Create a download link for any data
    
    Args:
        data: Binary data to download
        filename: Name of the file to be downloaded
        link_text: Text for the download link
        
    Returns:
        HTML string containing the download link
    """
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

def export_dataframe_to_csv(df, prefix="marine_data"):
    """
    Export a dataframe to CSV format
    
    Args:
        df: Pandas DataFrame to export
        prefix: Prefix for the filename
        
    Returns:
        CSV data as string
    """
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.csv"
    
    # Create CSV
    csv = df.to_csv(index=False)
    
    return csv, filename

def export_dataframe_to_excel(df, prefix="marine_data"):
    """
    Export a dataframe to Excel format
    
    Args:
        df: Pandas DataFrame to export
        prefix: Prefix for the filename
        
    Returns:
        Excel data as bytes
    """
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.xlsx"
    
    # Create Excel file
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    
    excel_data = buffer.getvalue()
    
    return excel_data, filename

def export_dataframe_to_json(df, prefix="marine_data"):
    """
    Export a dataframe to JSON format
    
    Args:
        df: Pandas DataFrame to export
        prefix: Prefix for the filename
        
    Returns:
        JSON data as string
    """
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.json"
    
    # Create JSON
    json_str = df.to_json(orient="records", date_format="iso")
    
    return json_str, filename

def create_export_section(data, container, prefix="marine_data"):
    """
    Create an export section with multiple download options
    
    Args:
        data: Pandas DataFrame to export
        container: Streamlit container to render in
        prefix: Prefix for export filenames
    """
    # Create separate columns for different export types
    col1, col2, col3 = container.columns(3)
    
    # CSV Export
    csv_data, csv_filename = export_dataframe_to_csv(data, prefix)
    col1.download_button(
        label="Export CSV",
        data=csv_data,
        file_name=csv_filename,
        mime="text/csv",
    )
    
    # Excel Export
    excel_data, excel_filename = export_dataframe_to_excel(data, prefix)
    col2.download_button(
        label="Export Excel",
        data=excel_data,
        file_name=excel_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    
    # JSON Export
    json_data, json_filename = export_dataframe_to_json(data, prefix)
    col3.download_button(
        label="Export JSON",
        data=json_data,
        file_name=json_filename,
        mime="application/json",
    )