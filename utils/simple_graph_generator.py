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


def season_sort_key(season_str):
    """
    Generate a sort key for chronological ordering of seasons
    Input format: "MAR-MAY 2020", "DEC-FEB 2020", etc.
    """
    try:
        parts = season_str.split(' ')
        if len(parts) != 2:
            return (9999, 0)  # Unknown seasons sort to end
        
        season_part, year_part = parts
        year = int(year_part)
        
        # Map seasons to chronological order
        season_order = {
            'DEC-FEB': 0,
            'MAR-MAY': 1, 
            'JUN-AUG': 2,
            'SEP-NOV': 3
        }
        
        # For DEC-FEB, the year shown is for February, so DEC is actually previous year
        if season_part == 'DEC-FEB':
            year -= 1  # December is in the previous year
        
        season_num = season_order.get(season_part, 9)
        return (year, season_num)
    except:
        return (9999, 0)  # Error cases sort to end


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
        
        # Check for COVID gap and split data if needed
        covid_start = pd.Timestamp('2020-04-01')  # Apr 2020
        covid_end = pd.Timestamp('2022-03-31')    # Mar 2022
        
        # Split data into pre and post COVID periods
        pre_covid = data[data['date'] < covid_start]
        post_covid = data[data['date'] > covid_end]
        covid_period = data[(data['date'] >= covid_start) & (data['date'] <= covid_end)]
        
        # Plot pre-COVID data if exists
        if not pre_covid.empty:
            fig.add_trace(go.Scatter(
                x=pre_covid['season'],
                y=pre_covid[metric_column],
                name=y_label,
                line=dict(color='#0077b6', width=3, shape='spline', smoothing=0.3),
                mode='lines+markers',
                marker=dict(size=8, color='#0077b6'),
                showlegend=True
            ))
        
        # Plot COVID period data if exists (same style)
        if not covid_period.empty:
            fig.add_trace(go.Scatter(
                x=covid_period['season'],
                y=covid_period[metric_column],
                name=y_label,
                line=dict(color='#0077b6', width=3, shape='spline', smoothing=0.3),
                mode='lines+markers',
                marker=dict(size=8, color='#0077b6'),
                showlegend=False  # Don't duplicate legend
            ))
        
        # Plot post-COVID data if exists
        if not post_covid.empty:
            fig.add_trace(go.Scatter(
                x=post_covid['season'],
                y=post_covid[metric_column],
                name=y_label,
                line=dict(color='#0077b6', width=3, shape='spline', smoothing=1.3),
                mode='lines+markers',
                marker=dict(size=8, color='#0077b6'),
                showlegend=False  # Don't duplicate legend
            ))
        
        # Add COVID gap dotted line if we have data before and after
        if not pre_covid.empty and not post_covid.empty:
            last_pre = pre_covid.iloc[-1]
            first_post = post_covid.iloc[0]
            
            # Check if both Y values are valid (not NaN)
            last_pre_value = last_pre[metric_column]
            first_post_value = first_post[metric_column]
            
            # Only create gap line if both values are valid (not NaN)
            if pd.notna(last_pre_value) and pd.notna(first_post_value):
                fig.add_trace(go.Scatter(
                    x=[last_pre['season'], first_post['season']],
                    y=[last_pre_value, first_post_value],
                    line=dict(color='#cccccc', dash='dot', width=2),
                    mode='lines',
                    name='COVID-19 Period (No Data)',
                    showlegend=True
                ))
        
        # Add "Data Collection Ongoing" indicator for current/future seasons
        if not data.empty:
            current_date = pd.Timestamp.now()
            last_data_point = data.iloc[-1]
            last_data_date = last_data_point['date']
            
            # If the last data point is recent (within 6 months), show ongoing collection
            if (current_date - last_data_date).days < 180:
                # Generate next expected season
                if last_data_date.month in [1, 2]:  # Winter season
                    next_season_date = pd.Timestamp(last_data_date.year, 4, 1)  # Spring
                    next_season = f"MAR-MAY {last_data_date.year}"
                elif last_data_date.month in [4, 5]:  # Spring season  
                    next_season_date = pd.Timestamp(last_data_date.year, 7, 1)  # Summer
                    next_season = f"JUN-AUG {last_data_date.year}"
                elif last_data_date.month in [7, 8]:  # Summer season
                    next_season_date = pd.Timestamp(last_data_date.year, 10, 1)  # Fall
                    next_season = f"SEP-NOV {last_data_date.year}"
                else:  # Fall season
                    next_season_date = pd.Timestamp(last_data_date.year + 1, 1, 1)  # Winter next year
                    next_season = f"DEC-FEB {last_data_date.year + 1}"
                
                # Add dotted line to indicate ongoing data collection
                fig.add_trace(go.Scatter(
                    x=[last_data_point['season'], next_season],
                    y=[last_data_point[metric_column], last_data_point[metric_column]],
                    line=dict(color='#888888', dash='dot', width=1),
                    mode='lines',
                    name='Data Collection Ongoing',
                    showlegend=True
                ))
                
                # Add annotation for ongoing data collection
                fig.add_annotation(
                    x=next_season,
                    y=last_data_point[metric_column],
                    text="Data Collection<br>Ongoing",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="#888888",
                    arrowwidth=1,
                    font=dict(size=10, color="#888888"),
                    bgcolor="white",
                    bordercolor="#888888",
                    borderwidth=1
                )
        
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
        
        # Create chronological ordering for seasons
        # Collect all unique seasons from main data and comparison data
        all_seasons = set()
        if not data.empty:
            all_seasons.update(data['season'].unique())
        
        if comparison_data is not None:
            if not isinstance(comparison_data, list):
                comparison_data = [comparison_data]
            for comp_data in comparison_data:
                if not comp_data.empty and 'season' in comp_data.columns:
                    all_seasons.update(comp_data['season'].unique())
        
        # Sort seasons chronologically
        sorted_seasons = sorted(list(all_seasons), key=lambda x: season_sort_key(x))
        
        # Update layout with proper season ordering
        fig.update_layout(
            title=dict(
                text=title, 
                x=0.5, 
                xanchor='center',
                xref='paper',
                font=dict(size=18, color='#2c3e50')
            ),
            xaxis=dict(
                title="Season",
                showgrid=True,
                gridwidth=1,
                gridcolor='#ecf0f1',
                tickangle=45,
                categoryorder='array',
                categoryarray=sorted_seasons
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
                xanchor="center",
                x=0.5,
                itemsizing="constant",
                font=dict(size=11),
                itemclick="toggleothers",
                itemdoubleclick="toggle",
                tracegroupgap=10
            ),
            hovermode='x unified',
            margin=dict(l=60, r=60, t=120, b=100),
            width=800,
            height=500
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