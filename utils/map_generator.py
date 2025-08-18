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
            
            # Collect data for markers
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
            
            # Second pass: create markers and radiation circles with dynamic thresholds
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
                        
                        # Determine color based on dynamic thresholds
                        if latest_biomass >= high_threshold:
                            color = 'green'
                            icon = 'leaf'
                            radiation_color = '#00ff00'  # Green
                        elif latest_biomass >= medium_threshold:
                            color = 'orange'
                            icon = 'warning-sign'
                            radiation_color = '#ffa500'  # Orange
                        else:
                            color = 'red'
                            icon = 'exclamation-sign'
                            radiation_color = '#ff0000'  # Red
                        
                        # Get site description based on current language (default to English)
                        # Since we don't have access to session state here, use English as default
                        description = site.description_en or f"Marine Protected Area in {site.municipality}"
                        
                        # Create popup content without date and with description
                        popup_html = f"""
                        <div style="font-family: Arial, sans-serif; width: 250px;">
                            <h4 style="margin: 0 0 10px 0; color: #2c3e50;">{site.name}</h4>
                            <p style="margin: 5px 0; color: #7f8c8d;"><b>Municipality:</b> {site.municipality}</p>
                            <p style="margin: 5px 0; color: #2c3e50;"><b>Latest Biomass:</b> {latest_biomass:.1f} kg/100m²</p>
                            <p style="margin: 5px 0; color: #7f8c8d;"><b>Coordinates:</b> {site.latitude:.4f}, {site.longitude:.4f}</p>
                            <div style="margin: 10px 0; padding: 8px; background: #f8f9fa; border-left: 3px solid #007acc; border-radius: 4px;">
                                <p style="margin: 0; color: #2c3e50; font-size: 13px; line-height: 1.4;"><b>About this site:</b><br>{description}</p>
                            </div>
                        </div>
                        """
                        
                        # Offset marker seaward by ~20px (approximately 0.0005 degrees longitude)
                        # This moves markers away from shoreline for better visibility
                        offset_longitude = site.longitude + 0.0005  # Move east/seaward
                        
                        # Add ocean-only radiation effect using custom GeoJSON
                        import math
                        import json
                        
                        # Calculate radiation circles with ocean masking
                        # 700m ≈ 0.0063 degrees latitude (constant)
                        lat_radius = 0.0063  # 700m in degrees latitude
                        lon_radius = 0.0063 / math.cos(math.radians(site.latitude))  # Adjust for latitude
                        
                        # Create ocean-only radiation effect using seaward-facing semicircles
                        for i, opacity in enumerate([0.3, 0.2, 0.1, 0.05]):
                            radius_multiplier = 1 - (i * 0.2)  # 100%, 80%, 60%, 40% of full radius
                            
                            # Create seaward-facing semicircle (180 degrees)
                            # Start from east (0°) and go to west (180°) - seaward arc
                            circle_points = []
                            num_points = 32  # Half circle with good resolution
                            
                            # Determine seaward direction based on site location and coastal orientation
                            # For Philippines, we can use site-specific logic based on coordinates
                            
                            # Site-specific seaward direction mapping based on actual coastal orientation
                            site_seaward_angles = {
                                # Zamboanguita sites (east coast facing east)
                                'Malatapay': (0, 180),      # East-facing
                                'Lutoban North': (0, 180),  # East-facing  
                                'Lutoban South': (0, 180),  # East-facing
                                'Lutoban Pier': (0, 180),   # East-facing
                                
                                # Siaton sites (mixed orientations)
                                'Andulay': (45, 225),       # Northeast-facing
                                'Antulang': (0, 180),       # East-facing
                                'Kookoos': (0, 180),        # East-facing
                                'Salag': (315, 135),        # Northwest-facing
                                'Basak': (0, 180),          # East-facing
                                'Dalakit': (270, 90),       # North-facing
                                'Guinsuan': (0, 180),       # East-facing
                                'Latason': (0, 180),        # East-facing
                                
                                # Santa Catalina sites (south/southwest coast)
                                'Mojon': (180, 360),        # South-facing
                                'Cawitan': (225, 45),       # Southwest-facing
                                'Manalongon': (180, 360),   # South-facing
                            }
                            
                            # Get site-specific angles or default to eastward
                            if site.name in site_seaward_angles:
                                start_angle, end_angle = site_seaward_angles[site.name]
                                # Convert to the angle system we're using (where 0° = east, 90° = north)
                                start_angle = start_angle - 90  # Adjust for our coordinate system
                                end_angle = end_angle - 90
                            else:
                                # Default to eastward semicircle
                                start_angle = -90  # Start from south
                                end_angle = 90     # End at north
                            
                            for i_angle in range(num_points + 1):
                                # Calculate angle for this point
                                angle = start_angle + (end_angle - start_angle) * (i_angle / num_points)
                                angle_rad = math.radians(angle)
                                
                                # Calculate point on semicircle
                                point_lat = site.latitude + (lat_radius * radius_multiplier * math.sin(angle_rad))
                                point_lon = offset_longitude + (lon_radius * radius_multiplier * math.cos(angle_rad))
                                
                                circle_points.append([point_lon, point_lat])  # GeoJSON uses [lon, lat]
                            
                            # Close the semicircle by connecting back to center and then to start
                            circle_points.append([offset_longitude, site.latitude])  # Center point
                            circle_points.append(circle_points[0])  # Close polygon
                            
                            # Create GeoJSON feature for seaward semicircle
                            geojson_feature = {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [circle_points]
                                },
                                "properties": {
                                    "fillColor": radiation_color,
                                    "fillOpacity": opacity,
                                    "stroke": False,
                                    "weight": 0
                                }
                            }
                            
                            # Add the seaward radiation semicircle
                            folium.GeoJson(
                                geojson_feature,
                                style_function=lambda x: {
                                    'fillColor': x['properties']['fillColor'],
                                    'fillOpacity': x['properties']['fillOpacity'],
                                    'stroke': x['properties']['stroke'],
                                    'weight': x['properties']['weight']
                                }
                            ).add_to(m)
                        
                        # Add tiny circle marker on top of radiation
                        folium.CircleMarker(
                            location=[site.latitude, offset_longitude],
                            radius=4,  # Tiny size like click markers
                            popup=folium.Popup(popup_html, max_width=250),
                            tooltip=f"{site.name}: {latest_biomass:.1f} kg/100m²",
                            color='white',
                            weight=1,
                            fillColor=color,
                            fillOpacity=0.9
                        ).add_to(m)
                        
                        marker_data.append({
                            'name': site.name,
                            'municipality': site.municipality,
                            'biomass': latest_biomass,
                            'lat': site.latitude,
                            'lon': site.longitude
                        })
            

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
            <p><i class="glyphicon glyphicon-leaf" style="color: green;"></i> High (≥{high_threshold:.1f} kg/100m²)</p>
            <p><i class="glyphicon glyphicon-warning-sign" style="color: orange;"></i> Medium ({medium_threshold:.1f}-{high_threshold:.1f} kg/100m²)</p>
            <p><i class="glyphicon glyphicon-exclamation-sign" style="color: red;"></i> Low (<{medium_threshold:.1f} kg/100m²)</p>
            <p style="font-size: 12px; color: #666; margin-top: 5px;">Range: {min_biomass:.1f}-{max_biomass:.1f} kg/100m²</p>
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