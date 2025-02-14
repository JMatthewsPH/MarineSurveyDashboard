import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

class GraphGenerator:
    def __init__(self, data_processor):
        self.data_processor = data_processor

    def create_time_series(self, data, title, y_label, comparison_data=None):
        """Create time series graph with optional comparison"""
        fig = go.Figure()
        
        # Main data
        fig.add_trace(go.Scatter(
            x=data['date'],
            y=data[data.columns[1]],
            name='Current Site',
            line=dict(color='#0077b6')
        ))
        
        # Add comparison if provided
        if comparison_data is not None:
            fig.add_trace(go.Scatter(
                x=comparison_data['date'],
                y=comparison_data[comparison_data.columns[1]],
                name='Comparison',
                line=dict(color='#ef476f')
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title=y_label,
            template='plotly_white',
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return fig

    def create_eco_tourism_chart(self, data, title, observation_type='percentage'):
        """Create bar chart for eco-tourism data"""
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=data.index,
            x=data.values,
            orientation='h',
            marker_color='#0077b6'
        ))
        
        x_title = '% Success Rate' if observation_type == 'percentage' else 'Average Count'
        
        fig.update_layout(
            title=title,
            xaxis_title=x_title,
            yaxis_title='Species',
            template='plotly_white',
            height=400
        )
        
        return fig
