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
            'Herbivore Density': {'min': 0, 'max': 5000},  # ind/ha - with 1k intervals
            'Herbivore': {'min': 0, 'max': 5000},          # ind/ha - with 1k intervals
            'Carnivore': {'min': 0, 'max': 5000},           # ind/ha
            'Omnivore Density': {'min': 0, 'max': 300},    # ind/ha - reduced from 1000
            'Omnivore': {'min': 0, 'max': 300},            # ind/ha - reduced from 1000
            'Corallivore': {'min': 0, 'max': 300},          # ind/ha - reduced from 600
            'Corallivore Density': {'min': 0, 'max': 300},  # ind/ha - reduced from 600
            'Rubble': {'min': 0, 'max': 100},               # percentage
            'Rubble Cover': {'min': 0, 'max': 100}          # percentage
        }
        
        # If exact match not found, look for partial matches
        if metric_name not in ranges:
            for key in ranges:
                if key in metric_name:
                    return ranges[key]
        
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
        print(f"DEBUG - Metric name: {metric_name}")
        
        # Force specific settings for Corallivore Density
        if 'Corallivore' in metric_name:
            print("APPLYING SPECIAL CORALLIVORE SETTINGS")
        y_range = self.get_metric_range(metric_name)
        
        # Set custom tick intervals for specific metrics
        y_axis_settings = {
            'automargin': True,
            'title': {
                'text': y_label,
                'standoff': 10
            },
            'side': 'left',
            'range': [y_range['min'], y_range['max']]  # Set fixed y-axis range
        }
        
        # Add specific tick settings for different metrics
        if 'Herbivore' in metric_name:
            y_axis_settings.update({
                'tickmode': 'linear',
                'tick0': 0,
                'dtick': 1000  # 1k intervals for Herbivore density
            })
        elif 'Corallivore' in metric_name:
            y_axis_settings.update({
                'tickmode': 'linear',
                'tick0': 0,
                'dtick': 50  # 50 unit intervals for Corallivore (reduced from 100)
            })
        elif 'Bleaching' in metric_name:
            y_axis_settings.update({
                'tickmode': 'linear',
                'tick0': 0,
                'dtick': 20  # 20% intervals for Bleaching
            })
        elif 'Rubble' in metric_name:
            y_axis_settings.update({
                'tickmode': 'linear',
                'tick0': 0,
                'dtick': 20  # 20% intervals for Rubble
            })

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
            'yaxis': y_axis_settings
        }
        
        # Special handling for specific metrics to ensure they always show properly
        if 'Corallivore' in metric_name:
            layout_updates['yaxis']['tickmode'] = 'linear'
            layout_updates['yaxis']['tick0'] = 0
            layout_updates['yaxis']['dtick'] = 50  # 50 unit intervals for Corallivore
        elif 'Omnivore' in metric_name:
            layout_updates['yaxis']['tickmode'] = 'linear'
            layout_updates['yaxis']['tick0'] = 0
            layout_updates['yaxis']['dtick'] = 50  # 50 unit intervals for Omnivore (reduced from 200)
        elif 'Herbivore' in metric_name:
            layout_updates['yaxis']['tickmode'] = 'linear'
            layout_updates['yaxis']['tick0'] = 0
            layout_updates['yaxis']['dtick'] = 1000  # 1k intervals for Herbivore density
        elif 'Bleaching' in metric_name:
            layout_updates['yaxis']['tickmode'] = 'linear'
            layout_updates['yaxis']['tick0'] = 0
            layout_updates['yaxis']['dtick'] = 20  # 20% intervals for Bleaching
        elif 'Rubble' in metric_name:
            layout_updates['yaxis']['tickmode'] = 'linear'
            layout_updates['yaxis']['tick0'] = 0
            layout_updates['yaxis']['dtick'] = 20  # 20% intervals for Rubble

        fig.update_layout(**layout_updates)
        
        # Final direct fix for Corallivore Density - ensures that the visualization always shows ticks properly
        if 'Corallivore' in metric_name:
            fig.update_yaxes(
                tickmode='linear',
                tick0=0,
                dtick=50,  # 50 unit intervals 
                range=[0, 300]  # Reduced from 600 to better fit actual data
            )
        elif 'Omnivore' in metric_name:
            fig.update_yaxes(
                tickmode='linear',
                tick0=0,
                dtick=50,  # 50 unit intervals (reduced from 200)
                range=[0, 300]  # Reduced from 1000 to better fit actual data
            )
            
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
        
    def create_site_comparison_heatmap(self, matrix_data, metric_column, title=None):
        """
        Create a heatmap for site comparison based on selected metric
        
        Args:
            matrix_data: DataFrame with sites as rows and metrics as columns
            metric_column: Column name to visualize in the heatmap
            title: Optional title for the heatmap
        """
        # Sort data by municipality then site name for better organization
        sorted_data = matrix_data.sort_values(['municipality', 'site'])
        
        # Get color scale based on metric
        if metric_column == 'hard_coral_cover':
            colorscale = 'Blues'  # Use Blues for coral (higher is better)
            zmin, zmax = 0, 100
        elif metric_column == 'fleshy_algae_cover':
            colorscale = 'Reds_r'  # Use reversed Reds for algae (lower is better)
            zmin, zmax = 0, 100
        elif metric_column == 'commercial_biomass':
            colorscale = 'Greens'  # Use Greens for biomass (higher is better)
            zmin, zmax = 0, 3000
        elif 'density' in metric_column:
            colorscale = 'Purples'  # Use Purples for fish density
            # Use different ranges based on fish type
            if metric_column == 'herbivore_density':
                zmin, zmax = 0, 5000
            else:
                zmin, zmax = 0, 300
        else:
            colorscale = 'Viridis'
            zmin, zmax = None, None
            
        # Format annotations and create hover text
        formatted_values = []
        for val in sorted_data[metric_column]:
            if pd.isna(val):
                formatted_values.append("No data")
            elif 'biomass' in metric_column:
                formatted_values.append(f"{val:.1f} kg/ha")
            elif 'cover' in metric_column:
                formatted_values.append(f"{val:.1f}%")
            elif 'density' in metric_column:
                formatted_values.append(f"{val:.1f} ind/ha")
            else:
                formatted_values.append(f"{val:.1f}")
                
        # Create custom hover text
        hover_text = [
            f"Site: {row['site']}<br>Municipality: {row['municipality']}<br>{metric_column.replace('_', ' ').title()}: {val}"
            for val, (_, row) in zip(formatted_values, sorted_data.iterrows())
        ]
            
        # Create the heatmap
        fig = go.Figure(data=go.Heatmap(
            z=sorted_data[metric_column],
            y=sorted_data['site'],
            x=[metric_column.replace('_', ' ').title()],
            colorscale=colorscale,
            zmin=zmin,
            zmax=zmax,
            text=formatted_values,
            hoverinfo='text',
            hovertext=hover_text
        ))
        
        # Add municipality separators
        municipalities = sorted_data['municipality'].unique()
        site_groups = []
        
        for muni in municipalities:
            mask = sorted_data['municipality'] == muni
            site_groups.append({
                'name': muni,
                'start': mask.idxmax(),
                'end': mask.iloc[::-1].idxmax(),
                'count': mask.sum()
            })
            
        # Add shapes to separate municipalities
        shapes = []
        for i, group in enumerate(site_groups):
            if i > 0:
                prev_end = site_groups[i-1]['end']
                if prev_end < group['start']:
                    y_pos = (sorted_data.index.get_loc(prev_end) + 
                            sorted_data.index.get_loc(group['start'])) / 2
                    
                    shapes.append(dict(
                        type="line",
                        x0=-0.5,
                        x1=0.5,
                        y0=y_pos,
                        y1=y_pos,
                        line=dict(color="black", width=2, dash="dot")
                    ))
                    
        # Set layout
        title_text = title if title else f"Site Comparison by {metric_column.replace('_', ' ').title()}"
        
        fig.update_layout(
            title=title_text,
            height=max(400, 20 * len(sorted_data) + 100),  # Adjust height based on number of sites
            margin=dict(l=130, r=20, t=60, b=40),
            yaxis=dict(
                tickfont=dict(size=10),
                title="",
                autorange="reversed"  # Display sites from top to bottom
            ),
            xaxis=dict(
                tickfont=dict(size=12),
                title="",
            ),
            shapes=shapes,
            template="plotly_white"
        )
        
        # Configure download settings
        config = {
            'toImageButtonOptions': {
                'format': 'png',
                'filename': generate_filename(title_text),
                'height': 800,
                'width': 1200,
                'scale': 2
            },
            'displaylogo': False,
            'responsive': True,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d'],
            'scrollZoom': False,
            'doubleClick': 'reset',
            'showTips': True,
            'displayModeBar': 'hover'
        }
        
        return fig, config
    
    def create_geographic_visualization(self, sites_data, metric_column, title=None):
        """
        Create a bubble map plot showing sites colored by metric value
        
        Args:
            sites_data: DataFrame with site info including lat/lon and metric values
            metric_column: Column name to visualize with color and size
            title: Optional title for the map
        """
        # This is a placeholder - in real implementation this would use lat/lon data
        # and create a Mapbox or Scattergeo plot
        
        # For now, create a scatter plot with municipality on x-axis as an approximation
        fig = px.scatter(
            sites_data,
            x='municipality',
            y='site',
            color=metric_column,
            size=metric_column,
            hover_name='site',
            color_continuous_scale=px.colors.sequential.Viridis,
            title=title if title else f"Geographic distribution of {metric_column.replace('_', ' ')}",
            size_max=30,
            opacity=0.8
        )
        
        fig.update_layout(
            height=500,
            template="plotly_white",
            margin=dict(l=40, r=40, t=60, b=60)
        )
        
        # Configure download settings
        config = {
            'toImageButtonOptions': {
                'format': 'png',
                'filename': generate_filename(title if title else f"Geographic distribution"),
                'height': 800,
                'width': 1200,
                'scale': 2
            },
            'displaylogo': False,
            'responsive': True,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d'],
            'scrollZoom': False,
            'doubleClick': 'reset',
            'showTips': True,
            'displayModeBar': 'hover'
        }
        
        return fig, config
        
    def create_multi_site_trend_chart(self, trend_data, metric_name, group_by_municipality=False, highlight_sites=None):
        """
        Create time series with multiple lines for all sites
        
        Args:
            trend_data: DataFrame with 'date', 'site', 'municipality', and metric columns
            metric_name: Name of the metric column to plot
            group_by_municipality: If True, group sites by municipality with same color
            highlight_sites: List of site names to highlight
        """
        # Create figure
        fig = go.Figure()
        
        # Set up color mapping for consistent colors
        if group_by_municipality:
            municipalities = trend_data['municipality'].unique()
            color_map = {muni: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] 
                        for i, muni in enumerate(municipalities)}
        else:
            sites = trend_data['site'].unique()
            color_map = {site: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] 
                        for i, site in enumerate(sites)}
        
        # Add traces for each site or municipality group
        for site in trend_data['site'].unique():
            site_data = trend_data[trend_data['site'] == site]
            
            if site_data.empty:
                continue
                
            municipality = site_data['municipality'].iloc[0]
            
            # Determine line properties
            line_props = {}
            if highlight_sites and site in highlight_sites:
                line_props['width'] = 3
                line_props['dash'] = None
            else:
                line_props['width'] = 1.5
                line_props['dash'] = 'dot' if highlight_sites else None
                
            # Set color based on grouping
            if group_by_municipality:
                color = color_map[municipality]
                name = f"{site} ({municipality})"
            else:
                color = color_map[site]
                name = site
                
            # Add the trace
            fig.add_trace(go.Scatter(
                x=site_data['date'],
                y=site_data[metric_name],
                name=name,
                line=dict(
                    color=color,
                    **line_props
                ),
                mode='lines+markers',
                marker=dict(size=6),
                hovertemplate=f"{site} ({municipality})<br>Date: %{{x}}<br>{metric_name}: %{{y:.1f}}<extra></extra>"
            ))
        
        # Format the y-axis range based on metric type
        y_range = self.get_metric_range(metric_name)
        y_min, y_max = y_range['min'], y_range['max']
        
        # Get an appropriate label based on the metric
        if 'biomass' in metric_name.lower():
            y_title = "Biomass (kg/ha)"
        elif 'coral' in metric_name.lower() or 'algae' in metric_name.lower() or 'cover' in metric_name.lower():
            y_title = "Cover (%)"
        elif 'density' in metric_name.lower():
            y_title = "Density (ind/ha)"
        else:
            y_title = metric_name.replace('_', ' ').title()
        
        # Set title and layout
        title = f"Trend Analysis: {metric_name.replace('_', ' ').title()} Across All Sites"
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title=y_title,
            template="plotly_white",
            height=500,
            margin=dict(l=40, r=40, t=60, b=60),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            yaxis=dict(range=[y_min, y_max])
        )
        
        # Configure download settings
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
            'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d'],
            'scrollZoom': False,
            'doubleClick': 'reset',
            'showTips': True,
            'displayModeBar': 'hover'
        }
        
        return fig, config