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

class GraphGenerator:
    def __init__(self, data_processor):
        self.data_processor = data_processor

    def create_time_series(self, data, title, y_label, comparison_data=None, secondary_data=None, secondary_label=None, tertiary_data=None, tertiary_label=None):
        """Create time series graph with optional comparison and secondary/tertiary metrics"""
        fig = go.Figure()

        # Main data
        if not data.empty:
            # Sort data by date
            data = data.sort_values('date')

            # Format dates as seasons
            data['season'] = data['date'].apply(format_season)

            # Split data into pre and post COVID
            covid_start = date(2019, 9, 1)
            covid_end = date(2022, 3, 1)

            pre_covid = data[data['date'] < covid_start]
            post_covid = data[data['date'] > covid_end]

            # Add main data traces
            fig.add_trace(go.Scatter(
                x=pre_covid['season'],
                y=pre_covid[pre_covid.columns[1]],
                name=y_label,
                line=dict(color='#0077b6', dash='solid'),
                mode='lines+markers'
            ))

            fig.add_trace(go.Scatter(
                x=post_covid['season'],
                y=post_covid[post_covid.columns[1]],
                name=y_label,
                line=dict(color='#0077b6', dash='solid'),
                mode='lines+markers',
                showlegend=False
            ))

            # Add dotted line for COVID gap if there's data on both sides
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

        # Secondary metric data (if provided)
        if secondary_data is not None and not secondary_data.empty:
            secondary_data = secondary_data.sort_values('date')
            secondary_data['season'] = secondary_data['date'].apply(format_season)
            pre_covid_sec = secondary_data[secondary_data['date'] < covid_start]
            post_covid_sec = secondary_data[secondary_data['date'] > covid_end]

            fig.add_trace(go.Scatter(
                x=pre_covid_sec['season'],
                y=pre_covid_sec[secondary_data.columns[1]],
                name=secondary_label,
                line=dict(color='#ef476f', dash='solid'),
                mode='lines+markers',
                yaxis='y2'
            ))

            fig.add_trace(go.Scatter(
                x=post_covid_sec['season'],
                y=post_covid_sec[post_covid_sec.columns[1]],
                name=secondary_label,
                line=dict(color='#ef476f', dash='solid'),
                mode='lines+markers',
                yaxis='y2',
                showlegend=False
            ))

            if not pre_covid_sec.empty and not post_covid_sec.empty:
                last_pre_covid = pre_covid_sec.iloc[-1]
                first_post_covid = post_covid_sec.iloc[0]

                fig.add_trace(go.Scatter(
                    x=[last_pre_covid['season'], first_post_covid['season']],
                    y=[last_pre_covid[secondary_data.columns[1]], first_post_covid[secondary_data.columns[1]]],
                    name='COVID-19 Period (No Data)',
                    line=dict(color='#ef476f', dash='dot', width=1),
                    opacity=0.3,
                    mode='lines',
                    yaxis='y2',
                    showlegend=False
                ))

        # Tertiary metric data (if provided)
        if tertiary_data is not None and not tertiary_data.empty:
            tertiary_data = tertiary_data.sort_values('date')
            tertiary_data['season'] = tertiary_data['date'].apply(format_season)
            pre_covid_ter = tertiary_data[tertiary_data['date'] < covid_start]
            post_covid_ter = tertiary_data[tertiary_data['date'] > covid_end]

            fig.add_trace(go.Scatter(
                x=pre_covid_ter['season'],
                y=pre_covid_ter[tertiary_data.columns[1]],
                name=tertiary_label,
                line=dict(color='#06d6a0', dash='solid'),
                mode='lines+markers',
                yaxis='y3'
            ))

            fig.add_trace(go.Scatter(
                x=post_covid_ter['season'],
                y=post_covid_ter[post_covid_ter.columns[1]],
                name=tertiary_label,
                line=dict(color='#06d6a0', dash='solid'),
                mode='lines+markers',
                yaxis='y3',
                showlegend=False
            ))

            if not pre_covid_ter.empty and not post_covid_ter.empty:
                last_pre_covid = pre_covid_ter.iloc[-1]
                first_post_covid = post_covid_ter.iloc[0]

                fig.add_trace(go.Scatter(
                    x=[last_pre_covid['season'], first_post_covid['season']],
                    y=[last_pre_covid[tertiary_data.columns[1]], first_post_covid[tertiary_data.columns[1]]],
                    name='COVID-19 Period (No Data)',
                    line=dict(color='#06d6a0', dash='dot', width=1),
                    opacity=0.3,
                    mode='lines',
                    yaxis='y3',
                    showlegend=False
                ))

        # Add comparison if provided (on primary y-axis)
        if comparison_data is not None and not comparison_data.empty:
            comparison_data = comparison_data.sort_values('date')
            comparison_data['season'] = comparison_data['date'].apply(format_season)
            pre_covid_comp = comparison_data[comparison_data['date'] < covid_start]
            post_covid_comp = comparison_data[comparison_data['date'] > covid_end]

            fig.add_trace(go.Scatter(
                x=pre_covid_comp['season'],
                y=pre_covid_comp[comparison_data.columns[1]],
                name='Comparison',
                line=dict(color='#ef476f', dash='solid'),
                mode='lines+markers'
            ))

            fig.add_trace(go.Scatter(
                x=post_covid_comp['season'],
                y=post_covid_comp[comparison_data.columns[1]],
                name='Comparison',
                line=dict(color='#ef476f', dash='solid'),
                mode='lines+markers',
                showlegend=False
            ))

            if not pre_covid_comp.empty and not post_covid_comp.empty:
                last_pre_covid = pre_covid_comp.iloc[-1]
                first_post_covid = post_covid_comp.iloc[0]

                fig.add_trace(go.Scatter(
                    x=[last_pre_covid['season'], first_post_covid['season']],
                    y=[last_pre_covid[comparison_data.columns[1]], first_post_covid[comparison_data.columns[1]]],
                    name='COVID-19 Period (No Data)',
                    line=dict(color='#ef476f', dash='dot', width=1),
                    opacity=0.3,
                    mode='lines',
                    showlegend=False
                ))

        # Update layout for better responsiveness
        layout_updates = {
            'title': title,
            'xaxis_title': 'Season',
            'yaxis_title': y_label,
            'template': 'plotly_white',
            'hovermode': 'x unified',
            'showlegend': True,
            'legend': dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255, 255, 255, 0.8)"
            ),
            'autosize': True,
            'height': 500,
            'margin': dict(l=50, r=50, t=100, b=50),
            'xaxis': dict(
                tickangle=45,
                automargin=True,
                type='category'  # Use category type for discrete season labels
            ),
            'yaxis': dict(
                automargin=True,
                title=y_label,
                side='left'
            )
        }

        # Add second y-axis if there's secondary data
        if secondary_data is not None and not secondary_data.empty:
            layout_updates['yaxis2'] = dict(
                title=secondary_label,
                overlaying='y',
                side='right',
                automargin=True
            )

        # Add third y-axis if there's tertiary data
        if tertiary_data is not None and not tertiary_data.empty:
            layout_updates['yaxis3'] = dict(
                title=tertiary_label,
                overlaying='y',
                side='right',
                position=0.85,
                automargin=True
            )

        fig.update_layout(**layout_updates)

        return fig

    def create_eco_tourism_chart(self, data, title, observation_type='percentage'):
        """Create bar chart for eco-tourism data"""
        if data.empty:
            # Create empty figure with message
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for selected period",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )
        else:
            fig = go.Figure(go.Bar(
                y=data.index,
                x=data.values,
                orientation='h',
                marker_color='#0077b6'
            ))

        x_title = 'Success Rate (%)' if observation_type == 'percentage' else 'Average Count'

        fig.update_layout(
            title=title,
            xaxis_title=x_title,
            yaxis_title='Species',
            template='plotly_white',
            height=400,
            margin=dict(l=150),  # Add more space for species names
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255, 255, 255, 0.8)"
            )
        )

        return fig