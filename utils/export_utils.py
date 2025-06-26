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
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import tempfile
import os

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

def convert_plotly_to_matplotlib(fig):
    """
    Convert a Plotly figure to a Matplotlib figure
    
    Args:
        fig: Plotly figure object
        
    Returns:
        Matplotlib figure object
    """
    # Import season formatting function
    from utils.graph_generator import format_season
    
    # Create Matplotlib figure
    mpl_fig, ax = plt.subplots(figsize=(8, 5))
    
    # Define COVID period dates for possible dotted line
    covid_start = pd.Timestamp('2019-09-01')
    covid_end = pd.Timestamp('2022-03-01')
    
    # Check if this is a time series with COVID period
    has_covid_period = False
    covid_line_x = []
    covid_line_y = []
    pre_covid_x = []
    pre_covid_y = []
    post_covid_x = []
    post_covid_y = []
    
    # Check if we have seasons in the x-axis
    has_seasons = False
    for trace in fig.data:
        if hasattr(trace, 'x') and isinstance(trace.x, list) and len(trace.x) > 0:
            if isinstance(trace.x[0], str) and any(month in trace.x[0] for month in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']):
                has_seasons = True
                break
    
    # Check multiple data traces for possible COVID marker
    for trace in fig.data:
        if trace.name == 'COVID-19 Period (No Data)' and trace.line.dash == 'dot':
            # We found a COVID period marker
            has_covid_period = True
            covid_line_x = trace.x
            covid_line_y = trace.y
        elif trace.mode == 'lines+markers' or trace.type == 'scatter':
            # Regular data points - check if they might be pre or post COVID
            if isinstance(trace.x, list) and len(trace.x) > 0:
                if has_seasons:
                    # We already have seasons, just use them
                    for i, x_val in enumerate(trace.x):
                        # Try to extract year to determine if pre or post COVID
                        try:
                            if '-' in x_val:
                                year_str = x_val.split(' ')[-1]
                                year = int(year_str)
                                
                                # Use the middle month to estimate the date
                                month_range = x_val.split(' ')[0]
                                if 'MAR-MAY' in month_range:
                                    month = 4  # April
                                elif 'JUN-AUG' in month_range:
                                    month = 7  # July
                                elif 'SEP-NOV' in month_range:
                                    month = 10  # October
                                else:  # DEC-FEB
                                    month = 1  # January
                                    
                                date = pd.Timestamp(year=year, month=month, day=15)
                                
                                if date < covid_start:
                                    pre_covid_x.append(x_val)
                                    pre_covid_y.append(trace.y[i])
                                elif date > covid_end:
                                    post_covid_x.append(x_val)
                                    post_covid_y.append(trace.y[i])
                        except:
                            # Can't determine if pre or post COVID, just use as is
                            pass
                else:
                    # Try to parse x values as dates to determine pre/post COVID and convert to seasons
                    try:
                        x_dates = [pd.to_datetime(x) for x in trace.x]
                        # Sort points by date
                        points = sorted(zip(x_dates, trace.y), key=lambda p: p[0])
                        x_dates = [p[0] for p in points]
                        y_values = [p[1] for p in points]
                        
                        # Convert dates to seasons
                        x_seasons = [format_season(date) for date in x_dates]
                        
                        # Split into pre and post COVID
                        for i, date in enumerate(x_dates):
                            if date < covid_start:
                                pre_covid_x.append(x_seasons[i])
                                pre_covid_y.append(y_values[i])
                            elif date > covid_end:
                                post_covid_x.append(x_seasons[i])
                                post_covid_y.append(y_values[i])
                    except:
                        # Not date data or other issue, plot as is
                        if not has_covid_period:  # Only plot if not already handling COVID period
                            if trace.type == 'scatter':
                                ax.plot(trace.x, trace.y, marker='o')
                            elif trace.type == 'bar':
                                ax.bar(trace.x, trace.y)
    
    # Plot with special COVID handling if needed, otherwise plot the first trace
    if has_covid_period:
        # Plot pre-COVID data
        if pre_covid_x:
            ax.plot(pre_covid_x, pre_covid_y, marker='o', color='#0077b6')
            
        # Plot post-COVID data
        if post_covid_x:
            ax.plot(post_covid_x, post_covid_y, marker='o', color='#0077b6')
            
        # Plot COVID dotted line
        if covid_line_x and len(covid_line_x) >= 2:
            if has_seasons:
                # Use season strings as is
                ax.plot([covid_line_x[0], covid_line_x[1]], 
                        [covid_line_y[0], covid_line_y[1]], 
                        linestyle='--', color='#0077b6', alpha=0.5, 
                        label='COVID-19 Period (No Data)')
            else:
                # Convert dates to seasons
                try:
                    covid_start_date = pd.to_datetime(covid_line_x[0])
                    covid_end_date = pd.to_datetime(covid_line_x[1])
                    covid_start_season = format_season(covid_start_date)
                    covid_end_season = format_season(covid_end_date)
                    
                    ax.plot([covid_start_season, covid_end_season], 
                            [covid_line_y[0], covid_line_y[1]], 
                            linestyle='--', color='#0077b6', alpha=0.5, 
                            label='COVID-19 Period (No Data)')
                except:
                    # Fallback if we can't convert to seasons
                    ax.plot([covid_line_x[0], covid_line_x[1]], 
                            [covid_line_y[0], covid_line_y[1]], 
                            linestyle='--', color='#0077b6', alpha=0.5, 
                            label='COVID-19 Period (No Data)')
            
            ax.legend(loc='best')
    else:
        # If no COVID period found and we haven't plotted yet, use the first trace
        if not pre_covid_x and not post_covid_x and len(fig.data) > 0:
            trace = fig.data[0]
            if trace.type == 'scatter':
                ax.plot(trace.x, trace.y, marker='o', color='#0077b6')
            elif trace.type == 'bar':
                ax.bar(trace.x, trace.y, color='#0077b6')
            
    # Rotate x-axis labels if we likely have seasonal labels
    if has_seasons or pre_covid_x or post_covid_x:
        plt.xticks(rotation=45, ha='right')
    
    # Set title and labels
    if fig.layout.title.text:
        ax.set_title(fig.layout.title.text)
    if fig.layout.xaxis.title.text:
        ax.set_xlabel(fig.layout.xaxis.title.text)
    if fig.layout.yaxis.title.text:
        ax.set_ylabel(fig.layout.yaxis.title.text)
    
    # Set consistent y-axis limits and ticks for specific metrics
    title_text = fig.layout.title.text if fig.layout.title.text else ""
    if "Commercial Fish Biomass" in title_text or "Commercial Biomass" in title_text:
        ax.set_ylim(0, 100)
        ax.set_yticks(range(0, 101, 20))
    elif "Herbivore" in title_text:
        ax.set_ylim(0, 2500)
        ax.set_yticks(range(0, 2501, 500))
    elif any(term in title_text for term in ["Carnivore", "Omnivore", "Corallivore"]):
        ax.set_ylim(0, 300)
        ax.set_yticks(range(0, 301, 50))
    elif any(term in title_text for term in ["Coral Cover", "Algae Cover", "Bleaching", "Rubble"]):
        ax.set_ylim(0, 100)
        ax.set_yticks(range(0, 101, 20))
    
    # Grid
    ax.grid(True, alpha=0.3)
    
    # Tight layout
    plt.tight_layout()
    
    return mpl_fig

def generate_single_chart_pdf(fig, title, site_name):
    """
    Generate a PDF file containing a single chart
    
    Args:
        fig: Plotly figure to include in the PDF
        title: Title for the chart
        site_name: Name of the site
        
    Returns:
        PDF file as bytes
    """
    # Create a BytesIO object to store the PDF
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Add title
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    elements.append(Paragraph(f"Marine Conservation Report", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add site name and date
    subtitle_style = styles['Heading2']
    elements.append(Paragraph(f"Site: {site_name}", subtitle_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add chart title
    chart_title_style = styles['Heading3']
    elements.append(Paragraph(title, chart_title_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # Save plotly figure to a temporary PNG file
    temp_dir = tempfile.mkdtemp()
    temp_img_path = os.path.join(temp_dir, "chart.png")
    
    # Export figure as an image
    fig_bytes = fig.to_image(format="png", width=800, height=500, scale=2)
    
    # Write to temp file
    with open(temp_img_path, "wb") as f:
        f.write(fig_bytes)
    
    # Add the image to the PDF
    img = Image(temp_img_path, width=6.5*inch, height=4*inch)
    elements.append(img)
    
    # Add some notes
    elements.append(Spacer(1, 0.25*inch))
    elements.append(Paragraph("Notes:", styles['Heading4']))
    
    notes = [
        f"This chart shows data for {site_name}.",
        "Data source: Marine Conservation Monitoring Program.",
        f"Report generated via Marine Conservation Dashboard on {datetime.now().strftime('%Y-%m-%d')}."
    ]
    
    for note in notes:
        elements.append(Paragraph(note, styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
    
    # Build the PDF
    doc.build(elements)
    
    # Clean up the temp file
    try:
        os.remove(temp_img_path)
        os.rmdir(temp_dir)
    except:
        pass
    
    # Reset the buffer position to the beginning
    buffer.seek(0)
    return buffer.getvalue()

def generate_site_report_pdf(site_name, data_processor, metrics=None, include_biomass=True):
    """
    Generate a comprehensive PDF report for a specific site with selected charts
    
    Args:
        site_name: Name of the site
        data_processor: Data processor instance with access to all metrics
        metrics: List of metrics to include (default is standard set)
        include_biomass: Whether to include biomass data (default is True)
        
    Returns:
        PDF file as bytes
    """
    # Import GraphGenerator for consistent Y-axis ranges
    from utils.graph_generator import GraphGenerator
    graph_generator = GraphGenerator(data_processor)
    # If no metrics specified, use standard set matching what's shown on the website
    if metrics is None:
        metrics = ["hard_coral", "fleshy_algae", "herbivore", "carnivore",
                  "omnivore", "corallivore", "bleaching", "rubble"]
    
    # Create buffer for PDF
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Add title
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    elements.append(Paragraph(f"Marine Conservation Report: {site_name}", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Get site information to include municipality
    try:
        sites_df = data_processor.get_sites()
        site_matches = sites_df[sites_df['name'] == site_name]
        if not site_matches.empty:
            site_info = site_matches.iloc[0]
            municipality_name = str(site_info['municipality']) if 'municipality' in site_info else "Unknown Municipality"
        else:
            municipality_name = "Unknown Municipality"
    except Exception as e:
        print(f"Error getting municipality info: {e}")
        municipality_name = "Unknown Municipality"
    
    # Add date and description with improved format
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%B-%d')}", styles['Normal']))
    elements.append(Paragraph(f"The below report contains all available graphs for {site_name}, {municipality_name}.", styles['Normal']))
    elements.append(Spacer(1, 0.5*inch))
    
    # Create temp directory for images
    temp_dir = tempfile.mkdtemp()
    
    # Add biomass data if selected
    if include_biomass:
        biomass_data = data_processor.get_biomass_data(site_name)
        if not biomass_data.empty:
            # Find the actual biomass column
            biomass_column = None
            for col in biomass_data.columns:
                if 'biomass' in col.lower():
                    biomass_column = col
                    break
            
            if biomass_column:
                elements.append(Paragraph(f"Commercial Fish Biomass", styles['Heading2']))
                elements.append(Spacer(1, 0.15*inch))
                
                # Create matplotlib figure
                fig, ax = plt.subplots(figsize=(8, 4))
                
                # Add COVID period markers
                covid_start = pd.Timestamp('2019-09-01')
                covid_end = pd.Timestamp('2022-03-01')
                
                # Import season formatting function
                from utils.graph_generator import format_season
                
                # Ensure date column is in datetime format
                biomass_data['date'] = pd.to_datetime(biomass_data['date'])
                
                # Add season column for x-axis
                biomass_data['season'] = biomass_data['date'].apply(format_season)
                
                # Split data for pre-COVID and post-COVID
                pre_covid = biomass_data[biomass_data['date'] < covid_start].sort_values('date')
                post_covid = biomass_data[biomass_data['date'] > covid_end].sort_values('date')
                
                # Plot pre-COVID data with seasons
                if not pre_covid.empty:
                    ax.plot(pre_covid['season'], pre_covid[biomass_column], marker='o', color='#0077b6')
                
                # Plot post-COVID data with seasons
                if not post_covid.empty:
                    ax.plot(post_covid['season'], post_covid[biomass_column], marker='o', color='#0077b6')
                
                # Add dotted line for COVID period if applicable
                if not pre_covid.empty and not post_covid.empty:
                    last_pre_covid = pre_covid.iloc[-1]
                    first_post_covid = post_covid.iloc[0]
                    ax.plot([last_pre_covid['season'], first_post_covid['season']], 
                            [last_pre_covid[biomass_column], first_post_covid[biomass_column]], 
                            linestyle='--', color='#0077b6', alpha=0.5, label='COVID-19 Period (No Data)')
                    
                ax.set_title(f"Commercial Fish Biomass - {site_name}")
                ax.set_xlabel("Season")
                ax.set_ylabel("Biomass (kg/ha)")
                
                # Rotate x-axis labels for better readability
                plt.xticks(rotation=45, ha='right')
                
                # Get Y-axis range from graph generator to match web display
                y_range = graph_generator.get_metric_range('Commercial Fish Biomass')
                
                # Set the y-axis limits using the same ranges as the web display
                ax.set_ylim(y_range['min'], y_range['max'])
                
                # Add consistent tick spacing (0, 20, 40, 60, 80, 100)
                ax.set_yticks(range(0, 101, 20))
                
                # Add legend if we have the COVID period line
                if not pre_covid.empty and not post_covid.empty:
                    ax.legend(loc='best')
                    
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                
                # Save to temp file
                biomass_img_path = os.path.join(temp_dir, "biomass.png")
                fig.savefig(biomass_img_path, dpi=150)
                plt.close(fig)
                
                # Add to PDF
                img = Image(biomass_img_path, width=6.5*inch, height=3.5*inch)
                elements.append(img)
                elements.append(Spacer(1, 0.25*inch))
    
    # Process regular metrics
    for metric in metrics:
        metric_data = data_processor.get_metric_data(site_name, metric)
        if not metric_data.empty:
            # Get the standardized metric name
            metric_column = data_processor.METRIC_MAP[metric]
            display_name = data_processor.DISPLAY_NAMES.get(metric_column, metric_column.replace('_', ' ').title())
            
            elements.append(Paragraph(f"{display_name}", styles['Heading2']))
            elements.append(Spacer(1, 0.15*inch))
            
            # Let's print available columns in the DataFrame for debugging
            print(f"Available columns for {metric}: {metric_data.columns.tolist()}")
            
            # Find the actual column containing the metric name
            metric_col = None
            for col in metric_data.columns:
                if metric in col.lower() or col == metric_column:
                    metric_col = col
                    break
            
            # Proceed if we found a matching column
            if metric_col is not None:
                # Create matplotlib figure
                fig, ax = plt.subplots(figsize=(8, 4))
                
                # Add COVID period markers
                covid_start = pd.Timestamp('2019-09-01')
                covid_end = pd.Timestamp('2022-03-01')
                
                # Import season formatting function
                from utils.graph_generator import format_season
                
                # Ensure date column is in datetime format
                metric_data['date'] = pd.to_datetime(metric_data['date'])
                
                # Add season column for x-axis
                metric_data['season'] = metric_data['date'].apply(format_season)
                
                # Split data for pre-COVID and post-COVID
                pre_covid = metric_data[metric_data['date'] < covid_start].sort_values('date')
                post_covid = metric_data[metric_data['date'] > covid_end].sort_values('date')
                
                # Plot pre-COVID data with seasons
                if not pre_covid.empty:
                    ax.plot(pre_covid['season'], pre_covid[metric_col], marker='o', color='#0077b6')
                
                # Plot post-COVID data with seasons
                if not post_covid.empty:
                    ax.plot(post_covid['season'], post_covid[metric_col], marker='o', color='#0077b6')
                
                # Add dotted line for COVID period if applicable
                if not pre_covid.empty and not post_covid.empty:
                    last_pre_covid = pre_covid.iloc[-1]
                    first_post_covid = post_covid.iloc[0]
                    ax.plot([last_pre_covid['season'], first_post_covid['season']], 
                            [last_pre_covid[metric_col], first_post_covid[metric_col]], 
                            linestyle='--', color='#0077b6', alpha=0.5, label='COVID-19 Period (No Data)')
                
                ax.set_title(f"{display_name} - {site_name}")
                ax.set_xlabel("Season")
                
                # Rotate x-axis labels for better readability
                plt.xticks(rotation=45, ha='right')
                
                # Set appropriate y-axis label
                if 'cover' in metric_column.lower():
                    ax.set_ylabel("Cover (%)")
                elif 'density' in metric_column.lower() or 'herbivore' in metric.lower() or 'carnivore' in metric.lower() or 'omnivore' in metric.lower() or 'corallivore' in metric.lower():
                    ax.set_ylabel("Density (ind/ha)")
                elif 'biomass' in metric_column.lower():
                    ax.set_ylabel("Biomass (kg/ha)")
                elif 'bleaching' in metric_column.lower():
                    ax.set_ylabel("Bleaching (%)")
                else:
                    ax.set_ylabel(metric_column.replace('_', ' ').title())
                
                # Get Y-axis range from graph generator to match web display
                # First try with display name
                y_range = graph_generator.get_metric_range(display_name)
                
                # If not found by display name, try with metric name
                if y_range['min'] == 0 and y_range['max'] == 100 and display_name not in ['Hard Coral Cover', 'Fleshy Algae Cover', 'Bleaching', 'Rubble Cover']:
                    y_range = graph_generator.get_metric_range(metric)
                
                # Set the y-axis limits using the same ranges as the web display
                ax.set_ylim(y_range['min'], y_range['max'])
                
                # Set consistent tick spacing based on the metric
                if 'Herbivore' in display_name:
                    ax.set_yticks(range(0, 2501, 500))
                elif 'Carnivore' in display_name or 'Omnivore' in display_name or 'Corallivore' in display_name:
                    ax.set_yticks(range(0, 301, 50))
                elif 'Coral Cover' in display_name or 'Algae Cover' in display_name or 'Bleaching' in display_name or 'Rubble' in display_name:
                    ax.set_yticks(range(0, 101, 20))
                
                # Add legend if we have the COVID period line
                if not pre_covid.empty and not post_covid.empty:
                    ax.legend(loc='best')
                    
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                
                # Save to temp file
                metric_img_path = os.path.join(temp_dir, f"{metric}.png")
                fig.savefig(metric_img_path, dpi=150)
                plt.close(fig)
                
                # Add to PDF
                img = Image(metric_img_path, width=6.5*inch, height=3.5*inch)
                elements.append(img)
                elements.append(Spacer(1, 0.25*inch))
    
    # Add a summary table of latest values if we have data
    included_metrics_with_data = []
    summary_rows = []
    
    # Check biomass data for table
    if include_biomass:
        biomass_data = data_processor.get_biomass_data(site_name)
        if not biomass_data.empty:
            # Find the biomass column
            biomass_column = None
            for col in biomass_data.columns:
                if 'biomass' in col.lower():
                    biomass_column = col
                    break
            
            if biomass_column:
                included_metrics_with_data.append('biomass')
                latest_biomass = biomass_data.sort_values('date', ascending=False).iloc[0]
                
                # Determine trend
                trend = '−'
                if len(biomass_data) > 1:
                    prev_value = biomass_data.sort_values('date', ascending=False).iloc[1][biomass_column]
                    if latest_biomass[biomass_column] > prev_value:
                        trend = '↑'
                    elif latest_biomass[biomass_column] < prev_value:
                        trend = '↓'
                
                summary_rows.append([
                    'Commercial Fish Biomass', 
                    f"{latest_biomass[biomass_column]:.1f} kg/ha",
                    latest_biomass['date'].strftime('%Y-%m-%d'),
                    trend
                ])
    
    # Check other metrics for table
    for metric in metrics:
        metric_data = data_processor.get_metric_data(site_name, metric)
        if not metric_data.empty:
            metric_column = data_processor.METRIC_MAP[metric]
            
            # Find the actual column containing the metric name
            metric_col = None
            for col in metric_data.columns:
                if metric in col.lower() or col == metric_column:
                    metric_col = col
                    break
                
            if metric_col is not None:
                included_metrics_with_data.append(metric)
                latest_data = metric_data.sort_values('date', ascending=False).iloc[0]
                
                # Format value based on metric type
                if 'cover' in metric_col.lower():
                    value_str = f"{latest_data[metric_col]:.1f}%"
                elif 'density' in metric_col.lower() or any(term in metric.lower() for term in ['herbivore', 'carnivore', 'omnivore', 'corallivore']):
                    value_str = f"{latest_data[metric_col]:.1f} ind/ha"
                else:
                    value_str = f"{latest_data[metric_col]:.1f}"
                
                # Determine trend
                trend = '−'
                if len(metric_data) > 1:
                    prev_value = metric_data.sort_values('date', ascending=False).iloc[1][metric_col]
                    if latest_data[metric_col] > prev_value:
                        trend = '↑'
                    elif latest_data[metric_col] < prev_value:
                        trend = '↓'
                
                # Add to table
                display_name = data_processor.DISPLAY_NAMES.get(metric_column, metric_column.replace('_', ' ').title())
                summary_rows.append([
                    display_name,
                    value_str,
                    latest_data['date'].strftime('%Y-%m-%d'),
                    trend
                ])
    
    # Only add the summary table if we have data
    if included_metrics_with_data:
        elements.append(Paragraph("Summary of Latest Data", styles['Heading2']))
        elements.append(Spacer(1, 0.15*inch))
        
        # Create table data with header
        table_data = [['Metric', 'Latest Value', 'Date', 'Trend']]
        table_data.extend(summary_rows)
        
        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
    
    # Add footer with information
    elements.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray
    )
    
    elements.append(Paragraph(
        f"Report generated via Marine Conservation Dashboard on {datetime.now().strftime('%Y-%m-%d')}. " +
        "Data source: Marine Conservation Monitoring Program.",
        footer_style
    ))
    
    # Build the PDF
    doc.build(elements)
    
    # Clean up temp files
    try:
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)
    except:
        pass
    
    # Reset buffer position
    buffer.seek(0)
    return buffer.getvalue()

# Function removed as we now only use the comprehensive PDF report