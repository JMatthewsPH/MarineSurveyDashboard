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

    def create_time_series(self, data, title, y_label, comparison_data=None, comparison_labels=None, date_range=None, secondary_data=None, secondary_label=None, tertiary_data=None, tertiary_label=None, show_confidence_interval=False, show_error_bars=False, use_straight_lines=False):
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
        
        # Get the metric column (column order: date, season, metric, then statistical columns)
        metric_column = data.columns[2] if len(data.columns) > 2 else data.columns[1]
        
        # Convert decimal values to percentages for percentage-based metrics
        # Note: Use 'coral_cover' not 'coral' to avoid matching 'corallivore_density'
        is_percentage = 'coral_cover' in metric_column.lower() or 'algae' in metric_column.lower() or 'bleaching' in metric_column.lower() or 'rubble' in metric_column.lower()
        if is_percentage:
            data[metric_column] = data[metric_column] * 100
            # Also convert statistical columns to percentages
            for suffix in ['_ci_low', '_ci_high', '_eb_low', '_eb_high', '_sd']:
                stat_col = f'{metric_column}{suffix}'
                if stat_col in data.columns:
                    data[stat_col] = data[stat_col] * 100
        
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
        
        # Configure line style based on user preference
        line_style = {
            'color': '#0077b6',
            'width': 3
        }
        
        # Add smooth curves unless straight lines are requested
        if not use_straight_lines:
            line_style['shape'] = 'spline'
            line_style['smoothing'] = 1.3
        
        # Prepare error bar settings if requested
        error_y_settings = None
        if show_error_bars and not data.empty:
            # Check if error bar columns exist
            eb_low_col = f'{metric_column}_eb_low'
            eb_high_col = f'{metric_column}_eb_high'
            sd_col = f'{metric_column}_sd'
            
            if eb_low_col in data.columns and eb_high_col in data.columns:
                # Use asymmetric error bars from database
                error_minus = data[metric_column] - data[eb_low_col]
                error_plus = data[eb_high_col] - data[metric_column]
                error_y_settings = dict(
                    type='data',
                    symmetric=False,
                    array=error_plus,
                    arrayminus=error_minus,
                    visible=True,
                    color='rgba(0, 119, 182, 0.5)',
                    thickness=2,
                    width=3
                )
            elif sd_col in data.columns:
                # Fallback to standard deviation
                error_y_settings = dict(
                    type='data',
                    array=data[sd_col],
                    visible=True,
                    color='rgba(0, 119, 182, 0.5)',
                    thickness=2,
                    width=3
                )
        
        # Add confidence intervals if requested (mutually exclusive with error bars)
        if show_confidence_interval and not show_error_bars and not data.empty:
            ci_low_col = f'{metric_column}_ci_low'
            ci_high_col = f'{metric_column}_ci_high'
            
            if ci_low_col in data.columns and ci_high_col in data.columns:
                # Add CI for each data period (pre-COVID, COVID, post-COVID)
                for period_data in [pre_covid, covid_period, post_covid]:
                    if not period_data.empty:
                        # Filter to rows with CI data
                        has_ci = period_data[ci_low_col].notna() & period_data[ci_high_col].notna()
                        if has_ci.any():
                            ci_data = period_data[has_ci]
                            # Add upper bound
                            fig.add_trace(go.Scatter(
                                x=ci_data['season'],
                                y=ci_data[ci_high_col],
                                mode='lines',
                                line=dict(width=0),
                                showlegend=False,
                                hoverinfo='skip'
                            ))
                            # Add lower bound with fill
                            fig.add_trace(go.Scatter(
                                x=ci_data['season'],
                                y=ci_data[ci_low_col],
                                mode='lines',
                                line=dict(width=0),
                                fill='tonexty',
                                fillcolor='rgba(0, 119, 182, 0.2)',
                                showlegend=False,
                                name='95% Confidence Interval',
                                hoverinfo='skip'
                            ))
        
        # Track whether we've shown the main data series in the legend
        main_legend_shown = False
        
        # Plot pre-COVID data if exists
        if not pre_covid.empty:
            trace_args = {
                'x': pre_covid['season'],
                'y': pre_covid[metric_column],
                'name': y_label,
                'line': line_style,
                'mode': 'lines+markers',
                'marker': dict(size=8, color='#0077b6'),
                'showlegend': True
            }
            if error_y_settings and not show_confidence_interval:
                # Filter error bar settings for pre-COVID period
                pre_covid_indices = pre_covid.index
                if error_y_settings.get('symmetric', True):
                    trace_args['error_y'] = {
                        'type': 'data',
                        'array': error_y_settings['array'][pre_covid_indices],
                        'visible': True,
                        'color': error_y_settings['color'],
                        'thickness': error_y_settings['thickness'],
                        'width': error_y_settings['width']
                    }
                else:
                    trace_args['error_y'] = {
                        'type': 'data',
                        'symmetric': False,
                        'array': error_y_settings['array'][pre_covid_indices],
                        'arrayminus': error_y_settings['arrayminus'][pre_covid_indices],
                        'visible': True,
                        'color': error_y_settings['color'],
                        'thickness': error_y_settings['thickness'],
                        'width': error_y_settings['width']
                    }
            fig.add_trace(go.Scatter(**trace_args))
            main_legend_shown = True
        
        # Plot COVID period data if exists (same style)
        if not covid_period.empty:
            trace_args = {
                'x': covid_period['season'],
                'y': covid_period[metric_column],
                'name': y_label,
                'line': line_style,
                'mode': 'lines+markers',
                'marker': dict(size=8, color='#0077b6'),
                'showlegend': not main_legend_shown
            }
            if error_y_settings and not show_confidence_interval:
                covid_indices = covid_period.index
                if error_y_settings.get('symmetric', True):
                    trace_args['error_y'] = {
                        'type': 'data',
                        'array': error_y_settings['array'][covid_indices],
                        'visible': True,
                        'color': error_y_settings['color'],
                        'thickness': error_y_settings['thickness'],
                        'width': error_y_settings['width']
                    }
                else:
                    trace_args['error_y'] = {
                        'type': 'data',
                        'symmetric': False,
                        'array': error_y_settings['array'][covid_indices],
                        'arrayminus': error_y_settings['arrayminus'][covid_indices],
                        'visible': True,
                        'color': error_y_settings['color'],
                        'thickness': error_y_settings['thickness'],
                        'width': error_y_settings['width']
                    }
            fig.add_trace(go.Scatter(**trace_args))
            if not main_legend_shown:
                main_legend_shown = True
        
        # Plot post-COVID data if exists
        if not post_covid.empty:
            trace_args = {
                'x': post_covid['season'],
                'y': post_covid[metric_column],
                'name': y_label,
                'line': line_style,
                'mode': 'lines+markers',
                'marker': dict(size=8, color='#0077b6'),
                'showlegend': not main_legend_shown
            }
            if error_y_settings and not show_confidence_interval:
                post_covid_indices = post_covid.index
                if error_y_settings.get('symmetric', True):
                    trace_args['error_y'] = {
                        'type': 'data',
                        'array': error_y_settings['array'][post_covid_indices],
                        'visible': True,
                        'color': error_y_settings['color'],
                        'thickness': error_y_settings['thickness'],
                        'width': error_y_settings['width']
                    }
                else:
                    trace_args['error_y'] = {
                        'type': 'data',
                        'symmetric': False,
                        'array': error_y_settings['array'][post_covid_indices],
                        'arrayminus': error_y_settings['arrayminus'][post_covid_indices],
                        'visible': True,
                        'color': error_y_settings['color'],
                        'thickness': error_y_settings['thickness'],
                        'width': error_y_settings['width']
                    }
            fig.add_trace(go.Scatter(**trace_args))
            if not main_legend_shown:
                main_legend_shown = True
        
        # Add COVID gap dotted line if we have data before and after
        if not pre_covid.empty and not post_covid.empty:
            # Find the last valid (non-NaN) pre-COVID value
            pre_covid_valid = pre_covid[pre_covid[metric_column].notna()]
            # Find the first valid (non-NaN) post-COVID value
            post_covid_valid = post_covid[post_covid[metric_column].notna()]
            
            # Only create gap line if we have valid values on both sides
            if not pre_covid_valid.empty and not post_covid_valid.empty:
                last_pre = pre_covid_valid.iloc[-1]
                first_post = post_covid_valid.iloc[0]
                last_pre_value = last_pre[metric_column]
                first_post_value = first_post[metric_column]
                
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
                    comp_metric_column = comp_data.columns[2] if len(comp_data.columns) > 2 else comp_data.columns[1]
                    
                    # Convert decimal values to percentages for percentage-based metrics
                    # Note: Use 'coral_cover' not 'coral' to avoid matching 'corallivore_density'
                    comp_is_percentage = 'coral_cover' in comp_metric_column.lower() or 'algae' in comp_metric_column.lower() or 'bleaching' in comp_metric_column.lower() or 'rubble' in comp_metric_column.lower()
                    if comp_is_percentage:
                        comp_data[comp_metric_column] = comp_data[comp_metric_column] * 100
                        # Also convert statistical columns to percentages
                        for suffix in ['_ci_low', '_ci_high', '_eb_low', '_eb_high', '_sd']:
                            stat_col = f'{comp_metric_column}{suffix}'
                            if stat_col in comp_data.columns:
                                comp_data[stat_col] = comp_data[stat_col] * 100
                    
                    comp_data['season'] = comp_data['date'].apply(format_season)
                    
                    # Apply same date filter
                    if date_range and len(date_range) == 2:
                        start_filter, end_filter = date_range
                        if start_filter and end_filter:
                            start_dt = pd.to_datetime(start_filter)
                            end_dt = pd.to_datetime(end_filter)
                            comp_data = comp_data[(comp_data['date'] >= start_dt) & (comp_data['date'] <= end_dt)]
                    
                    color = colors[i % len(colors)]
                    # Ensure label is a string, not a list
                    if comparison_labels and isinstance(comparison_labels, list) and i < len(comparison_labels):
                        label = comparison_labels[i]
                        # If label is still a list (edge case), take first element
                        if isinstance(label, list):
                            label = label[0] if label else f"Comparison {i+1}"
                    else:
                        label = f"Comparison {i+1}"
                    
                    # Configure comparison line style based on user preference
                    comp_line_style = {
                        'color': color,
                        'width': 2,
                        'dash': 'dash'
                    }
                    
                    # Add smooth curves unless straight lines are requested
                    if not use_straight_lines:
                        comp_line_style['shape'] = 'spline'
                        comp_line_style['smoothing'] = 1.3
                    
                    fig.add_trace(go.Scatter(
                        x=comp_data['season'],
                        y=comp_data[comp_metric_column],
                        name=label,
                        line=comp_line_style,
                        mode='lines+markers',
                        marker=dict(size=6, color=color)
                    ))
        
        # Get sorted seasons for x-axis ordering (maintain chronological order)
        sorted_seasons = data.sort_values('date')['season'].unique().tolist()
        
        # Update layout
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