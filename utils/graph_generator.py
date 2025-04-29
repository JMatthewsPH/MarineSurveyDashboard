import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np

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

    # Format date part of filename
    try:
        if start_date and end_date:
            # Convert to datetime if needed
            if not isinstance(start_date, datetime):
                start_date = pd.to_datetime(start_date)
            if not isinstance(end_date, datetime):
                end_date = pd.to_datetime(end_date)
            date_str = f"{start_date.strftime('%Y%b').lower()}_{end_date.strftime('%Y%b').lower()}"
        else:
            # Default to current date if no range specified
            current_date = datetime.now().strftime("%Y%b%d").lower()
            date_str = current_date
    except (AttributeError, ValueError, TypeError) as e:
        print(f"Error formatting dates for filename: {e}")
        current_date = datetime.now().strftime("%Y%b%d").lower()
        date_str = current_date

    return f"{clean_title}_{date_str}.png"

class GraphGenerator:
    def __init__(self, data_processor):
        self.data_processor = data_processor

    def get_metric_range(self, metric_name):
        """Define standard ranges for each metric type"""
        ranges = {
            'Commercial Biomass': {'min': 0, 'max': 3000},  # kg/ha
            'Hard Coral Cover': {'min': 0, 'max': 100},     # percentage
            'Fleshy Algae': {'min': 0, 'max': 100},         # percentage
            'Bleaching': {'min': 0, 'max': 100},            # percentage
            'Herbivore Density': {'min': 0, 'max': 20000},  # ind/ha - increased to 20,000 to accommodate Basak data
            'Herbivore': {'min': 0, 'max': 20000},          # ind/ha - increased to 20,000 to accommodate Basak data
            'Carnivore': {'min': 0, 'max': 5000},           # ind/ha
            'Omnivore': {'min': 0, 'max': 8000},            # ind/ha
            'Corallivore': {'min': 0, 'max': 1500},         # ind/ha
            'Rubble': {'min': 0, 'max': 100}                # percentage
        }
        return ranges.get(metric_name, {'min': 0, 'max': 100})  # default range

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
        # Create base figure
        fig = go.Figure()

        # Configure basic download settings with mobile-friendly options
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
            'displayModeBar': 'hover'  # Only show mode bar on hover to save space
        }

        # If no data, return empty figure with basic config
        if data.empty:
            return fig, config

        # Sort data by date and get date range for filename
        data = data.sort_values('date')
        start_date = data['date'].min()
        end_date = data['date'].max()

        # Update filename with date range
        config['toImageButtonOptions']['filename'] = generate_filename(title, start_date, end_date)

        # Format dates as seasons
        data['season'] = data['date'].apply(format_season)

        # Split data into pre and post COVID
        covid_start = pd.Timestamp(date(2019, 9, 1))
        covid_end = pd.Timestamp(date(2022, 3, 1))
        
        # Ensure data['date'] is in datetime64 format
        if not data.empty:
            data['date'] = pd.to_datetime(data['date'])
            pre_covid = data[data['date'] < covid_start]
            post_covid = data[data['date'] > covid_end]
        else:
            pre_covid = data
            post_covid = data

        # Get the metric name from the title
        metric_name = title.split(' - ')[0].strip()
        y_range = self.get_metric_range(metric_name)

        # Add pre-COVID data
        fig.add_trace(go.Scatter(
            x=pre_covid['season'],
            y=pre_covid[pre_covid.columns[1]],
            name=y_label,
            line=dict(color='#0077b6', dash='solid'),
            mode='lines+markers'
        ))

        # Add post-COVID data
        fig.add_trace(go.Scatter(
            x=post_covid['season'],
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
                x=[last_pre_covid['season'], first_post_covid['season']],
                y=[last_pre_covid[pre_covid.columns[1]], first_post_covid[post_covid.columns[1]]],
                name='COVID-19 Period (No Data)',
                line=dict(color='#0077b6', dash='dot', width=1),
                opacity=0.3,
                mode='lines'
            ))

        # Apply date range filter if provided
        if date_range and len(date_range) == 2:
            start_filter, end_filter = date_range
            if start_filter and end_filter:
                # Convert data['date'] to datetime64 for consistent comparison
                if not data.empty:
                    data['date'] = pd.to_datetime(data['date'])
                    
                    # Convert filter dates to datetime64 for consistent comparison
                    start_dt = pd.to_datetime(start_filter).tz_localize(None)
                    end_dt = pd.to_datetime(end_filter).tz_localize(None)
                    
                    # Filter the primary data
                    data = data[(data['date'] >= start_dt) & (data['date'] <= end_dt)]
                    pre_covid = data[data['date'] < covid_start]
                    post_covid = data[data['date'] > covid_end]
                    
                    # Update chart title with date range info
                    date_range_str = f"{start_dt.strftime('%b %Y')} - {end_dt.strftime('%b %Y')}"
                    title = f"{title} ({date_range_str})"
        
        # Define a list of colors for multiple comparison sites
        comparison_colors = ['#ef476f', '#ffd166', '#06d6a0', '#118ab2', '#073b4c', '#9b5de5', '#f15bb5']
        
        # Handle comparison data (which can be a single DataFrame or a list of DataFrames)
        if comparison_data is not None:
            comparison_list = []
            labels_list = []
            
            # Convert single DataFrame to list for consistent handling
            if isinstance(comparison_data, pd.DataFrame) and not comparison_data.empty:
                comparison_list = [comparison_data]
                labels_list = ['Comparison'] if comparison_labels is None else [comparison_labels[0]]
            # Handle list of DataFrames
            elif isinstance(comparison_data, list):
                comparison_list = [df for df in comparison_data if df is not None and not df.empty]
                if comparison_labels is not None:
                    # Use provided labels but ensure the length matches our data
                    labels_list = comparison_labels[:len(comparison_list)] if comparison_labels else []
                    # Fill any missing labels
                    labels_list += [f'Comparison {i+1}' for i in range(len(labels_list), len(comparison_list))]
                else:
                    # Generate default labels if none provided
                    labels_list = [f'Comparison {i+1}' for i in range(len(comparison_list))]
            
            # Process each comparison dataset
            for i, (comp_df, label) in enumerate(zip(comparison_list, labels_list)):
                # Apply date range filter if specified
                if date_range and len(date_range) == 2:
                    start_filter, end_filter = date_range
                    if start_filter and end_filter and not comp_df.empty:
                        # Convert to datetime for consistent comparison
                        comp_df['date'] = pd.to_datetime(comp_df['date'])
                        start_dt = pd.to_datetime(start_filter).tz_localize(None)
                        end_dt = pd.to_datetime(end_filter).tz_localize(None)
                        comp_df = comp_df[(comp_df['date'] >= start_dt) & (comp_df['date'] <= end_dt)]
                
                # Sort and format data
                comp_df = comp_df.sort_values('date')
                
                # Ensure comp_df['date'] is in datetime64 format
                if not comp_df.empty:
                    comp_df['date'] = pd.to_datetime(comp_df['date'])
                    comp_df['season'] = comp_df['date'].apply(format_season)
                    
                    # Split into pre/post COVID periods
                    pre_covid_comp = comp_df[comp_df['date'] < covid_start]
                    post_covid_comp = comp_df[comp_df['date'] > covid_end]
                else:
                    # For empty dataframes, ensure we have a season column
                    if 'season' not in comp_df.columns:
                        comp_df['season'] = pd.Series(dtype='object')
                    pre_covid_comp = comp_df
                    post_covid_comp = comp_df
                
                # Pick a color (cycle through the available colors)
                color = comparison_colors[i % len(comparison_colors)]
                
                # Add pre-COVID comparison data
                if not pre_covid_comp.empty:
                    fig.add_trace(go.Scatter(
                        x=pre_covid_comp['season'],
                        y=pre_covid_comp[comp_df.columns[1]],
                        name=label,
                        line=dict(color=color, dash='solid'),
                        mode='lines+markers'
                    ))
                
                # Add post-COVID comparison data
                if not post_covid_comp.empty:
                    fig.add_trace(go.Scatter(
                        x=post_covid_comp['season'],
                        y=post_covid_comp[comp_df.columns[1]],
                        name=label,
                        line=dict(color=color, dash='solid'),
                        mode='lines+markers',
                        showlegend=False
                    ))
                    
                # Add COVID period connector if both pre and post exist
                if not pre_covid_comp.empty and not post_covid_comp.empty:
                    last_pre = pre_covid_comp.iloc[-1]
                    first_post = post_covid_comp.iloc[0]
                    fig.add_trace(go.Scatter(
                        x=[last_pre['season'], first_post['season']],
                        y=[last_pre[comp_df.columns[1]], first_post[comp_df.columns[1]]],
                        line=dict(color=color, dash='dot', width=1),
                        opacity=0.3,
                        mode='lines',
                        showlegend=False
                    ))

        # Update layout with fixed y-axis range
        layout_updates = {
            'title': {
                'text': title,
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 16}
            },
            'xaxis_title': 'Season',
            'yaxis_title': y_label,
            'template': 'plotly_white',
            'hovermode': 'x unified',
            'showlegend': True,
            'legend': {
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': -0.6,
                'xanchor': 'center',
                'x': 0.5,
                'bgcolor': 'rgba(255, 255, 255, 1)'
            },
            'autosize': True,
            'height': 550,
            'margin': {
                'l': 50,
                'r': 30,
                't': 60,
                'b': 180
            },
            'xaxis': {
                'tickangle': 45,
                'automargin': True,
                'type': 'category',
                'tickfont': {'size': 10},
                'title': {'standoff': 50}
            },
            'yaxis': {
                'automargin': True,
                'title': {
                    'text': y_label,
                    'standoff': 10
                },
                'side': 'left',
                'range': [y_range['min'], y_range['max']]  # Set fixed y-axis range
            }
        }

        fig.update_layout(**layout_updates)
        return fig, config

    def create_eco_tourism_chart(self, data, title, observation_type='percentage'):
        """Create bar chart for eco-tourism data"""
        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for selected period",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )
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
                'displayModeBar': 'hover'  # Only show mode bar on hover to save space
            }
            return fig, config

        fig = go.Figure(go.Bar(
            y=data.index,
            x=data.values,
            orientation='h',
            marker_color='#0077b6'
        ))

        x_title = 'Success Rate (%)' if observation_type == 'percentage' else 'Average Count'

        fig.update_layout(
            title=dict(
                text=title,
                y=0.95,
                x=0.5,
                xanchor='center',
                yanchor='top'
            ),
            xaxis_title=x_title,
            yaxis_title='Species',
            template='plotly_white',
            height=500,
            margin=dict(l=80, r=30, t=100, b=50),
            showlegend=False,
            autosize=True
        )

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
            'displayModeBar': 'hover'  # Only show mode bar on hover to save space
        }
        return fig, config