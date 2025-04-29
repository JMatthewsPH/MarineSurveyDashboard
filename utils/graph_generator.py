import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np
import streamlit as st

def format_season(date_obj):
    """Convert date to season format"""
    month = date_obj.month
    year = date_obj.year

    if 3 <= month <= 5:  # Q1: MAR-MAY
        return f'MAR-MAY {year}'
    elif 6 <= month <= 8:  # Q2: JUN-AUG
        return f'JUN-AUG {year}'
    elif 9 <= month <= 11:  # Q3: SEP-NOV
        return f'SEP-NOV {year}'
    else:  # Q4: DEC-FEB
        # If it's December, it's the start of Q4 for next year
        if month == 12:
            return f'DEC-FEB {year + 1}'
        # If it's January or February, it's end of Q4 for current year
        return f'DEC-FEB {year}'

def generate_filename(title: str, start_date=None, end_date=None) -> str:
    """Generate a filename based on the plot title and date range"""
    # Remove any special characters and convert spaces to underscores
    clean_title = "".join(c if c.isalnum() or c.isspace() else "_" for c in title.lower())
    clean_title = clean_title.replace(" ", "_")
    
    # Add date range to filename if provided
    date_str = ""
    if start_date and end_date:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        date_str = f"{start_str}_to_{end_str}"
    
    return f"{clean_title}_{date_str}.png"

class GraphGenerator:
    def __init__(self, data_processor):
        self.data_processor = data_processor

    def get_metric_range(self, metric_name, data=None, comparison_data=None):
        """
        Define ranges for each metric type, with dynamic scaling option
        
        Args:
            metric_name: The name of the metric (e.g., 'Herbivore')
            data: Primary data DataFrame
            comparison_data: Optional comparison data
            
        Returns:
            Dictionary with min and max values for the Y-axis
        """
        # Default fixed ranges
        fixed_ranges = {
            'Commercial Biomass': {'min': 0, 'max': 3000},  # kg/ha
            'Hard Coral Cover': {'min': 0, 'max': 100},     # percentage
            'Fleshy Algae': {'min': 0, 'max': 100},         # percentage
            'Bleaching': {'min': 0, 'max': 100},            # percentage
            'Herbivore': None,                              # Dynamic
            'Carnivore': None,                              # Dynamic
            'Omnivore': None,                               # Dynamic
            'Corallivore': None,                            # Dynamic
            'Rubble': {'min': 0, 'max': 100}                # percentage
        }
        
        # Print metric name for debugging
        print(f"DEBUG - Metric name received: '{metric_name}'")
        if metric_name == 'Herbivore':
            print("DEBUG - Confirmed herbivore will use dynamic scaling")
        
        # Get the default range or None if dynamic scaling should be used
        default_range = fixed_ranges.get(metric_name, {'min': 0, 'max': 100})
        
        # If a fixed range is specified, return it
        if default_range is not None:
            return default_range
            
        # Otherwise, calculate dynamic range based on data
        if data is not None and not data.empty:
            # Get all values for calculation
            all_values = []
            
            # Add primary data values
            if len(data.columns) > 1:
                all_values.extend(data[data.columns[1]].tolist())
                
            # Add comparison data values if available
            if comparison_data is not None:
                if isinstance(comparison_data, list):
                    for comp_df in comparison_data:
                        if comp_df is not None and len(comp_df.columns) > 1:
                            all_values.extend(comp_df[comp_df.columns[1]].tolist())
                elif isinstance(comparison_data, pd.DataFrame) and len(comparison_data.columns) > 1:
                    all_values.extend(comparison_data[comparison_data.columns[1]].tolist())
            
            # Remove None and NaN values
            all_values = [v for v in all_values if v is not None and not (isinstance(v, float) and np.isnan(v))]
            
            if all_values:
                min_val = min(all_values)
                max_val = max(all_values)
                
                # Add padding (10% on each side)
                padding = (max_val - min_val) * 0.1
                
                # Ensure min is not negative for values that shouldn't go below zero
                min_val = max(0, min_val - padding)
                
                return {
                    'min': min_val,
                    'max': max_val + padding
                }
        
        # Default fallback dynamic range if we couldn't calculate
        return {'min': 0, 'max': 100}
    
    def create_time_series(self, data, title, y_label, comparison_data=None, comparison_labels=None, date_range=None, secondary_data=None, secondary_label=None, tertiary_data=None, tertiary_label=None):
        """
        Create time series graph with optional multiple comparison sites and date range
        
        Args:
            data: Primary data to plot
            title: Chart title
            y_label: Y-axis label
            comparison_data: Single DataFrame or list of DataFrames for comparison
            comparison_labels: List of labels for comparison data
            date_range: Tuple of (start_date, end_date) to filter the data
            secondary_data: Optional secondary metric data
            secondary_label: Label for secondary data
            tertiary_data: Optional tertiary metric data
            tertiary_label: Label for tertiary data
        """
        # Ensure data is not empty
        if data is None or data.empty:
            return go.Figure(), {}
            
        # Use light mode colors for better consistency with Streamlit's native theme
        text_color = '#000000'  # Black text for better readability
        grid_color = '#e0e0e0'  # Light grid
        legend_bg = 'rgba(255, 255, 255, 0.7)'  # Semi-transparent legend
        
        # Use optimized layout for mobile
        fig = go.Figure()
        
        # Copy data to avoid modifying original
        filtered_data = data.copy()
        
        # Apply date range filtering if specified
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            
            # Ensure dates are properly converted for comparison
            try:
                # Make sure filtered_data['date'] is a datetime column
                if not pd.api.types.is_datetime64_dtype(filtered_data['date']):
                    filtered_data['date'] = pd.to_datetime(filtered_data['date'])
                
                # Convert input dates to pandas Timestamp
                if not isinstance(start_date, pd.Timestamp):
                    start_date = pd.Timestamp(start_date)
                    
                if not isinstance(end_date, pd.Timestamp):
                    end_date = pd.Timestamp(end_date)
                
                # Filter with converted timestamps
                filtered_data = filtered_data[(filtered_data['date'] >= start_date) & 
                                             (filtered_data['date'] <= end_date)]
            except Exception as e:
                print(f"DEBUG - Date filtering error: {e}")
                # If all else fails, just return the original data
                pass
        
        # Sort by date for proper trend lines
        filtered_data = filtered_data.sort_values('date')
        
        # Separate data into pre-COVID and post-COVID periods
        covid_start = datetime.strptime('2020-03-01', '%Y-%m-%d').date()
        covid_end = datetime.strptime('2020-09-30', '%Y-%m-%d').date()
        
        # Convert date column to datetime if it's not already
        if not pd.api.types.is_datetime64_dtype(filtered_data['date']):
            filtered_data['date'] = pd.to_datetime(filtered_data['date'])
            
        # Convert comparison dates to Timestamp
        covid_start_ts = pd.Timestamp(covid_start)
        covid_end_ts = pd.Timestamp(covid_end)
            
        pre_covid = filtered_data[filtered_data['date'] < covid_start_ts]
        post_covid = filtered_data[filtered_data['date'] > covid_end_ts]
        
        # Add primary data trace (pre-COVID)
        fig.add_trace(go.Scatter(
            x=pre_covid['date'],
            y=pre_covid[pre_covid.columns[1]],
            name=y_label,
            line=dict(color='#0077b6', dash='solid'),
            mode='lines+markers'
        ))
        
        # Add post-COVID data
        fig.add_trace(go.Scatter(
            x=post_covid['date'],
            y=post_covid[post_covid.columns[1]],
            name=y_label,
            line=dict(color='#0077b6', dash='solid'),
            mode='lines+markers',
            showlegend=False
        ))
        
        # Add COVID period indicator if data exists on both sides
        if not pre_covid.empty and not post_covid.empty:
            last_pre_covid = pre_covid.iloc[-1]
            first_post_covid = post_covid.iloc[0]
            fig.add_trace(go.Scatter(
                x=[last_pre_covid['date'], first_post_covid['date']],
                y=[last_pre_covid[pre_covid.columns[1]], first_post_covid[post_covid.columns[1]]],
                name='COVID-19 Period (No Data)',
                line=dict(color='#0077b6', dash='dot', width=1),
                opacity=0.3,
                mode='lines'
            ))
        
        # Handle secondary metric if provided
        if secondary_data is not None and not secondary_data.empty:
            filtered_secondary = secondary_data.copy()
            
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                
                # Ensure dates are properly converted for comparison
                try:
                    # Make sure filtered_secondary['date'] is a datetime column
                    if not pd.api.types.is_datetime64_dtype(filtered_secondary['date']):
                        filtered_secondary['date'] = pd.to_datetime(filtered_secondary['date'])
                    
                    # Convert input dates to pandas Timestamp
                    if not isinstance(start_date, pd.Timestamp):
                        start_date = pd.Timestamp(start_date)
                        
                    if not isinstance(end_date, pd.Timestamp):
                        end_date = pd.Timestamp(end_date)
                    
                    # Filter with converted timestamps
                    filtered_secondary = filtered_secondary[(filtered_secondary['date'] >= start_date) & 
                                                          (filtered_secondary['date'] <= end_date)]
                except Exception as e:
                    print(f"DEBUG - Secondary date filtering error: {e}")
                    # If all else fails, just return the original data
                    pass
            
            filtered_secondary = filtered_secondary.sort_values('date')
            
            # Convert date column to datetime if it's not already
            if not pd.api.types.is_datetime64_dtype(filtered_secondary['date']):
                filtered_secondary['date'] = pd.to_datetime(filtered_secondary['date'])
                
            pre_covid_secondary = filtered_secondary[filtered_secondary['date'] < covid_start_ts]
            post_covid_secondary = filtered_secondary[filtered_secondary['date'] > covid_end_ts]
            
            # Add secondary metric pre-COVID
            fig.add_trace(go.Scatter(
                x=pre_covid_secondary['date'],
                y=pre_covid_secondary[pre_covid_secondary.columns[1]],
                name=secondary_label,
                line=dict(color='#f4a261', dash='solid'),
                mode='lines+markers',
                yaxis='y2'
            ))
            
            # Add secondary metric post-COVID
            fig.add_trace(go.Scatter(
                x=post_covid_secondary['date'],
                y=post_covid_secondary[post_covid_secondary.columns[1]],
                name=secondary_label,
                line=dict(color='#f4a261', dash='solid'),
                mode='lines+markers',
                showlegend=False,
                yaxis='y2'
            ))
            
            # Add COVID period connector for secondary metric
            if not pre_covid_secondary.empty and not post_covid_secondary.empty:
                last_pre_covid_secondary = pre_covid_secondary.iloc[-1]
                first_post_covid_secondary = post_covid_secondary.iloc[0]
                fig.add_trace(go.Scatter(
                    x=[last_pre_covid_secondary['date'], first_post_covid_secondary['date']],
                    y=[last_pre_covid_secondary[pre_covid_secondary.columns[1]], 
                       first_post_covid_secondary[post_covid_secondary.columns[1]]],
                    name='COVID-19 Period (No Data)',
                    line=dict(color='#f4a261', dash='dot', width=1),
                    opacity=0.3,
                    mode='lines',
                    showlegend=False,
                    yaxis='y2'
                ))
        
        # Handle tertiary metric if provided
        if tertiary_data is not None and not tertiary_data.empty:
            filtered_tertiary = tertiary_data.copy()
            
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                
                # Ensure dates are properly converted for comparison
                try:
                    # Make sure filtered_tertiary['date'] is a datetime column
                    if not pd.api.types.is_datetime64_dtype(filtered_tertiary['date']):
                        filtered_tertiary['date'] = pd.to_datetime(filtered_tertiary['date'])
                    
                    # Convert input dates to pandas Timestamp
                    if not isinstance(start_date, pd.Timestamp):
                        start_date = pd.Timestamp(start_date)
                        
                    if not isinstance(end_date, pd.Timestamp):
                        end_date = pd.Timestamp(end_date)
                    
                    # Filter with converted timestamps
                    filtered_tertiary = filtered_tertiary[(filtered_tertiary['date'] >= start_date) & 
                                                        (filtered_tertiary['date'] <= end_date)]
                except Exception as e:
                    print(f"DEBUG - Tertiary date filtering error: {e}")
                    # If all else fails, just return the original data
                    pass
            
            filtered_tertiary = filtered_tertiary.sort_values('date')
            
            # Convert date column to datetime if it's not already
            if not pd.api.types.is_datetime64_dtype(filtered_tertiary['date']):
                filtered_tertiary['date'] = pd.to_datetime(filtered_tertiary['date'])
                
            pre_covid_tertiary = filtered_tertiary[filtered_tertiary['date'] < covid_start_ts]
            post_covid_tertiary = filtered_tertiary[filtered_tertiary['date'] > covid_end_ts]
            
            # Add tertiary metric pre-COVID
            fig.add_trace(go.Scatter(
                x=pre_covid_tertiary['date'],
                y=pre_covid_tertiary[pre_covid_tertiary.columns[1]],
                name=tertiary_label,
                line=dict(color='#e76f51', dash='solid'),
                mode='lines+markers',
                yaxis='y3'
            ))
            
            # Add tertiary metric post-COVID
            fig.add_trace(go.Scatter(
                x=post_covid_tertiary['date'],
                y=post_covid_tertiary[post_covid_tertiary.columns[1]],
                name=tertiary_label,
                line=dict(color='#e76f51', dash='solid'),
                mode='lines+markers',
                showlegend=False,
                yaxis='y3'
            ))
            
            # Add COVID period connector for tertiary metric
            if not pre_covid_tertiary.empty and not post_covid_tertiary.empty:
                last_pre_covid_tertiary = pre_covid_tertiary.iloc[-1]
                first_post_covid_tertiary = post_covid_tertiary.iloc[0]
                fig.add_trace(go.Scatter(
                    x=[last_pre_covid_tertiary['date'], first_post_covid_tertiary['date']],
                    y=[last_pre_covid_tertiary[pre_covid_tertiary.columns[1]], 
                       first_post_covid_tertiary[post_covid_tertiary.columns[1]]],
                    name='COVID-19 Period (No Data)',
                    line=dict(color='#e76f51', dash='dot', width=1),
                    opacity=0.3,
                    mode='lines',
                    showlegend=False,
                    yaxis='y3'
                ))
        
        # Add comparison data if provided
        if comparison_data is not None:
            comparison_list = comparison_data if isinstance(comparison_data, list) else [comparison_data]
            labels = comparison_labels if comparison_labels else [f"Comparison {i+1}" for i in range(len(comparison_list))]
            
            # Set colors for comparison sites
            colors = ['#2a9d8f', '#e9c46a', '#f4a261', '#e76f51', '#264653', '#8338ec', '#ff006e', '#8d99ae', '#457b9d']
            
            for i, (comp_data, label) in enumerate(zip(comparison_list, labels)):
                if comp_data is not None and not comp_data.empty:
                    # Apply filter to comparison data
                    filtered_comp = comp_data.copy()
                    
                    if date_range and len(date_range) == 2:
                        start_date, end_date = date_range
                        
                        # Ensure dates are properly converted for comparison
                        try:
                            # Make sure filtered_comp['date'] is a datetime column
                            if not pd.api.types.is_datetime64_dtype(filtered_comp['date']):
                                filtered_comp['date'] = pd.to_datetime(filtered_comp['date'])
                            
                            # Convert input dates to pandas Timestamp
                            if not isinstance(start_date, pd.Timestamp):
                                start_date = pd.Timestamp(start_date)
                                
                            if not isinstance(end_date, pd.Timestamp):
                                end_date = pd.Timestamp(end_date)
                            
                            # Filter with converted timestamps
                            filtered_comp = filtered_comp[(filtered_comp['date'] >= start_date) & 
                                                        (filtered_comp['date'] <= end_date)]
                        except Exception as e:
                            print(f"DEBUG - Comparison date filtering error: {e}")
                            # If all else fails, just return the original data
                            pass
                    
                    filtered_comp = filtered_comp.sort_values('date')
                    
                    # Convert date column to datetime if it's not already
                    if not pd.api.types.is_datetime64_dtype(filtered_comp['date']):
                        filtered_comp['date'] = pd.to_datetime(filtered_comp['date'])
                        
                    pre_covid_comp = filtered_comp[filtered_comp['date'] < covid_start_ts]
                    post_covid_comp = filtered_comp[filtered_comp['date'] > covid_end_ts]
                    
                    color_idx = i % len(colors)
                    
                    # Add comparison pre-COVID
                    fig.add_trace(go.Scatter(
                        x=pre_covid_comp['date'],
                        y=pre_covid_comp[pre_covid_comp.columns[1]],
                        name=label,
                        line=dict(color=colors[color_idx], dash='solid'),
                        mode='lines+markers'
                    ))
                    
                    # Add comparison post-COVID
                    fig.add_trace(go.Scatter(
                        x=post_covid_comp['date'],
                        y=post_covid_comp[post_covid_comp.columns[1]],
                        name=label,
                        line=dict(color=colors[color_idx], dash='solid'),
                        mode='lines+markers',
                        showlegend=False
                    ))
                    
                    # Add COVID period connector for comparison
                    if not pre_covid_comp.empty and not post_covid_comp.empty:
                        last_pre_covid_comp = pre_covid_comp.iloc[-1]
                        first_post_covid_comp = post_covid_comp.iloc[0]
                        fig.add_trace(go.Scatter(
                            x=[last_pre_covid_comp['date'], first_post_covid_comp['date']],
                            y=[last_pre_covid_comp[pre_covid_comp.columns[1]], 
                               first_post_covid_comp[post_covid_comp.columns[1]]],
                            name='COVID-19 Period (No Data)',
                            line=dict(color=colors[color_idx], dash='dot', width=1),
                            opacity=0.3,
                            mode='lines',
                            showlegend=False
                        ))
        
        # Add COVID period rectangle annotation
        fig.add_vrect(
            x0=pd.Timestamp('2020-03-01'), x1=pd.Timestamp('2020-09-30'),
            fillcolor="red", opacity=0.1,
            layer="below", line_width=0,
            annotation_text="COVID-19",
            annotation_position="top left",
            annotation=dict(
                font=dict(size=12, color=text_color),
                bgcolor="rgba(255, 0, 0, 0.1)",
                bordercolor="red",
                borderwidth=1
            )
        )
        
        # Calculate dynamic y-axis range based on metric type
        metric_name = y_label.split(' ')[0] if ' ' in y_label else y_label
        y_range = self.get_metric_range(metric_name, filtered_data, comparison_data)
        
        # Set layout - with high contrast for readability
        layout = dict(
            title=dict(
                text=title,
                font=dict(color=text_color)
            ),
            legend=dict(
                bgcolor=legend_bg,
                font=dict(color=text_color)
            ),
            xaxis=dict(
                title='Season',
                gridcolor=grid_color,
                zerolinecolor=grid_color,
                tickfont=dict(color=text_color),
                title_font=dict(color=text_color)
            ),
            yaxis=dict(
                title=y_label,
                gridcolor=grid_color,
                zerolinecolor=grid_color,
                range=[y_range['min'], y_range['max']],
                tickfont=dict(color=text_color),
                title_font=dict(color=text_color)
            ),
            height=500,
            margin=dict(l=80, r=30, t=100, b=50),
            showlegend=False,
            autosize=True,
            paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
            plot_bgcolor='rgba(0,0,0,0)',   # Transparent background,
            xaxis_title=dict(
                text='Season',
                font=dict(color=text_color, size=14)
            ),
            yaxis_title=dict(
                text=y_label,
                font=dict(color=text_color, size=14)
            )
        )
        
        # Add secondary y-axis if needed
        if secondary_data is not None and not secondary_data.empty:
            layout['yaxis2'] = dict(
                title=secondary_label,
                overlaying='y',
                side='right',
                gridcolor='rgba(0,0,0,0)',
                zerolinecolor=grid_color,
                tickfont=dict(color=text_color),
                title_font=dict(color=text_color)
            )
            layout['showlegend'] = True
        
        # Add tertiary y-axis if needed
        if tertiary_data is not None and not tertiary_data.empty:
            layout['yaxis3'] = dict(
                title=tertiary_label,
                overlaying='y',
                side='right',
                position=0.85,
                gridcolor='rgba(0,0,0,0)',
                zerolinecolor=grid_color,
                tickfont=dict(color=text_color),
                title_font=dict(color=text_color)
            )
            layout['showlegend'] = True
        
        fig.update_layout(layout)
        
        # Configure download options
        config = {
            'toImageButtonOptions': {
                'format': 'png',
                'filename': generate_filename(title),
                'height': 800,
                'width': 1200,
                'scale': 2
            },
            'displaylogo': False,
            'responsive': True,
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d'],
            'scrollZoom': False,  # Disable scroll zoom on mobile to prevent accidental zooming
            'doubleClick': 'reset',  # Double tap to reset the view
            'showTips': True,  # Show tips for better usability
        }
        
        return fig, config
        
    def create_eco_tourism_chart(self, data, title, observation_type='percentage'):
        """Create bar chart for eco-tourism data"""
        if data is None or data.empty:
            return go.Figure(), {}
        
        # Use light mode colors for better consistency with Streamlit's native theme
        text_color = '#000000'  # Black text for better readability
        grid_color = '#e0e0e0'  # Light grid
        
        fig = go.Figure()
        
        # For percentage data
        if observation_type == 'percentage':
            bar_colors = ['#0077b6', '#2a9d8f', '#e9c46a', '#f4a261', '#e76f51']
            
            # Sort data by percentage descending
            sorted_data = data.sort_values('percentage', ascending=False).head(10)
            
            fig.add_trace(go.Bar(
                x=sorted_data['species'],
                y=sorted_data['percentage'],
                marker_color=bar_colors[:len(sorted_data)],
                text=sorted_data['percentage'].apply(lambda x: f"{x:.1f}%"),
                textposition='auto',
                hovertemplate='%{x}: %{y:.1f}%<extra></extra>'
            ))
            
            y_title = 'Percentage of Eco-Tourism Observations'
            
        # For count data
        else:
            bar_colors = ['#0077b6', '#2a9d8f', '#e9c46a', '#f4a261', '#e76f51']
            
            # Sort data by count descending
            sorted_data = data.sort_values('count', ascending=False).head(10)
            
            fig.add_trace(go.Bar(
                x=sorted_data['species'],
                y=sorted_data['count'],
                marker_color=bar_colors[:len(sorted_data)],
                text=sorted_data['count'],
                textposition='auto',
                hovertemplate='%{x}: %{y}<extra></extra>'
            ))
            
            y_title = 'Number of Eco-Tourism Observations'
        
        # Set layout
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(color=text_color, size=20)
            ),
            xaxis=dict(
                title='Species',
                gridcolor=grid_color,
                tickfont=dict(color=text_color),
                title_font=dict(color=text_color)
            ),
            yaxis=dict(
                title=y_title,
                gridcolor=grid_color,
                zerolinecolor=grid_color,
                tickfont=dict(color=text_color),
                title_font=dict(color=text_color)
            ),
            height=500,
            margin=dict(l=80, r=30, t=100, b=150),
            showlegend=False,
            autosize=True,
            paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
            plot_bgcolor='rgba(0,0,0,0)',   # Transparent background
        )
        
        # Rotate x-axis labels for better readability
        fig.update_xaxes(tickangle=45)
        
        # Configure download options
        config = {
            'toImageButtonOptions': {
                'format': 'png',
                'filename': generate_filename(title),
                'height': 800,
                'width': 1200,
                'scale': 2
            },
            'displaylogo': False,
            'responsive': True,
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'scrollZoom': False,
            'doubleClick': 'reset'
        }
        
        return fig, config