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

    def create_time_series(self, data, title, y_label, comparison_data=None, secondary_data=None, secondary_label=None, tertiary_data=None, tertiary_label=None):
        """Create time series graph with optional comparison and secondary/tertiary metrics"""
        # Create base figure
        fig = go.Figure()

        # Configure basic download settings
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
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
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
        covid_start = date(2019, 9, 1)
        covid_end = date(2022, 3, 1)

        pre_covid = data[data['date'] < covid_start]
        post_covid = data[data['date'] > covid_end]

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

        # Add comparison data if provided
        if comparison_data is not None and not comparison_data.empty:
            comparison_data = comparison_data.sort_values('date')
            comparison_data['season'] = comparison_data['date'].apply(format_season)
            pre_covid_comp = comparison_data[comparison_data['date'] < covid_start]
            post_covid_comp = comparison_data[comparison_data['date'] > covid_end]

            # Add pre-COVID comparison data
            fig.add_trace(go.Scatter(
                x=pre_covid_comp['season'],
                y=pre_covid_comp[comparison_data.columns[1]],
                name='Comparison',
                line=dict(color='#ef476f', dash='solid'),
                mode='lines+markers'
            ))

            # Add post-COVID comparison data
            fig.add_trace(go.Scatter(
                x=post_covid_comp['season'],
                y=post_covid_comp[comparison_data.columns[1]],
                name='Comparison',
                line=dict(color='#ef476f', dash='solid'),
                mode='lines+markers',
                showlegend=False
            ))

        # Update layout
        layout_updates = {
                'title': {
                    'text': title,
                    'y': 0.95,  # Move title up slightly
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'size': 16}  # Slightly smaller font for better mobile view
                },
                'xaxis_title': 'Season',
                'yaxis_title': y_label,
                'template': 'plotly_white',
                'hovermode': 'x unified',
                'showlegend': True,
                'legend': {
                    'orientation': 'h',
                    'yanchor': 'bottom',
                    'y': -0.6,  # Further increased distance from plot area
                    'xanchor': 'center',
                    'x': 0.5,
                    'bgcolor': 'rgba(255, 255, 255, 1)'  # Fully opaque background
                },
                'autosize': True,
                'height': 550,  # Further increased height to accommodate legend and axis labels
                'margin': {
                    'l': 50,
                    'r': 30,
                    't': 60,
                    'b': 180  # Further increased bottom margin for legend and x-axis labels
                },
                'xaxis': {
                    'tickangle': 45,
                    'automargin': True,
                    'type': 'category',
                    'tickfont': {'size': 10},
                    'title': {'standoff': 50}  # Add space between axis title and labels
                },
                'yaxis': {
                    'automargin': True,
                    'title': {
                        'text': y_label,
                        'standoff': 10
                    },
                    'side': 'left'
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
                'modeBarButtonsToRemove': ['lasso2d', 'select2d']
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
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }
        return fig, config