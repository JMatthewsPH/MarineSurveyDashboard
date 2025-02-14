import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np

class GraphGenerator:
    def __init__(self, data_processor):
        self.data_processor = data_processor

    def create_time_series(self, data, title, y_label, comparison_data=None):
        """Create time series graph with optional comparison and data gap handling"""
        fig = go.Figure()

        # COVID-19 gap dates as date objects
        covid_start = date(2019, 9, 1)
        covid_end = date(2022, 3, 1)

        # Main data
        if not data.empty:
            # Sort data by date
            data = data.sort_values('date')

            # Split data into pre and post COVID
            pre_covid = data[data['date'] < covid_start]
            post_covid = data[data['date'] > covid_end]

            # Add main data traces
            fig.add_trace(go.Scatter(
                x=pre_covid['date'],
                y=pre_covid[pre_covid.columns[1]],
                name='Current Site',
                line=dict(color='#0077b6', dash='solid'),
                mode='lines+markers'
            ))

            fig.add_trace(go.Scatter(
                x=post_covid['date'],
                y=post_covid[post_covid.columns[1]],
                name='Current Site',
                line=dict(color='#0077b6', dash='solid'),
                mode='lines+markers',
                showlegend=False
            ))

            # Add dotted line for COVID gap if there's data on both sides
            if not pre_covid.empty and not post_covid.empty:
                last_pre_covid = pre_covid.iloc[-1]
                first_post_covid = post_covid.iloc[0]

                fig.add_trace(go.Scatter(
                    x=[last_pre_covid['date'], first_post_covid['date']],
                    y=[last_pre_covid[pre_covid.columns[1]], first_post_covid[post_covid.columns[1]]],
                    name='COVID-19 Period (No Data)',
                    line=dict(
                        color='#0077b6',
                        dash='dot',
                        width=1
                    ),
                    opacity=0.3,
                    mode='lines'
                ))

        # Add comparison if provided (with same COVID gap handling)
        if comparison_data is not None and not comparison_data.empty:
            comparison_data = comparison_data.sort_values('date')
            pre_covid_comp = comparison_data[comparison_data['date'] < covid_start]
            post_covid_comp = comparison_data[comparison_data['date'] > covid_end]

            fig.add_trace(go.Scatter(
                x=pre_covid_comp['date'],
                y=pre_covid_comp[comparison_data.columns[1]],
                name='Comparison',
                line=dict(color='#ef476f', dash='solid'),
                mode='lines+markers'
            ))

            fig.add_trace(go.Scatter(
                x=post_covid_comp['date'],
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
                    x=[last_pre_covid['date'], first_post_covid['date']],
                    y=[last_pre_covid[comparison_data.columns[1]], first_post_covid[comparison_data.columns[1]]],
                    name='COVID-19 Period (No Data)',
                    line=dict(
                        color='#ef476f',
                        dash='dot',
                        width=1
                    ),
                    opacity=0.3,
                    mode='lines',
                    showlegend=False
                ))

        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title=y_label,
            template='plotly_white',
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",  # horizontal orientation
                yanchor="bottom",
                y=1.02,  # Place it above the chart
                xanchor="center",  # Center horizontally
                x=0.5,  # Center position
                bgcolor="rgba(255, 255, 255, 0.8)"  # Semi-transparent background
            ),
            # Ensure future dates can be accommodated
            xaxis=dict(
                range=[
                    datetime(2017, 1, 1),
                    datetime.now() + timedelta(days=365)
                ],
                tickformat='%b %Y',  # Format to show month and year (e.g., "Jan 2023")
                dtick='M3',  # Show tick every 3 months
                tickangle=45  # Angle the labels for better readability
            )
        )

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
                orientation="h",  # horizontal orientation
                yanchor="bottom",
                y=1.02,  # Place it above the chart
                xanchor="center",  # Center horizontally
                x=0.5,  # Center position
                bgcolor="rgba(255, 255, 255, 0.8)"  # Semi-transparent background
            )
        )

        return fig