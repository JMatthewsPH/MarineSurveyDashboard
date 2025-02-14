import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

class GraphGenerator:
    def __init__(self, data_processor):
        self.data_processor = data_processor

    def create_time_series(self, data, title, y_label, comparison_data=None):
        """Create time series graph with optional comparison and data gap handling"""
        fig = go.Figure()

        # Main data
        if not data.empty:
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=data[data.columns[1]],
                name='Current Site',
                line=dict(
                    color='#0077b6',
                    dash='solid'
                ),
                mode='lines+markers'
            ))

        # Add comparison if provided
        if comparison_data is not None and not comparison_data.empty:
            fig.add_trace(go.Scatter(
                x=comparison_data['date'],
                y=comparison_data[comparison_data.columns[1]],
                name='Comparison',
                line=dict(
                    color='#ef476f',
                    dash='solid'
                ),
                mode='lines+markers'
            ))

        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title=y_label,
            template='plotly_white',
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
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
            margin=dict(l=150)  # Add more space for species names
        )

        return fig