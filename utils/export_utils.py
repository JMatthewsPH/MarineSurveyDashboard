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
    # Extract data from plotly fig
    fig_data = fig.data[0]
    
    # Create Matplotlib figure
    mpl_fig, ax = plt.subplots(figsize=(8, 5))
    
    # Determine plot type and add data
    if fig_data.type == 'scatter':
        ax.plot(fig_data.x, fig_data.y, marker='o')
    elif fig_data.type == 'bar':
        ax.bar(fig_data.x, fig_data.y)
    
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
    
    # Add date and description
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Paragraph("This report contains selected metrics for the specified marine conservation site.", styles['Normal']))
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
                ax.plot(biomass_data['date'], biomass_data[biomass_column], marker='o')
                ax.set_title(f"Commercial Fish Biomass - {site_name}")
                ax.set_xlabel("Date")
                ax.set_ylabel("Biomass (kg/ha)")
                
                # Get Y-axis range from graph generator to match web display
                y_range = graph_generator.get_metric_range('Commercial Fish Biomass')
                
                # Set the y-axis limits using the same ranges as the web display
                ax.set_ylim(y_range['min'], y_range['max'])
                
                # Add consistent tick spacing (0, 20, 40, 60, 80, 100)
                ax.set_yticks(range(0, 101, 20))
                
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
                ax.plot(metric_data['date'], metric_data[metric_col], marker='o')
                ax.set_title(f"{display_name} - {site_name}")
                ax.set_xlabel("Date")
                
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

def add_chart_export_button(fig, container, site_name, title):
    """
    Add a button to export a chart as PDF
    
    Args:
        fig: Plotly figure object
        container: Streamlit container to place the button
        site_name: Name of the site for the chart title
        title: Chart title
    """
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{site_name}_{title.replace(' ', '_').lower()}_{timestamp}.pdf"
    
    # Create PDF
    pdf_bytes = generate_single_chart_pdf(fig, title, site_name)
    
    # Add download button
    container.download_button(
        label="Export Chart as PDF",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
    )