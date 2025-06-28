"""
Map Generator for Interactive Biomass Heatmap

This module creates interactive maps showing biomass distribution across MPA sites
using Folium for web-based interactive mapping.
"""

import folium
from folium.plugins import HeatMap
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class MapGenerator:
    """
    Generates interactive maps for marine conservation data visualization
    """
    
    def __init__(self, data_processor):
        """Initialize with a data processor instance"""
        self.data_processor = data_processor
        
    def create_biomass_heatmap(self, center_lat=9.1, center_lon=123.1, zoom_start=10):
        """
        Create an interactive heatmap showing biomass distribution across all MPA sites
        
        Args:
            center_lat: Latitude for map center
            center_lon: Longitude for map center  
            zoom_start: Initial zoom level
            
        Returns:
            Folium map object with biomass heatmap
        """
        try:
            # Get all sites with coordinates and latest biomass data
            sites = self.data_processor.get_sites()
            
            # Create base map with higher max zoom to prevent data unavailable issues
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=zoom_start,
                tiles='OpenStreetMap',
                max_zoom=20  # Increased max zoom
            )
            
            # Add satellite imagery layer with higher zoom levels
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='Satellite',
                overlay=False,
                control=True,
                max_zoom=20
            ).add_to(m)
            
            # Add a lighter sea-focused tile layer with higher zoom
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
                attr='Esri Ocean',
                name='Ocean View',
                overlay=False,
                control=True,
                max_zoom=20
            ).add_to(m)
            
            # Add CartoDB Positron as backup with excellent zoom support
            folium.TileLayer(
                tiles='https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png',
                attr='CartoDB',
                name='Light Map',
                overlay=False,
                control=True,
                max_zoom=20,
                subdomains='abcd'
            ).add_to(m)
            
            # Collect data for heatmap and markers
            heatmap_data = []
            marker_data = []
            biomass_values = []
            
            # First pass: collect all biomass values to calculate dynamic thresholds
            for site in sites:
                if site.latitude and site.longitude:
                    # Get latest biomass data for this site
                    biomass_df = self.data_processor.get_biomass_data(site.name)
                    
                    if not biomass_df.empty:
                        # Get the most recent biomass value - check column name
                        possible_cols = ['Commercial Biomass', 'commercial_biomass', 'biomass', 'commercial_fish_biomass']
                        biomass_col = None
                        for col in possible_cols:
                            if col in biomass_df.columns:
                                biomass_col = col
                                break
                        
                        if biomass_col is None:
                            continue  # Skip if no biomass data
                            
                        latest_biomass = biomass_df[biomass_col].iloc[-1]
                        biomass_values.append(latest_biomass)
            
            # Calculate dynamic thresholds based on data distribution
            if biomass_values:
                import numpy as np
                biomass_array = np.array(biomass_values)
                max_biomass = np.max(biomass_array)
                min_biomass = np.min(biomass_array)
                
                # Calculate percentile-based thresholds for more dynamic scaling
                high_threshold = np.percentile(biomass_array, 66.67)  # Top third
                medium_threshold = np.percentile(biomass_array, 33.33)  # Middle third
                
                # Ensure reasonable minimum gaps between thresholds
                if high_threshold - medium_threshold < 2:
                    high_threshold = medium_threshold + 2
                if medium_threshold - min_biomass < 1:
                    medium_threshold = min_biomass + 1
            else:
                # Fallback values if no data
                max_biomass = 21
                high_threshold = 15
                medium_threshold = 8
            
            # Second pass: create markers with dynamic thresholds
            for site in sites:
                if site.latitude and site.longitude:
                    # Get latest biomass data for this site
                    biomass_df = self.data_processor.get_biomass_data(site.name)
                    
                    if not biomass_df.empty:
                        # Get the most recent biomass value
                        possible_cols = ['Commercial Biomass', 'commercial_biomass', 'biomass', 'commercial_fish_biomass']
                        biomass_col = None
                        for col in possible_cols:
                            if col in biomass_df.columns:
                                biomass_col = col
                                break
                        
                        if biomass_col is None:
                            continue  # Skip if no biomass data
                            
                        latest_biomass = biomass_df[biomass_col].iloc[-1]
                        latest_date = biomass_df['date'].iloc[-1]
                        
                        # Add to heatmap data with dynamic scaling using same offset as markers
                        weight = max(0.1, min(latest_biomass / max_biomass * 2.0, 2.0))
                        offset_longitude = site.longitude + 0.0005  # Same offset as markers
                        heatmap_data.append([site.latitude, offset_longitude, weight])
                        
                        # Determine color based on dynamic thresholds
                        if latest_biomass >= high_threshold:
                            color = 'green'
                            icon = 'leaf'
                        elif latest_biomass >= medium_threshold:
                            color = 'orange'
                            icon = 'warning-sign'
                        else:
                            color = 'red'
                            icon = 'exclamation-sign'
                        
                        # Create popup content
                        popup_html = f"""
                        <div style="font-family: Arial, sans-serif; width: 200px;">
                            <h4 style="margin: 0; color: #2c3e50;">{site.name}</h4>
                            <p style="margin: 5px 0; color: #7f8c8d;"><b>Municipality:</b> {site.municipality}</p>
                            <p style="margin: 5px 0; color: #2c3e50;"><b>Latest Biomass:</b> {latest_biomass:.1f} kg/ha</p>
                            <p style="margin: 5px 0; color: #7f8c8d;"><b>Date:</b> {latest_date.strftime('%b %Y')}</p>
                            <p style="margin: 5px 0; color: #7f8c8d;"><b>Coordinates:</b> {site.latitude:.4f}, {site.longitude:.4f}</p>
                        </div>
                        """
                        
                        # Offset marker seaward by ~20px (approximately 0.0005 degrees longitude)
                        # This moves markers away from shoreline for better visibility
                        offset_longitude = site.longitude + 0.0005  # Move east/seaward
                        
                        # Add tiny circle marker instead of large pin
                        folium.CircleMarker(
                            location=[site.latitude, offset_longitude],
                            radius=4,  # Tiny size like click markers
                            popup=folium.Popup(popup_html, max_width=250),
                            tooltip=f"{site.name}: {latest_biomass:.1f} kg/ha",
                            color='white',
                            weight=1,
                            fillColor=color,
                            fillOpacity=0.8
                        ).add_to(m)
                        
                        marker_data.append({
                            'name': site.name,
                            'municipality': site.municipality,
                            'biomass': latest_biomass,
                            'lat': site.latitude,
                            'lon': site.longitude
                        })
            
            # Add heatmap layer if we have data with reduced transparency and smaller radius
            if heatmap_data:
                HeatMap(
                    heatmap_data,
                    name='Biomass Heatmap',
                    min_opacity=0.15,  # Reduced transparency
                    max_zoom=20,       # Increased to match map max zoom
                    radius=15,  # Smaller radius to minimize land spillover
                    blur=8,     # Less blur to contain effect better
                    gradient={0.2: 'red', 0.4: 'orange', 0.6: 'yellow', 1.0: 'green'}
                ).add_to(m)
            

            # Add layer control
            folium.LayerControl().add_to(m)
            
            # Add a dynamic legend based on calculated thresholds
            legend_html = f'''
            <div style="
                position: fixed; 
                bottom: 50px; right: 50px; width: 220px; height: 130px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px; border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            ">
            <h4 style="margin-top: 0;">Commercial Biomass</h4>
            <p><i class="glyphicon glyphicon-leaf" style="color: green;"></i> High (≥{high_threshold:.1f} kg/ha)</p>
            <p><i class="glyphicon glyphicon-warning-sign" style="color: orange;"></i> Medium ({medium_threshold:.1f}-{high_threshold:.1f} kg/ha)</p>
            <p><i class="glyphicon glyphicon-exclamation-sign" style="color: red;"></i> Low (<{medium_threshold:.1f} kg/ha)</p>
            <p style="font-size: 12px; color: #666; margin-top: 5px;">Range: {min_biomass:.1f}-{max_biomass:.1f} kg/ha</p>
            </div>
            '''
            m.get_root().add_child(folium.Element(legend_html))
            
            logger.info(f"Created biomass heatmap with {len(marker_data)} sites")
            return m
            
        except Exception as e:
            logger.error(f"Error creating biomass heatmap: {str(e)}")
            # Return a basic map if there's an error
            return folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)
    
    def create_metric_map(self, metric='hard_coral', center_lat=9.1, center_lon=123.1, zoom_start=10):
        """
        Create an interactive map for any metric type
        
        Args:
            metric: Metric type to visualize
            center_lat: Latitude for map center
            center_lon: Longitude for map center
            zoom_start: Initial zoom level
            
        Returns:
            Folium map object with metric visualization
        """
        try:
            sites = self.data_processor.get_sites()
            
            # Create base map
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=zoom_start,
                tiles='OpenStreetMap'
            )
            
            # Get display name for metric
            display_name = self.data_processor.DISPLAY_NAMES.get(
                self.data_processor.METRIC_MAP.get(metric, metric), 
                metric.replace('_', ' ').title()
            )
            
            for site in sites:
                if site.latitude and site.longitude:
                    # Get metric data for this site
                    if metric == 'commercial_biomass':
                        metric_df = self.data_processor.get_biomass_data(site.name)
                        value_col = 'commercial_biomass'
                    else:
                        metric_df = self.data_processor.get_metric_data(site.name, metric)
                        value_col = self.data_processor.METRIC_MAP.get(metric, metric)
                    
                    if not metric_df.empty and value_col in metric_df.columns:
                        latest_value = metric_df[value_col].iloc[-1]
                        latest_date = metric_df['date'].iloc[-1]
                        
                        # Color coding based on metric type and value
                        if metric in ['hard_coral']:
                            # Higher is better
                            color = 'green' if latest_value >= 30 else 'orange' if latest_value >= 15 else 'red'
                        elif metric in ['fleshy_algae', 'bleaching', 'rubble']:
                            # Lower is better
                            color = 'red' if latest_value >= 30 else 'orange' if latest_value >= 15 else 'green'
                        else:
                            # Default neutral coloring
                            color = 'blue'
                        
                        popup_html = f"""
                        <div style="font-family: Arial, sans-serif; width: 200px;">
                            <h4 style="margin: 0; color: #2c3e50;">{site.name}</h4>
                            <p style="margin: 5px 0; color: #7f8c8d;"><b>Municipality:</b> {site.municipality}</p>
                            <p style="margin: 5px 0; color: #2c3e50;"><b>{display_name}:</b> {latest_value:.1f}</p>
                            <p style="margin: 5px 0; color: #7f8c8d;"><b>Date:</b> {latest_date.strftime('%b %Y')}</p>
                        </div>
                        """
                        
                        folium.Marker(
                            location=[site.latitude, site.longitude],
                            popup=folium.Popup(popup_html, max_width=250),
                            tooltip=f"{site.name}: {latest_value:.1f}",
                            icon=folium.Icon(color=color, icon='info-sign', prefix='glyphicon')
                        ).add_to(m)
            
            return m
            
        except Exception as e:
            logger.error(f"Error creating metric map: {str(e)}")
            return folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)