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

def generate_season_timeline(start_date, end_date=None):
    """Generate all seasons from start_date to end_date (or current date)"""
    if end_date is None:
        end_date = datetime.now()
    
    seasons = []
    current = pd.to_datetime(start_date)
    target_end = pd.to_datetime(end_date)
    
    while current <= target_end:
        season = format_season(current)
        if season not in seasons:
            seasons.append(season)
        
        # Move to next season (3 months)
        if current.month in [3, 4, 5]:  # MAR-MAY -> JUN-AUG
            current = current.replace(month=6, day=1)
        elif current.month in [6, 7, 8]:  # JUN-AUG -> SEP-NOV
            current = current.replace(month=9, day=1)
        elif current.month in [9, 10, 11]:  # SEP-NOV -> DEC-FEB
            current = current.replace(month=12, day=1)
        else:  # DEC-FEB -> MAR-MAY (next year)
            current = current.replace(year=current.year + 1, month=3, day=1)
    
    return seasons

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
            'Commercial Biomass': {'min': 0, 'max': 100},  # kg/ha
            'Commercial Fish Biomass': {'min': 0, 'max': 100},  # kg/ha
            'Hard Coral Cover': {'min': 0, 'max': 100},     # percentage
            'Fleshy Algae': {'min': 0, 'max': 100},         # percentage
            'Bleaching': {'min': 0, 'max': 100},            # percentage
            'Herbivore Density': {'min': 0, 'max': 2500},  # ind/ha - reduced from 5000
            'Herbivore': {'min': 0, 'max': 2500},          # ind/ha - reduced from 5000
            'Carnivore': {'min': 0, 'max': 300},           # ind/ha - match omnivore scale
            'Carnivore Density': {'min': 0, 'max': 300},   # ind/ha - match omnivore scale
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

    def create_time_series(self, data, title, y_label, comparison_data=None, comparison_labels=None, date_range=None, secondary_data=None, secondary_label=None, tertiary_data=None, tertiary_label=None, show_confidence_interval=False):
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
            show_confidence_interval: Whether to show confidence interval bands (95% CI)
        """
        
        # Debug logging for Lutoban Pier
        if 'Lutoban Pier' in title:
            print(f"DEBUG LUTOBAN MAIN: Creating chart for {title}")
            print(f"DEBUG LUTOBAN MAIN: Data shape: {data.shape}")
            print(f"DEBUG LUTOBAN MAIN: Data empty? {data.empty}")
            if not data.empty:
                print(f"DEBUG LUTOBAN MAIN: Data columns: {list(data.columns)}")
                print(f"DEBUG LUTOBAN MAIN: First few rows:")
                print(data.head())

        # Create base figure
        fig = go.Figure()

        # Configure basic download settings with mobile-friendly options - predefine static config
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
            'modeBarButtons': [['zoomIn2d', 'zoomOut2d', 'resetScale2d', 'toImage']],
            'scrollZoom': False,
            'doubleClick': 'reset',
            'showTips': True,
            'displayModeBar': 'hover'
        }

        # If no data, return empty figure with basic config
        if data.empty:
            return fig, config

        # Sort data by date and get date range for filename - optimization: sort only once
        if not isinstance(data['date'].iloc[0], pd.Timestamp):
            data['date'] = pd.to_datetime(data['date'])
        data = data.sort_values('date')
        
        # Precompute these values to avoid recalculating them later
        start_date = data['date'].min()
        end_date = data['date'].max()

        # Update filename with date range - only compute once
        config['toImageButtonOptions']['filename'] = generate_filename(title, start_date, end_date)

        # Format dates as seasons - vectorized operation
        data['season'] = data['date'].apply(format_season)
        
        # Sort data by date to ensure proper timeline ordering
        data_sorted = data.sort_values('date').copy()
        

        
        # Use all actual data but properly aggregate by season
        # First, properly aggregate by season (group by season and take the mean)
        metric_column = data_sorted.columns[1]  # Get the actual metric column name
        
        # Group by season and aggregate (using mean for multiple values in same season)
        aggregated_data = data_sorted.groupby('season').agg({
            'date': 'first',  # Take first date for each season
            metric_column: 'mean'  # Average if multiple surveys in same season
        }).reset_index()
        
        # Rename the metric column to 'value' for consistent processing
        complete_df = aggregated_data.rename(columns={metric_column: 'value'})
        complete_df['has_data'] = True
        
        # Sort by date to ensure proper chronological order
        complete_df = complete_df.sort_values('date')
        
        # Data is ready for gap detection in the main plotting section

        # Get the metric name from the title - only compute once
        metric_name = title.split(' - ')[0].strip()
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
                'dtick': 500  # 500 unit intervals for Herbivore density
            })
        elif 'Carnivore' in metric_name:
            y_axis_settings.update({
                'tickmode': 'linear',
                'tick0': 0,
                'dtick': 50  # 50 unit intervals for Carnivore density
            })
        elif 'Omnivore' in metric_name:
            y_axis_settings.update({
                'tickmode': 'linear',
                'tick0': 0,
                'dtick': 50  # 50 unit intervals for Omnivore density
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
        elif 'Commercial Fish Biomass' in metric_name or 'Commercial Biomass' in metric_name:
            y_axis_settings.update({
                'tickmode': 'linear',
                'tick0': 0,
                'dtick': 20  # 20 unit intervals for Commercial Fish Biomass
            })

        # Helper function to calculate and add confidence intervals
        def add_confidence_interval(data_subset, metric_column):
            if data_subset.empty:
                return
                
            # Get the y-values (using direct column name is faster)
            y_values = data_subset[metric_column].values
            
            # Vectorized calculations are much faster
            n_values = len(y_values)
            if n_values <= 1:
                return
                
            # Vectorized calculations for confidence intervals
            sem = np.std(y_values, ddof=1) / np.sqrt(n_values)
            ci_lower = np.maximum(y_values - 1.96 * sem, 0)  # Don't go below 0
            ci_upper = y_values + 1.96 * sem
            
            # Add confidence interval traces - add both at once
            fig.add_trace(go.Scatter(
                x=data_subset['season'],
                y=ci_upper,
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_trace(go.Scatter(
                x=data_subset['season'],
                y=ci_lower,
                mode='lines',
                line=dict(width=0),
                fill='tonexty',
                fillcolor='rgba(0, 119, 182, 0.2)',  # Light blue with transparency
                showlegend=False,
                name='95% Confidence Interval',
                hoverinfo='skip'
            ))
        
        # Calculate confidence intervals if requested (using complete dataset)
        metric_column = data.columns[1] if not data.empty else None
        if show_confidence_interval and metric_column and not complete_df.empty:
            # Use complete dataset for confidence intervals
            complete_df_for_ci = complete_df.copy()
            complete_df_for_ci[metric_column] = complete_df_for_ci['value']
            add_confidence_interval(complete_df_for_ci, metric_column)
        
        # Add data points with automatic gap detection for COVID periods
        # Detect gaps in consecutive data and add dotted connectors
        
        # Sort data chronologically
        complete_df_sorted = complete_df.sort_values('date').reset_index(drop=True)
        
        # Find gaps (more than 6 months between consecutive data points)
        gaps = []
        if 'Lutoban Pier' in title:
            print(f"DEBUG LUTOBAN: Checking {len(complete_df_sorted)} data points for gaps")
            for i in range(len(complete_df_sorted)):
                print(f"DEBUG LUTOBAN: Point {i}: {complete_df_sorted.iloc[i]['date']} - {complete_df_sorted.iloc[i]['season']}")
        
        for i in range(len(complete_df_sorted) - 1):
            current_date = complete_df_sorted.iloc[i]['date']
            next_date = complete_df_sorted.iloc[i + 1]['date']
            
            # Calculate months between dates
            months_diff = (next_date.year - current_date.year) * 12 + (next_date.month - current_date.month)
            
            if 'Lutoban Pier' in title:
                print(f"DEBUG LUTOBAN: Gap between {current_date.strftime('%Y-%m-%d')} and {next_date.strftime('%Y-%m-%d')} = {months_diff} months")
            
            # If gap is more than 6 months, it's likely a COVID period
            if months_diff > 6:
                if 'Lutoban Pier' in title:
                    print(f"DEBUG LUTOBAN: Found gap! Adding dotted line.")
                gaps.append({
                    'before_idx': i,
                    'after_idx': i + 1,
                    'before_season': complete_df_sorted.iloc[i]['season'],
                    'after_season': complete_df_sorted.iloc[i + 1]['season'],
                    'before_value': complete_df_sorted.iloc[i]['value'],
                    'after_value': complete_df_sorted.iloc[i + 1]['value']
                })
        

        
        # Add all data points as one trace
        fig.add_trace(go.Scatter(
            x=complete_df['season'],
            y=complete_df['value'],
            name=y_label,
            line=dict(color='#0077b6', dash='solid'),
            mode='lines+markers',
            showlegend=True
        ))
        
        # Add dotted lines for each detected gap
        for i, gap in enumerate(gaps):
            fig.add_trace(go.Scatter(
                x=[gap['before_season'], gap['after_season']],
                y=[gap['before_value'], gap['after_value']],
                line=dict(color='#cccccc', dash='dot', width=2),
                mode='lines',
                name='COVID-19 Period (No Data)' if i == 0 else '',
                showlegend=(i == 0)  # Only show in legend once
            ))

        # Apply date range filter if provided
        if date_range and len(date_range) == 2:
            start_filter, end_filter = date_range
            if start_filter and end_filter:
                # Convert complete_df['date'] to datetime64 for consistent comparison
                if not complete_df.empty:
                    # Ensure dates are properly converted to pandas timestamps
                    complete_df['date'] = pd.to_datetime(complete_df['date'])
                    
                    # Convert filter dates to pandas timestamps for consistent comparison
                    # Also remove timezone info to avoid comparison issues
                    start_dt = pd.to_datetime(start_filter).tz_localize(None)
                    end_dt = pd.to_datetime(end_filter).tz_localize(None)
                    
                    # Filter the primary data
                    complete_df = complete_df[(complete_df['date'] >= start_dt) & (complete_df['date'] <= end_dt)]
                    
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
                        comp_df = comp_df.copy()
                        comp_df['date'] = pd.to_datetime(comp_df['date'])
                        
                        # Convert filter dates to pandas timestamps for consistent comparison
                        # Also remove timezone info to avoid comparison issues
                        start_dt = pd.to_datetime(start_filter).tz_localize(None)
                        end_dt = pd.to_datetime(end_filter).tz_localize(None)
                        
                        # Filter using consistent timestamp objects
                        comp_df = comp_df[(comp_df['date'] >= start_dt) & (comp_df['date'] <= end_dt)]
                
                # Sort and format data
                if not comp_df.empty and 'date' in comp_df.columns:
                    comp_df = comp_df.sort_values('date')
                
                # Ensure comp_df['date'] is in datetime64 format
                if not comp_df.empty:
                    comp_df['date'] = pd.to_datetime(comp_df['date'])
                    comp_df['season'] = comp_df['date'].apply(format_season)
                    
                    # Sort by date for gap detection
                    comp_df_sorted = comp_df.sort_values('date').reset_index(drop=True)
                    
                    # Find gaps in this comparison data
                    comp_gaps = []
                    for j in range(len(comp_df_sorted) - 1):
                        current_date = comp_df_sorted.iloc[j]['date']
                        next_date = comp_df_sorted.iloc[j + 1]['date']
                        
                        # Calculate months between dates
                        months_diff = (next_date.year - current_date.year) * 12 + (next_date.month - current_date.month)
                        
                        # If gap is more than 6 months, it's likely a COVID period
                        if months_diff > 6:
                            comp_gaps.append({
                                'before_idx': j,
                                'after_idx': j + 1,
                                'before_season': comp_df_sorted.iloc[j]['season'],
                                'after_season': comp_df_sorted.iloc[j + 1]['season'],
                                'before_value': comp_df_sorted.iloc[j][comp_df.columns[1]],
                                'after_value': comp_df_sorted.iloc[j + 1][comp_df.columns[1]]
                            })
                else:
                    # For empty dataframes, ensure we have a season column
                    if 'season' not in comp_df.columns:
                        comp_df['season'] = pd.Series(dtype='object')
                    comp_gaps = []
                
                # Pick a color (cycle through the available colors)
                color = comparison_colors[i % len(comparison_colors)]
                
                # Determine if we should add a legend item for this comparison
                # We want to ensure the legend shows each site, regardless of data period
                have_shown_in_legend = False
                
                # Add comparison data as one continuous trace
                if not comp_df.empty:
                    fig.add_trace(go.Scatter(
                        x=comp_df['season'],
                        y=comp_df[comp_df.columns[1]],
                        name=label,
                        line=dict(color=color, dash='solid'),
                        mode='lines+markers'
                    ))
                    have_shown_in_legend = True
                    
                    # Add dotted connectors for gaps in this comparison data
                    for j, gap in enumerate(comp_gaps):
                        fig.add_trace(go.Scatter(
                            x=[gap['before_season'], gap['after_season']],
                            y=[gap['before_value'], gap['after_value']],
                            line=dict(color='#cccccc', dash='dot', width=2),
                            mode='lines',
                            name='COVID-19 Period (No Data)' if i == 0 and j == 0 else '',
                            showlegend=(i == 0 and j == 0)  # Only show in legend once
                        ))
                else:
                    # Ensure site is in legend even if it has no data
                    placeholder_season = "2022Q1"  # Default placeholder season
                    fig.add_trace(go.Scatter(
                        x=[placeholder_season],
                        y=[None],  # Using None for better handling in plotly
                        name=label,
                        line=dict(color=color, dash='solid'),
                        mode='markers',
                        marker=dict(opacity=0),  # Transparent marker
                        showlegend=True
                    ))
                    have_shown_in_legend = True

        # Update layout with fixed y-axis range and responsive design
        layout_updates = {
            'title': {
                'text': title,
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 18},  # Slightly larger title
                'xref': 'paper',
                'yref': 'paper'
            },
            'xaxis_title': 'Season',
            'yaxis_title': y_label,
            'template': 'plotly_white',
            'hovermode': 'x unified',
            'showlegend': True,
            'legend': {
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': -0.4,
                'xanchor': 'center',
                'x': 0.5,
                'bgcolor': 'rgba(255, 255, 255, 1)',
                'bordercolor': 'rgba(0,0,0,0.1)',
                'borderwidth': 1
            },
            'autosize': True,  # Enable responsive resizing
            'height': 550,
            'margin': {
                'l': 50,
                'r': 30,
                't': 100,  # Even more space for annotation title
                'b': 140  # Reduced bottom margin for better legend positioning
            },
            'xaxis': {
                'tickangle': 45,
                'automargin': True,
                'type': 'category',
                'categoryorder': 'trace',  # Maintain order as data appears in traces
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
        
        # Ensure title centering is properly applied
        fig.update_layout(
            title={
                'text': title,
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 18},
                'xref': 'paper',
                'yref': 'paper',
                'pad': {'t': 20}
            }
        )
        
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
        
        # Skip annotation logic for now - focus on showing all data correctly
            
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
                # Define the exact buttons to show: zoom in, zoom out, reset view, download
                'modeBarButtons': [['zoomIn2d', 'zoomOut2d', 'resetScale2d', 'toImage']],
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
            # Define the exact buttons to show: zoom in, zoom out, reset view, download
            'modeBarButtons': [['zoomIn2d', 'zoomOut2d', 'resetScale2d', 'toImage']],
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
            'displayModeBar': True,
            # Define the exact buttons to show: zoom in, zoom out, reset view, download
            'modeBarButtons': [['zoomIn2d', 'zoomOut2d', 'resetScale2d', 'toImage']],
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
        
        # First, handle NaN values in the metric column by replacing them with 0
        # Create a copy to avoid modifying the original dataframe
        chart_data = sites_data.copy()
        
        # Fill NaN values with 0 for the metric column
        chart_data[metric_column] = chart_data[metric_column].fillna(0)
        
        # Create a size column that's always positive (minimum 5) for better visibility
        # Scale the values to a reasonable range for the scatter plot
        # Handle different metric scales appropriately
        if 'biomass' in metric_column.lower():
            # Biomass values tend to be larger (e.g., 100-2000), so we divide by 100
            chart_data['marker_size'] = chart_data[metric_column].apply(
                lambda x: max(5, min(30, x/100)) if pd.notnull(x) else 5
            )
        else:
            # Percentage values (0-100)
            chart_data['marker_size'] = chart_data[metric_column].apply(
                lambda x: max(5, min(30, x)) if pd.notnull(x) else 5
            )
        
        # Now we're sure marker_size doesn't contain any NaN values
        # For now, create a scatter plot with municipality on x-axis as an approximation
        fig = px.scatter(
            chart_data,
            x='municipality',
            y='site',
            color=metric_column,
            size='marker_size',  # Use our calculated size column
            hover_name='site',
            color_continuous_scale=px.colors.sequential.Viridis,
            title=title if title else f"Geographic distribution of {metric_column.replace('_', ' ')}",
            size_max=40,
            opacity=0.8
        )
        
        # Add appropriate labels in the hover data based on the metric type
        hover_template = ""
        if 'biomass' in metric_column:
            hover_template = "<b>%{hovertext}</b><br>Municipality: %{x}<br>Biomass: %{marker.color:.1f} kg/ha<extra></extra>"
        elif 'coral' in metric_column or 'algae' in metric_column:
            hover_template = "<b>%{hovertext}</b><br>Municipality: %{x}<br>Cover: %{marker.color:.1f}%<extra></extra>"
        elif 'density' in metric_column:
            hover_template = "<b>%{hovertext}</b><br>Municipality: %{x}<br>Density: %{marker.color:.1f} ind/ha<extra></extra>"
        else:
            hover_template = "<b>%{hovertext}</b><br>Municipality: %{x}<br>Value: %{marker.color:.1f}<extra></extra>"
            
        fig.update_traces(
            hovertemplate=hover_template
        )
        
        fig.update_layout(
            height=500,
            template="plotly_white",
            margin=dict(l=40, r=40, t=60, b=60),
            xaxis_title="Municipality",
            yaxis_title="Site"
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
            'displayModeBar': True,
            # Define the exact buttons to show: zoom in, zoom out, reset view, download
            'modeBarButtons': [['zoomIn2d', 'zoomOut2d', 'resetScale2d', 'toImage']],
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
                
            # Add the trace with improved styling
            fig.add_trace(go.Scatter(
                x=site_data['date'],
                y=site_data[metric_name],
                name=name,
                line=dict(
                    color=color,
                    **line_props
                ),
                mode='lines+markers',
                marker=dict(
                    size=8,
                    line=dict(width=1, color='white')  # Add white outline to markers
                ),
                hovertemplate=f"{site} ({municipality})<br>Date: %{{x}}<br>{metric_name}: %{{y:.1f}}<extra></extra>"
            ))
        
        # Format the y-axis range based on metric type - use fixed range of 0-100 with 10 unit spacing
        y_min, y_max = 0, 100
        
        # Get an appropriate label based on the metric
        if 'biomass' in metric_name.lower():
            y_title = "Biomass (kg/ha)"
        elif 'coral' in metric_name.lower() or 'algae' in metric_name.lower() or 'cover' in metric_name.lower():
            y_title = "Cover (%)"
        elif 'density' in metric_name.lower():
            y_title = "Density (ind/ha)"
        else:
            y_title = metric_name.replace('_', ' ').title()
        
        # Set title and layout with centered title and responsive design
        title = f"Trend Analysis: {metric_name.replace('_', ' ').title()} Across All Sites"
        fig.update_layout(
            title={
                'text': title,
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 18}
            },
            xaxis_title="Date",
            yaxis_title=y_title,
            template="plotly_white",
            height=600,  # Increased height for better visualization
            margin=dict(l=40, r=120, t=80, b=60),  # More top margin for centered title
            autosize=True,  # Enable responsive resizing
            legend=dict(
                orientation="v",  # Change to vertical orientation
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,  # Position legend to the right of the chart
                bgcolor="rgba(255,255,255,0.8)",  # Add semi-transparent background
                bordercolor="lightgray",
                borderwidth=1
            ),
            yaxis=dict(
                range=[y_min, y_max],
                tickmode='linear',
                tick0=0,
                dtick=10,  # 10 unit spacing between ticks
                gridcolor='lightgray'
            )
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
            'displayModeBar': True,
            # Define the exact buttons to show: zoom in, zoom out, reset view, download
            'modeBarButtons': [['zoomIn2d', 'zoomOut2d', 'resetScale2d', 'toImage']],
            'scrollZoom': False,
            'doubleClick': 'reset',
            'showTips': True,
            'displayModeBar': 'hover'
        }
        
        return fig, config
    def create_municipality_grouped_bar_chart(self, matrix_data, metric_column, title=None, y_axis_label=None):
        """
        Create a bar chart with sites grouped by municipality, using red-yellow-green color coding
        for health indicators, starting Y-axis from 0
        
        Args:
            matrix_data: DataFrame with site, municipality, and metric columns
            metric_column: Column name to visualize
            title: Optional title for the chart
            y_axis_label: Label for Y-axis including units
        """
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            import numpy as np
            
            # Clean the data - replace NaN with 0 instead of dropping rows
            clean_data = matrix_data.copy()
            clean_data[metric_column] = clean_data[metric_column].fillna(0)
            
            if clean_data.empty:
                # Return empty chart if no data
                fig = go.Figure()
                fig.add_annotation(
                    text="No data available for this metric",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=16, color="gray")
                )
                fig.update_layout(
                    title=title or "No Data Available",
                    height=400,
                    template="plotly_white"
                )
                config = {'displaylogo': False, 'responsive': True}
                return fig, config
            
            # Sort by municipality and then by site name for consistent ordering
            clean_data = clean_data.sort_values(['municipality', 'site'])
            
            # Create site labels with municipality grouping for X-axis
            clean_data['site_label'] = clean_data['site']
            
            # Determine color mapping based on metric values
            min_val = clean_data[metric_column].min()
            max_val = clean_data[metric_column].max()
            
            # Create color scale: red (low) -> yellow (medium) -> green (high)
            # For biomass and positive indicators, high values are green
            # For negative indicators like bleaching, we'd reverse this
            if 'biomass' in metric_column.lower() or 'coral' in metric_column.lower():
                # Higher values are better (green)
                colorscale = 'RdYlGn'  # Red-Yellow-Green
            elif 'bleaching' in metric_column.lower() or 'algae' in metric_column.lower():
                # Lower values are better (reverse scale)
                colorscale = 'RdYlGn_r'  # Green-Yellow-Red (reversed)
            else:
                # Default to red-yellow-green for most metrics
                colorscale = 'RdYlGn'
            
            # Create the bar chart with color mapping (no title here - will be set in update_layout)
            fig = px.bar(
                clean_data,
                x='site_label',
                y=metric_column,
                color=metric_column,
                color_continuous_scale=colorscale,
                labels={
                    'site_label': 'Site',
                    metric_column: y_axis_label or metric_column.replace('_', ' ').title()
                },
                hover_data=['municipality']
            )
            
            # Customize the layout with centered title and responsive design
            fig.update_layout(
                title={
                    'text': title or f"Site Comparison: {metric_column.replace('_', ' ').title()}",
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'size': 18}
                },
                height=500,
                template="plotly_white",
                margin=dict(l=60, r=60, t=100, b=120),  # More top margin for centered title
                autosize=True,  # Enable responsive resizing
                xaxis=dict(
                    title="Sites (Grouped by Municipality)",
                    tickangle=-45,
                    tickmode='linear'
                ),
                yaxis=dict(
                    title=y_axis_label or metric_column.replace('_', ' ').title(),
                    range=[0, max_val * 1.1],  # Start from 0, add 10% padding at top
                    gridcolor='lightgray'
                ),
                showlegend=False  # Hide color legend to save space
            )
            
            # Add municipality group separators
            municipalities = clean_data['municipality'].unique()
            x_pos = 0
            for i, municipality in enumerate(municipalities):
                muni_data = clean_data[clean_data['municipality'] == municipality]
                sites_in_muni = len(muni_data)
                
                # Add vertical line to separate municipalities (except before first)
                if i > 0:
                    fig.add_vline(
                        x=x_pos - 0.5,
                        line_width=2,
                        line_dash="dash",
                        line_color="gray",
                        opacity=0.5
                    )
                
                # Add municipality label
                fig.add_annotation(
                    x=x_pos + (sites_in_muni - 1) / 2,
                    y=max_val * 1.05,
                    text=f"<b>{municipality}</b>",
                    showarrow=False,
                    font=dict(size=12, color="darkblue"),
                    yref="y"
                )
                
                x_pos += sites_in_muni
            
            # Enhanced hover template
            if 'biomass' in metric_column.lower():
                hover_template = "<b>%{x}</b><br>Municipality: %{customdata[0]}<br>Biomass: %{y:.1f} kg/ha<extra></extra>"
            elif 'coral' in metric_column.lower() or 'algae' in metric_column.lower():
                hover_template = "<b>%{x}</b><br>Municipality: %{customdata[0]}<br>Cover: %{y:.1f}%<extra></extra>"
            elif 'density' in metric_column.lower():
                hover_template = "<b>%{x}</b><br>Municipality: %{customdata[0]}<br>Density: %{y:.1f} ind/ha<extra></extra>"
            else:
                hover_template = "<b>%{x}</b><br>Municipality: %{customdata[0]}<br>Value: %{y:.1f}<extra></extra>"
            
            fig.update_traces(hovertemplate=hover_template)
            
            # Configure download settings
            config = {
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': generate_filename(title or f"Site_Comparison_{metric_column}"),
                    'height': 800,
                    'width': 1200,
                    'scale': 2
                },
                'displaylogo': False,
                'responsive': True,
                'displayModeBar': True,
                'modeBarButtons': [['zoomIn2d', 'zoomOut2d', 'resetScale2d', 'toImage']],
                'scrollZoom': False,
                'doubleClick': 'reset',
                'showTips': True,
                'displayModeBar': 'hover'
            }
            
            return fig, config
            
        except Exception as e:
            print(f"Error creating municipality grouped bar chart: {str(e)}")
            # Return a simple error chart
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=14, color="red")
            )
            config = {'displaylogo': False, 'responsive': True}
            return fig, config
