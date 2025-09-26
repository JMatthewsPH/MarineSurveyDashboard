"""
Summary Dashboard Graph Generator

Specialized graph generator for Summary Dashboard with comprehensive visualization capabilities.
Includes all necessary methods for site comparison matrices, trend analysis, and geographic visualizations.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def generate_filename(title):
    """Generate a clean filename from chart title"""
    if not title:
        return "marine_conservation_chart"
    # Remove special characters and replace spaces with underscores
    clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    return clean_title.replace(' ', '_').lower()

def format_season(date_obj):
    """Format date to season string (e.g., 'Spring 2020')"""
    if pd.isna(date_obj):
        return ""
    
    try:
        date_obj = pd.to_datetime(date_obj)
        year = date_obj.year
        month = date_obj.month
        
        if month in [3, 4, 5]:  # MAR-MAY
            return f"Spring {year}"
        elif month in [6, 7, 8]:  # JUN-AUG
            return f"Summer {year}"
        elif month in [9, 10, 11]:  # SEP-NOV
            return f"Fall {year}"
        else:  # DEC-FEB (winter spans years)
            if month == 12:
                return f"Winter {year}/{year+1}"
            else:
                return f"Winter {year-1}/{year}"
    except:
        return str(date_obj)

class SummaryGraphGenerator:
    def __init__(self, data_processor):
        self.data_processor = data_processor

    def create_municipality_grouped_bar_chart(self, matrix_data, metric_column, title=None, y_axis_label=None, hide_colorbar=False):
        """
        Create a bar chart with sites grouped by municipality, using red-yellow-green color coding
        for health indicators, starting Y-axis from 0
        
        Args:
            matrix_data: DataFrame with site, municipality, and metric columns
            metric_column: Column name to visualize
            title: Optional title for the chart
            y_axis_label: Label for Y-axis including units
            hide_colorbar: Boolean to hide colorbar for mobile optimization
        """
        try:
            # Clean the data - track which sites have no data vs zero values
            clean_data = matrix_data.copy()
            
            # Identify sites with genuine null/NaN values (no data) vs actual zeros
            no_data_sites = clean_data[clean_data[metric_column].isna()]['site'].tolist()
            
            # Convert coral cover and algae cover from decimals to percentages
            if 'coral' in metric_column.lower() or 'algae' in metric_column.lower() or 'bleaching' in metric_column.lower() or 'rubble' in metric_column.lower():
                clean_data[metric_column] = clean_data[metric_column] * 100
            
            # Replace NaN with 0 for visualization purposes
            clean_data[metric_column] = clean_data[metric_column].fillna(0)
            
            # Add a column to track data availability for hover information
            clean_data['has_data'] = ~matrix_data[metric_column].isna()
            
            if clean_data.empty:
                # Return empty chart if no data
                fig = go.Figure()
                fig.add_annotation(
                    text="No data available for this metric",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=16, color="gray")
                )
                fig.update_layout(
                    title=title or "No Data Available",
                    height=400,
                    template="plotly_white"
                )
                config = {'displaylogo': False, 'responsive': True}
                return fig, config
            
            # Sort by municipality and then by site name for consistent ordering
            clean_data = clean_data.sort_values(['municipality', 'site'])
            
            # Use full site names (no abbreviations)
            clean_data['site_label'] = clean_data['site']
            
            # Determine color mapping based on metric values and ecological thresholds
            actual_min_val = clean_data[metric_column].min()
            actual_max_val = clean_data[metric_column].max()
            
            # Use ecologically meaningful thresholds for biomass instead of dynamic scaling
            if 'biomass' in metric_column.lower():
                # Fixed ecological thresholds: 0=red, 20=green, 20+=green
                min_val = 0
                max_val = max(20, actual_max_val)  # Ensure scale goes to at least 20
                colorscale = 'RdYlGn'  # Red-Yellow-Green
            elif 'coral' in metric_column.lower():
                # For coral cover, use percentage-based thresholds (0-100%)
                min_val = 0
                max_val = max(50, actual_max_val)  # Scale to at least 50% for coral
                colorscale = 'RdYlGn'  # Red-Yellow-Green  
            elif 'bleaching' in metric_column.lower() or 'algae' in metric_column.lower():
                # Lower values are better (reverse scale)
                min_val = actual_min_val
                max_val = actual_max_val
                colorscale = 'RdYlGn_r'  # Green-Yellow-Red (reversed)
            else:
                # Default to red-yellow-green for most metrics with dynamic scaling
                min_val = actual_min_val
                max_val = actual_max_val
                colorscale = 'RdYlGn'
            
            # Create the bar chart with color mapping (no title here - will be set in update_layout)
            fig = px.bar(
                clean_data,
                x='site_label',
                y=metric_column,
                color=metric_column,
                color_continuous_scale=colorscale,
                range_color=[min_val, max_val],  # Use ecological thresholds for biomass, data range for others
                labels={
                    'site_label': 'Site',
                    metric_column: y_axis_label or metric_column.replace('_', ' ').title()
                },
                hover_data=['municipality']
            )
            
            # Customize the layout with centered title and responsive design
            fig.update_layout(
                title={
                    'text': title or f"Site Comparison: {metric_column.replace('_', ' ').title()}",
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'size': 18}
                },
                height=600,  # Increased height for mobile readability
                template="plotly_white",
                margin=dict(l=60, r=60, t=100, b=160),  # Increased bottom margin for rotated labels
                autosize=True,  # Enable responsive resizing
                hovermode='closest',  # Use closest point hover instead of unified
                xaxis=dict(
                    title="Sites (Grouped by Municipality)",
                    tickangle=-45,  # Diagonal labels for better readability
                    tickmode='linear',
                    tickfont=dict(size=10)
                ),
                yaxis=dict(
                    title=y_axis_label or metric_column.replace('_', ' ').title(),
                    range=[0, max_val * 1.1] if max_val > 0 else [0, 0],  # Start from 0, add 10% padding at top
                    gridcolor='lightgray'
                ),
                showlegend=False,  # Hide color legend to save space
                coloraxis=dict(
                    showscale=not hide_colorbar,  # Hide colorbar on mobile when requested
                    colorbar=dict(
                        len=1.10,  # 20 pixels longer in height total
                        thickness=20,  # Back to standard thickness
                        x=1.02,  # Position to the right
                        y=-0.04,  # Start lower to accommodate extra length
                        yanchor='bottom'
                    ) if not hide_colorbar else dict()  # Empty dict if hiding colorbar
                )
            )
            
            # Add municipality group separators
            municipalities = clean_data['municipality'].unique()
            x_pos = 0
            for i, municipality in enumerate(municipalities):
                muni_data = clean_data[clean_data['municipality'] == municipality]
                sites_in_muni = len(muni_data)
                
                # Add vertical line to separate municipalities (except before first)
                if i > 0:
                    fig.add_vline(
                        x=x_pos - 0.5,
                        line_width=2,
                        line_dash="dash",
                        line_color="gray",
                        opacity=0.5
                    )
                
                # Add municipality label
                fig.add_annotation(
                    x=x_pos + (sites_in_muni - 1) / 2,
                    y=max_val * 1.05 if max_val > 0 else 5,
                    text=f"<b>{municipality}</b>",
                    showarrow=False,
                    font=dict(size=12, color="darkblue"),
                    yref="y"
                )
                
                x_pos += sites_in_muni
            
            # Enhanced hover template with data availability information
            if 'biomass' in metric_column.lower():
                hover_template = "<b>%{x}</b><br>Municipality: %{customdata[0]}<br>" + \
                               "Biomass: %{y:.1f} kg/150m²<br>" + \
                               "<i>%{customdata[1]}</i><extra></extra>"
            elif 'coral' in metric_column.lower() or 'algae' in metric_column.lower():
                hover_template = "<b>%{x}</b><br>Municipality: %{customdata[0]}<br>" + \
                               "Cover: %{y:.1f}%<br>" + \
                               "<i>%{customdata[1]}</i><extra></extra>"
            elif 'density' in metric_column.lower():
                hover_template = "<b>%{x}</b><br>Municipality: %{customdata[0]}<br>" + \
                               "Density: %{y:.1f} ind/ha<br>" + \
                               "<i>%{customdata[1]}</i><extra></extra>"
            else:
                hover_template = "<b>%{x}</b><br>Municipality: %{customdata[0]}<br>" + \
                               "Value: %{y:.1f}<br>" + \
                               "<i>%{customdata[1]}</i><extra></extra>"
            
            # Prepare custom data with municipality and data availability status
            clean_data['data_status'] = clean_data['has_data'].apply(
                lambda x: "Data available" if x else "No data in database"
            )
            
            fig.update_traces(
                hovertemplate=hover_template,
                customdata=clean_data[['municipality', 'data_status']].values
            )
            
            # Configure download settings with standard plotly settings
            config = {
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': generate_filename(title or f"Site_Comparison_{metric_column}"),
                    'height': 800,
                    'width': 1200,
                    'scale': 2
                },
                'displaylogo': False,
                'responsive': True,
                'displayModeBar': True,
                'modeBarButtons': [['zoomIn2d', 'zoomOut2d', 'resetScale2d', 'toImage']],
                'scrollZoom': False,
                'doubleClick': 'reset'
            }
            
            return fig, config
            
        except Exception as e:
            logger.error(f"Error creating municipality grouped bar chart: {str(e)}")
            # Return a simple error chart
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color="red")
            )
            config = {'displaylogo': False, 'responsive': True}
            return fig, config

    def create_site_comparison_heatmap(self, matrix_data, metric_column, title=None):
        """
        Create a heatmap visualization for site comparison
        
        Args:
            matrix_data: DataFrame with site, municipality, and metric columns
            metric_column: Column name to visualize
            title: Optional title for the chart
        """
        try:
            # Clean the data - replace NaN with 0
            clean_data = matrix_data.copy()
            clean_data[metric_column] = clean_data[metric_column].fillna(0)
            
            if clean_data.empty:
                # Return empty chart if no data
                fig = go.Figure()
                fig.add_annotation(
                    text="No data available for this metric",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=16, color="gray")
                )
                config = {'displaylogo': False, 'responsive': True}
                return fig, config
            
            # Sort by municipality and site for consistent ordering
            clean_data = clean_data.sort_values(['municipality', 'site'])
            
            # Create a matrix structure for heatmap
            # Group by municipality for better visualization
            municipalities = clean_data['municipality'].unique()
            
            # Create the heatmap data
            z_data = []
            y_labels = []
            
            for municipality in municipalities:
                muni_data = clean_data[clean_data['municipality'] == municipality]
                for _, row in muni_data.iterrows():
                    z_data.append([row[metric_column]])
                    y_labels.append(f"{row['site']} ({municipality})")
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=z_data,
                y=y_labels,
                x=[metric_column.replace('_', ' ').title()],
                colorscale='RdYlGn' if 'biomass' in metric_column.lower() or 'coral' in metric_column.lower() else 'RdYlGn_r',
                hoverongaps=False,
                hovertemplate="<b>%{y}</b><br>Value: %{z:.1f}<extra></extra>"
            ))
            
            fig.update_layout(
                title=title or f"Site Comparison Heatmap: {metric_column.replace('_', ' ').title()}",
                height=600,
                template="plotly_white",
                margin=dict(l=200, r=60, t=80, b=60),
                yaxis=dict(title="Sites"),
                xaxis=dict(title="Metric")
            )
            
            config = {
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': generate_filename(title or f"Heatmap_{metric_column}"),
                    'height': 800,
                    'width': 1000,
                    'scale': 2
                },
                'displaylogo': False,
                'responsive': True
            }
            
            return fig, config
            
        except Exception as e:
            logger.error(f"Error creating heatmap: {str(e)}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating heatmap: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color="red")
            )
            config = {'displaylogo': False, 'responsive': True}
            return fig, config

    def create_municipal_trend_chart(self, trend_data, metric_name, group_by_all_sites=False, municipality_focus=None):
        """
        Create a municipal-level trend chart for Summary Dashboard broad overview
        
        Args:
            trend_data: DataFrame with columns: date, metric_value, site, municipality
            metric_name: Name of the metric being displayed  
            group_by_all_sites: Whether to show overall average across all municipalities
            municipality_focus: Specific municipality to focus on (Zamboanguita, Siaton, Santa Catalina)
        """
        try:
            if trend_data.empty:
                fig = go.Figure()
                fig.add_annotation(
                    text="No trend data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=16, color="gray")
                )
                config = {'displaylogo': False, 'responsive': True}
                return fig, config
            
            # Ensure date is datetime
            trend_data['date'] = pd.to_datetime(trend_data['date'])
            
            # Convert coral cover and algae cover from decimals to percentages for proper display
            if any(term in metric_name.lower() for term in ['coral', 'algae', 'bleaching', 'rubble']):
                # Find the metric column and convert it to percentage
                for col in trend_data.columns:
                    if col not in ['date', 'site', 'municipality'] and trend_data[col].dtype in ['float64', 'int64']:
                        trend_data[col] = trend_data[col] * 100
            
            # Find the metric column
            metric_col = None
            for col in trend_data.columns:
                if col.lower() in [metric_name.lower(), metric_name.lower().replace(' ', '_')]:
                    metric_col = col
                    break
            
            if metric_col is None:
                # Look for numeric columns that aren't date, site, or municipality
                numeric_cols = trend_data.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    if col not in ['site', 'municipality']:
                        metric_col = col
                        break
            
            if metric_col is None:
                raise ValueError(f"Could not find metric column for {metric_name}")
            
            fig = go.Figure()
            
            # COVID period markers
            covid_start = pd.Timestamp('2020-04-01')
            covid_end = pd.Timestamp('2022-03-01')
            
            # Define municipality colors for consistency
            municipality_colors = {
                'Zamboanguita': '#2E8B57',  # Sea Green
                'Siaton': '#4682B4',        # Steel Blue  
                'Santa Catalina': '#CD853F' # Peru
            }
            
            if group_by_all_sites:
                # Show overall average across all municipalities
                all_avg = trend_data.groupby('date')[metric_col].mean().reset_index()
                
                fig.add_trace(go.Scatter(
                    x=all_avg['date'],
                    y=all_avg[metric_col],
                    mode='lines+markers',
                    name="All Municipalities Average",
                    line=dict(
                        color='#1f77b4',
                        width=3,
                        shape='spline',
                        smoothing=1.3
                    ),
                    marker=dict(size=6, color='#1f77b4'),
                    hovertemplate='<b>All Municipalities</b><br>' +
                                  'Date: %{x}<br>' +
                                  f'{metric_name}: %{{y:.1f}}<br>' +
                                  '<extra></extra>'
                ))
            elif municipality_focus:
                # Show specific municipality average
                muni_data = trend_data[trend_data['municipality'] == municipality_focus]
                if not muni_data.empty:
                    muni_avg = muni_data.groupby('date')[metric_col].mean().reset_index()
                    
                    fig.add_trace(go.Scatter(
                        x=muni_avg['date'],
                        y=muni_avg[metric_col],
                        mode='lines+markers',
                        name=f"{municipality_focus} Average",
                        line=dict(
                            color=municipality_colors.get(municipality_focus, '#1f77b4'),
                            width=3,
                            shape='spline',
                            smoothing=1.3
                        ),
                        marker=dict(size=6, color=municipality_colors.get(municipality_focus, '#1f77b4')),
                        hovertemplate=f'<b>{municipality_focus}</b><br>' +
                                      'Date: %{x}<br>' +
                                      f'{metric_name}: %{{y:.1f}}<br>' +
                                      '<extra></extra>'
                    ))
            else:
                # Show all three municipalities as separate averages
                for municipality in ['Zamboanguita', 'Siaton', 'Santa Catalina']:
                    muni_data = trend_data[trend_data['municipality'] == municipality]
                    if not muni_data.empty:
                        muni_avg = muni_data.groupby('date')[metric_col].mean().reset_index()
                        
                        fig.add_trace(go.Scatter(
                            x=muni_avg['date'],
                            y=muni_avg[metric_col],
                            mode='lines+markers',
                            name=f"{municipality}",
                            line=dict(
                                color=municipality_colors.get(municipality, '#1f77b4'),
                                width=2.5,
                                shape='spline',
                                smoothing=1.3
                            ),
                            marker=dict(size=5, color=municipality_colors.get(municipality, '#1f77b4')),
                            hovertemplate=f'<b>{municipality}</b><br>' +
                                          'Date: %{x}<br>' +
                                          f'{metric_name}: %{{y:.1f}}<br>' +
                                          '<extra></extra>'
                        ))
            
            # Add COVID-19 shaded region
            fig.add_vrect(
                x0=covid_start, x1=covid_end,
                fillcolor="rgba(255, 200, 200, 0.3)",
                layer="below",
                line_width=0,
                annotation_text="COVID-19 Impact Period",
                annotation_position="top left",
                annotation=dict(font_size=10, font_color="red")
            )
            
            # Update layout for municipal overview styling
            title_text = f"Municipal {metric_name} Trends - Historic Overview"
            if municipality_focus:
                title_text = f"{municipality_focus} {metric_name} Trends - Municipal Average"
            
            fig.update_layout(
                title=dict(
                    text=title_text,
                    x=0.5,
                    xanchor='center',
                    font=dict(size=16, color='#2c3e50')
                ),
                xaxis=dict(
                    title="Date",
                    showgrid=True,
                    gridcolor='rgba(128,128,128,0.2)',
                    title_font=dict(size=12, color='#2c3e50'),
                    tickfont=dict(size=10, color='#2c3e50')
                ),
                yaxis=dict(
                    title=f"{metric_name}",
                    showgrid=True,
                    gridcolor='rgba(128,128,128,0.2)',
                    title_font=dict(size=12, color='#2c3e50'),
                    tickfont=dict(size=10, color='#2c3e50'),
                    rangemode='tozero'
                ),
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    x=0.5,
                    xanchor='center',
                    y=1.02,
                    yanchor='bottom',
                    bgcolor="rgba(255, 255, 255, 0.8)",
                    bordercolor="rgba(0, 0, 0, 0.2)",
                    borderwidth=1
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=60, r=40, t=80, b=60),
                showlegend=True,
                height=400  # Set reasonable height to prevent overflow
            )
            
            config = {
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                'responsive': True,
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': generate_filename(f"municipal_{metric_name}_trends"),
                    'height': 600,
                    'width': 1000,
                    'scale': 2
                }
            }
            
            return fig, config
            
        except Exception as e:
            logger.error(f"Error creating municipal trend chart: {str(e)}")
            # Return empty figure with error message
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error loading trend data: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color="red")
            )
            config = {'displaylogo': False, 'responsive': True}
            return fig, config

    def create_multi_site_trend_chart(self, trend_data, metric_name, group_by_municipality=False, highlight_sites=None, group_by_all_sites=False):
        """
        Create a multi-site trend chart for the Summary Dashboard
        
        Args:
            trend_data: DataFrame with columns: date, metric_value, site, municipality
            metric_name: Name of the metric being displayed
            group_by_municipality: Whether to group lines by municipality
            highlight_sites: List of sites to highlight
            group_by_all_sites: Whether to show overall average across all sites
        """
        try:
            if trend_data.empty:
                fig = go.Figure()
                fig.add_annotation(
                    text="No trend data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=16, color="gray")
                )
                config = {'displaylogo': False, 'responsive': True}
                return fig, config
            
            # Ensure date is datetime
            trend_data['date'] = pd.to_datetime(trend_data['date'])
            
            # Determine the metric column name (it could be metric_name or a variation)
            metric_col = None
            for col in trend_data.columns:
                if col.lower() in [metric_name.lower(), metric_name.lower().replace(' ', '_')]:
                    metric_col = col
                    break
            
            # If exact match not found, try to find the value column
            if metric_col is None:
                # Look for numeric columns that aren't date, site, or municipality
                numeric_cols = trend_data.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    if col not in ['site', 'municipality']:
                        metric_col = col
                        break
            
            if metric_col is None:
                raise ValueError(f"Could not find metric column for {metric_name}")
            
            fig = go.Figure()
            
            # COVID period markers
            covid_start = pd.Timestamp('2020-04-01')
            covid_end = pd.Timestamp('2022-03-01')
            
            if group_by_all_sites:
                # Show overall average across all sites
                all_sites_avg = trend_data.groupby('date')[metric_col].mean().reset_index()
                
                fig.add_trace(go.Scatter(
                    x=all_sites_avg['date'],
                    y=all_sites_avg[metric_col],
                    mode='lines+markers',
                    name="All Sites Average",
                    line=dict(
                        color='#1f77b4',
                        width=3,
                        shape='spline',
                        smoothing=1.3
                    ),
                    marker=dict(size=8, line=dict(width=1, color='white')),
                    hovertemplate=f"All Sites Average<br>Date: %{{x}}<br>{metric_name}: %{{y:.1f}}<extra></extra>"
                ))
            elif group_by_municipality:
                # Group by municipality
                municipalities = trend_data['municipality'].unique()
                colors = px.colors.qualitative.Set3[:len(municipalities)]
                
                for i, municipality in enumerate(municipalities):
                    muni_data = trend_data[trend_data['municipality'] == municipality]
                    
                    # Calculate average for this municipality
                    muni_avg = muni_data.groupby('date')[metric_col].mean().reset_index()
                    
                    fig.add_trace(go.Scatter(
                        x=muni_avg['date'],
                        y=muni_avg[metric_col],
                        mode='lines+markers',
                        name=f"{municipality} Average",
                        line=dict(color=colors[i % len(colors)], width=3, shape='spline', smoothing=1.3),
                        marker=dict(size=6)
                    ))
            else:
                # Show individual sites
                sites = trend_data['site'].unique()
                colors = px.colors.qualitative.Set1
                
                for i, site in enumerate(sites):
                    site_data = trend_data[trend_data['site'] == site].sort_values('date')
                    
                    # Determine line style and opacity based on highlighting
                    if highlight_sites and site in highlight_sites:
                        line_width = 4
                        opacity = 1.0
                        marker_size = 8
                    elif highlight_sites and site not in highlight_sites:
                        line_width = 1
                        opacity = 0.3
                        marker_size = 4
                    else:
                        line_width = 2
                        opacity = 0.8
                        marker_size = 6
                    
                    fig.add_trace(go.Scatter(
                        x=site_data['date'],
                        y=site_data[metric_col],
                        mode='lines+markers',
                        name=site,
                        line=dict(color=colors[i % len(colors)], width=line_width, shape='spline', smoothing=1.3),
                        marker=dict(size=marker_size),
                        opacity=opacity
                    ))
            
            # Add COVID period shading
            fig.add_vrect(
                x0=covid_start, x1=covid_end,
                fillcolor="gray", opacity=0.2,
                layer="below", line_width=0,
                annotation_text="COVID Period",
                annotation_position="top left"
            )
            
            # Update layout with centered title and responsive design
            y_title = "Commercial Biomass (kg/150m²)" if "biomass" in metric_name.lower() else metric_name
            
            fig.update_layout(
                title={
                    'text': f"Trend Analysis: {metric_name}",
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'size': 18}
                },
                xaxis_title="Date",
                yaxis_title=y_title,
                height=500,
                template="plotly_white",
                margin=dict(l=60, r=60, t=100, b=60),  # More top margin for centered title
                autosize=True,  # Enable responsive resizing
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                )
            )
            
            config = {
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': generate_filename(f"Trend_{metric_name}"),
                    'height': 600,
                    'width': 1000,
                    'scale': 2
                },
                'displaylogo': False,
                'responsive': True
            }
            
            return fig, config
            
        except Exception as e:
            logger.error(f"Error creating multi-site trend chart: {str(e)}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating trend chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color="red")
            )
            config = {'displaylogo': False, 'responsive': True}
            return fig, config