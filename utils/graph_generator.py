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
        
        # Generate complete season timeline from earliest data to current date
        earliest_date = data['date'].min() if not data.empty else pd.Timestamp('2017-01-01')
        current_date = datetime.now()
        complete_seasons = generate_season_timeline(earliest_date, current_date)
        
        # Create a complete dataframe with all seasons, excluding COVID period indicators
        seasons_with_data = set(data['season'].tolist())
        complete_data = []
        
        for season in complete_seasons:
            if season in seasons_with_data:
                # Use actual data
                season_data = data[data['season'] == season].iloc[0]
                complete_data.append({
                    'season': season,
                    'value': season_data[data.columns[1]],
                    'has_data': True,
                    'date': season_data['date']
                })
            else:
                # Add placeholder for missing data (COVID gap will be handled separately)
                complete_data.append({
                    'season': season,
                    'value': None,
                    'has_data': False,
                    'date': None
                })
        
        complete_df = pd.DataFrame(complete_data)
        
        # Dynamically determine COVID gap based on actual data interruption for this site
        # Find the largest gap in data collection to identify COVID period
        if len(data) > 1:
            data_sorted = data.sort_values('date')
            data_sorted['date_diff'] = data_sorted['date'].diff()
            
            # Find the largest gap (assuming COVID gap is the biggest interruption)
            max_gap_idx = data_sorted['date_diff'].idxmax()
            if pd.notna(max_gap_idx) and data_sorted.loc[max_gap_idx, 'date_diff'].days > 365:  # Gap > 1 year
                covid_gap_start = data_sorted[data_sorted.index < max_gap_idx]['date'].max()
                covid_gap_end = data_sorted.loc[max_gap_idx, 'date']
                
                pre_covid = data[data['date'] <= covid_gap_start]
                post_covid = data[data['date'] >= covid_gap_end]
            else:
                # No significant gap found, treat all data as continuous
                pre_covid = data
                post_covid = pd.DataFrame()
                covid_gap_start = None
                covid_gap_end = None
        else:
            # Insufficient data to determine gaps
            pre_covid = data
            post_covid = pd.DataFrame()
            covid_gap_start = None
            covid_gap_end = None

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
        
        # Calculate confidence intervals if requested - reuse the helper function
        metric_column = data.columns[1] if not data.empty else None
        if show_confidence_interval and metric_column:
            # Add confidence intervals for both periods with one helper function
            add_confidence_interval(pre_covid, metric_column)
            add_confidence_interval(post_covid, metric_column)
        
        # Add data with existing values (blue line)
        data_with_values = complete_df[complete_df['has_data'] == True]
        if not data_with_values.empty:
            fig.add_trace(go.Scatter(
                x=data_with_values['season'],
                y=data_with_values['value'],
                name=y_label,
                line=dict(color='#0077b6', dash='solid'),
                mode='lines+markers'
            ))

        # Add placeholder markers for seasons without data (grey) - exclude COVID gap periods
        data_without_values = complete_df[complete_df['has_data'] == False]
        if not data_without_values.empty:
            # Filter out seasons that fall within the detected COVID gap
            filtered_seasons = []
            if covid_gap_start and covid_gap_end:
                for season in data_without_values['season']:
                    # Parse season to determine if it's within COVID gap
                    season_year = int(season.split()[-1])
                    if 'MAR-MAY' in season:
                        season_date = pd.Timestamp(f'{season_year}-03-01')
                    elif 'JUN-AUG' in season:
                        season_date = pd.Timestamp(f'{season_year}-06-01')
                    elif 'SEP-NOV' in season:
                        season_date = pd.Timestamp(f'{season_year}-09-01')
                    else:  # DEC-FEB
                        season_date = pd.Timestamp(f'{season_year-1}-12-01')
                    
                    # Only include if NOT in COVID gap period
                    if not (covid_gap_start <= season_date <= covid_gap_end):
                        filtered_seasons.append(season)
            else:
                # No COVID gap detected, use all seasons without data
                filtered_seasons = data_without_values['season'].tolist()
            
            if filtered_seasons:
                # Use mid-range value for positioning the grey markers
                mid_y = (y_range['min'] + y_range['max']) / 2
                fig.add_trace(go.Scatter(
                    x=filtered_seasons,
                    y=[mid_y] * len(filtered_seasons),
                    name='Data Collection Ongoing',
                    line=dict(color='#cccccc', dash='dash'),
                    marker=dict(color='#cccccc', size=8, symbol='x'),
                    mode='markers',
                    hovertemplate='%{x}<br>Data Collection Ongoing<extra></extra>'
                ))

        # Add COVID period indicator if a gap was detected
        if covid_gap_start and covid_gap_end and not pre_covid.empty and not post_covid.empty:
            last_pre_covid = pre_covid.iloc[-1]
            first_post_covid = post_covid.iloc[0]
            fig.add_trace(go.Scatter(
                x=[last_pre_covid['season'], first_post_covid['season']],
                y=[last_pre_covid[pre_covid.columns[1]], first_post_covid[post_covid.columns[1]]],
                name='COVID-19 Period (No Data)',
                line=dict(color='#888888', dash='3px,10px', width=2),
                mode='lines',
                opacity=0.8,
                showlegend=False
            ))

        # Apply date range filter if provided
        if date_range and len(date_range) == 2:
            start_filter, end_filter = date_range
            if start_filter and end_filter:
                # Convert data['date'] to datetime64 for consistent comparison
                if not data.empty:
                    # Ensure dates are properly converted to pandas timestamps
                    data['date'] = pd.to_datetime(data['date'])
                    
                    # Convert filter dates to pandas timestamps for consistent comparison
                    # Also remove timezone info to avoid comparison issues
                    start_dt = pd.to_datetime(start_filter).tz_localize(None)
                    end_dt = pd.to_datetime(end_filter).tz_localize(None)
                    
                    # Filter the primary data
                    data = data[(data['date'] >= start_dt) & (data['date'] <= end_dt)]
                    # Recalculate COVID gap after date filtering
                    if covid_gap_start and covid_gap_end:
                        pre_covid = data[data['date'] <= covid_gap_start]
                        post_covid = data[data['date'] >= covid_gap_end]
                    
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
                
                # Determine if we should add a legend item for this comparison
                # We want to ensure the legend shows each site, regardless of data period
                have_shown_in_legend = False
                
                # Add pre-COVID comparison data
                if not pre_covid_comp.empty:
                    fig.add_trace(go.Scatter(
                        x=pre_covid_comp['season'],
                        y=pre_covid_comp[comp_df.columns[1]],
                        name=label,
                        line=dict(color=color, dash='solid'),
                        mode='lines+markers'
                    ))
                    have_shown_in_legend = True
                
                # Add post-COVID comparison data
                if not post_covid_comp.empty:
                    fig.add_trace(go.Scatter(
                        x=post_covid_comp['season'],
                        y=post_covid_comp[comp_df.columns[1]],
                        name=label,
                        line=dict(color=color, dash='solid'),
                        mode='lines+markers',
                        # Only hide from legend if we've already added this site to the legend
                        showlegend=not have_shown_in_legend
                    ))
                    have_shown_in_legend = True
                    
                # Ensure site is in legend even if it has no pre-COVID or post-COVID data
                if not have_shown_in_legend:
                    # Add a placeholder with NaN value just to show in legend
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
                'categoryorder': 'array',
                'categoryarray': complete_seasons,
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
        
        # Add text annotation for data collection ongoing (only for post-COVID periods)
        if not data_without_values.empty:
            # Find the latest season with data and the first season without data
            if not data_with_values.empty:
                latest_season_idx = max([complete_seasons.index(s) for s in data_with_values['season']])
                
                # Look for the first season without data that's AFTER COVID period
                post_covid_threshold = pd.Timestamp('2022-03-01')
                first_without_data = None
                
                for idx in range(latest_season_idx + 1, len(complete_seasons)):
                    season = complete_seasons[idx]
                    season_year = int(season.split()[-1])
                    
                    # Parse season to get approximate date
                    if 'MAR-MAY' in season:
                        season_date = pd.Timestamp(f'{season_year}-03-01')
                    elif 'JUN-AUG' in season:
                        season_date = pd.Timestamp(f'{season_year}-06-01')
                    elif 'SEP-NOV' in season:
                        season_date = pd.Timestamp(f'{season_year}-09-01')
                    else:  # DEC-FEB
                        season_date = pd.Timestamp(f'{season_year-1}-12-01')
                    
                    # If this season is after COVID and has no data, use it for annotation
                    if season_date > post_covid_threshold and season in data_without_values['season'].values:
                        first_without_data = season
                        break
                
                # Add annotation only if we found a post-COVID season without data
                if first_without_data:
                    fig.add_annotation(
                        x=first_without_data,
                        y=y_range['max'] * 0.9,
                        text="Data Collection Ongoing",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        arrowcolor="#666666",
                        bgcolor="rgba(255,255,255,0.8)",
                        bordercolor="#666666",
                        borderwidth=1,
                        font=dict(size=12, color="#666666")
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
        
        # Set title and layout
        title = f"Trend Analysis: {metric_name.replace('_', ' ').title()} Across All Sites"
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title=y_title,
            template="plotly_white",
            height=600,  # Increased height for better visualization
            margin=dict(l=40, r=120, t=60, b=60),  # Increased right margin for legend
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