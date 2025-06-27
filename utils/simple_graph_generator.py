"""
Simple, clean graph generator for marine conservation data
No complex COVID logic, just plot the data as it comes from the database
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime


def format_season(date_obj):
    """Convert date to season format"""
    if pd.isna(date_obj):
        return "Unknown"
    
    year = date_obj.year
    month = date_obj.month
    
    if month in [12, 1, 2]:
        return f"DEC-FEB {year if month == 12 else year}"
    elif month in [3, 4, 5]:
        return f"MAR-MAY {year}"
    elif month in [6, 7, 8]:
        return f"JUN-AUG {year}"
    elif month in [9, 10, 11]:
        return f"SEP-NOV {year}"
    else:
        return f"Unknown {year}"


def generate_filename(title: str, start_date=None, end_date=None) -> str:
    """Generate a filename based on the plot title and date range"""
    # Clean the title for filename
    clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    clean_title = clean_title.replace(' ', '_')
    
    # Add date range if available
    if start_date and end_date:
        start_str = start_date.strftime("%Y-%m") if hasattr(start_date, 'strftime') else str(start_date)[:7]
        end_str = end_date.strftime("%Y-%m") if hasattr(end_date, 'strftime') else str(end_date)[:7]
        return f"{clean_title}_{start_str}_to_{end_str}"
    
    return clean_title


class SimpleGraphGenerator:
    def __init__(self, data_processor):
        self.data_processor = data_processor

    def create_time_series(self, data, title, y_label, comparison_data=None, comparison_labels=None, date_range=None, secondary_data=None, secondary_label=None, tertiary_data=None, tertiary_label=None, show_confidence_interval=False):
        """
        Create a simple time series chart
        Data comes clean from database - just plot it
        """
        
        # Chart configuration
        config = {
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['pan2d', 'select2d', 'lasso2d', 'resetScale2d', 'zoomIn2d', 'zoomOut2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': generate_filename(title),
                'height': 500,
                'width': 800,
                'scale': 2
            }
        }
        
        fig = go.Figure()
        
        # Handle empty data
        if data.empty:
            fig.add_annotation(
                text="No data available for the selected period",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            return fig, config

        # Simple data preparation
        data['date'] = pd.to_datetime(data['date'])
        data = data.sort_values('date')
        
        # Get the metric column (should be the second column)
        metric_column = data.columns[1]
        
        # Format seasons for display
        data['season'] = data['date'].apply(format_season)
        
        # Apply date range filter if provided
        if date_range and len(date_range) == 2:
            start_filter, end_filter = date_range
            if start_filter and end_filter:
                start_dt = pd.to_datetime(start_filter)
                end_dt = pd.to_datetime(end_filter)
                data = data[(data['date'] >= start_dt) & (data['date'] <= end_dt)]
        
        # Plot the main data
        fig.add_trace(go.Scatter(
            x=data['season'],
            y=data[metric_column],
            name=y_label,
            line=dict(color='#0077b6', width=3),
            mode='lines+markers',
            marker=dict(size=8, color='#0077b6')
        ))
        
        # Add comparison data if provided
        if comparison_data is not None:
            if not isinstance(comparison_data, list):
                comparison_data = [comparison_data]
                comparison_labels = [comparison_labels] if comparison_labels else ["Comparison"]
            
            colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57']
            
            for i, comp_data in enumerate(comparison_data):
                if not comp_data.empty:
                    comp_data['date'] = pd.to_datetime(comp_data['date'])
                    comp_data = comp_data.sort_values('date')
                    comp_metric_column = comp_data.columns[1]
                    comp_data['season'] = comp_data['date'].apply(format_season)
                    
                    # Apply same date filter
                    if date_range and len(date_range) == 2:
                        start_filter, end_filter = date_range
                        if start_filter and end_filter:
                            start_dt = pd.to_datetime(start_filter)
                            end_dt = pd.to_datetime(end_filter)
                            comp_data = comp_data[(comp_data['date'] >= start_dt) & (comp_data['date'] <= end_dt)]
                    
                    color = colors[i % len(colors)]
                    label = comparison_labels[i] if i < len(comparison_labels) else f"Comparison {i+1}"
                    
                    fig.add_trace(go.Scatter(
                        x=comp_data['season'],
                        y=comp_data[comp_metric_column],
                        name=label,
                        line=dict(color=color, width=2, dash='dash'),
                        mode='lines+markers',
                        marker=dict(size=6, color=color)
                    ))
        
        # Update layout
        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=18, color='#2c3e50')),
            xaxis=dict(
                title="Season",
                showgrid=True,
                gridwidth=1,
                gridcolor='#ecf0f1',
                tickangle=45
            ),
            yaxis=dict(
                title=y_label,
                showgrid=True,
                gridwidth=1,
                gridcolor='#ecf0f1'
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial, sans-serif", size=12, color='#2c3e50'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='x unified',
            margin=dict(l=60, r=60, t=80, b=100)
        )
        
        return fig, config

    def create_eco_tourism_chart(self, data, title, observation_type='percentage'):
        """Create bar chart for eco-tourism data (placeholder)"""
        fig = go.Figure()
        fig.add_annotation(
            text="Eco-tourism charts not yet implemented in simple generator",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig
    
    def create_site_comparison_heatmap(self, matrix_data, metric_column, title=None):
        """Create heatmap for site comparison (placeholder)"""
        fig = go.Figure()
        fig.add_annotation(
            text="Heatmap charts not yet implemented in simple generator",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig
    
    def create_geographic_visualization(self, sites_data, metric_column, title=None):
        """Create geographic visualization (placeholder)"""
        fig = go.Figure()
        fig.add_annotation(
            text="Geographic charts not yet implemented in simple generator",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig
    
    def create_multi_site_trend_chart(self, trend_data, metric_name, group_by_municipality=False, highlight_sites=None):
        """Create multi-site trend chart (placeholder)"""
        fig = go.Figure()
        fig.add_annotation(
            text="Multi-site trend charts not yet implemented in simple generator",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig
    
    def create_municipality_grouped_bar_chart(self, matrix_data, metric_column, title=None, y_axis_label=None):
        """Create municipality grouped bar chart (placeholder)"""
        fig = go.Figure()
        fig.add_annotation(
            text="Municipality bar charts not yet implemented in simple generator",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        return fig