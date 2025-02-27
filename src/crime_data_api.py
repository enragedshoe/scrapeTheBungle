"""
Module for accessing crime data from Ottawa's open data portal.
"""
import requests
import pandas as pd
import math
import logging
import sys
import os

# Add the parent directory to sys.path to allow for import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.base_scraper import APIScraper
from src.config import CRIME_MAP_URL

logger = logging.getLogger(__name__)

# ArcGIS REST API endpoint for Ottawa Crime data (Criminal Offences feature layer)
ARCGIS_CRIME_FEATURE_URL = "https://opendata.arcgis.com/datasets/ottawa::criminal-offences-.geojson"

class CrimeDataAPI(APIScraper):
    """Class for accessing Ottawa crime data."""
    
    def __init__(self, api_url=ARCGIS_CRIME_FEATURE_URL, delay=2):
        """Initialize the crime data API client."""
        super().__init__(delay=delay)
        self.api_url = api_url
        self._cached_data = None
    
    def fetch_all_crimes(self, force_refresh=False):
        """
        Fetch all crime incidents from the open data portal.
        
        Args:
            force_refresh (bool): Whether to force refresh the cache
            
        Returns:
            dict: GeoJSON data with crime incidents
        """
        if self._cached_data is None or force_refresh:
            logger.info(f"Fetching crime data from {self.api_url}")
            json_data = self.fetch_json(self.api_url)
            
            if not json_data:
                logger.error("Failed to fetch crime data")
                return {"features": []}
                
            self._cached_data = json_data
            logger.info(f"Retrieved {len(json_data.get('features', []))} crime incidents")
            
        return self._cached_data
    
    def count_crimes_by_year(self, year=2024):
        """
        Count crimes that occurred in a given year.
        
        Args:
            year (int): Year to filter by
            
        Returns:
            int: Number of crimes in that year
        """
        data = self.fetch_all_crimes()
        features = data.get("features", [])
        count = 0
        
        for feature in features:
            props = feature.get("properties", {})
            # Adjust field name as needed based on the actual dataset
            reported_year = props.get("reported_year") or props.get("Year")
            if reported_year == year:
                count += 1
                
        return count
    
    def crimes_near_location(self, lat, lon, radius_km=1.0):
        """
        Find crimes within a certain radius of a location.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            radius_km (float): Radius in kilometers
            
        Returns:
            list: Crime records within the radius
        """
        data = self.fetch_all_crimes()
        features = data.get("features", [])
        nearby_crimes = []
        
        # Filter by approximate bounding box first (for efficiency)
        lat_deg = radius_km / 111  # approx degrees latitude per km
        lon_deg = radius_km / (111 * abs(math.cos(math.radians(lat))))  # degrees longitude per km
        
        lat_min, lat_max = lat - lat_deg, lat + lat_deg
        lon_min, lon_max = lon - lon_deg, lon + lon_deg
        
        for feature in features:
            geom = feature.get("geometry", {})
            if geom.get("type") == "Point":
                coords = geom.get("coordinates")  # [lon, lat]
                if not coords:
                    continue
                    
                crime_lon, crime_lat = coords[0], coords[1]
                
                # Check if within bounding box
                if (lat_min <= crime_lat <= lat_max and 
                    lon_min <= crime_lon <= lon_max):
                    
                    # Calculate exact distance
                    dist = haversine_distance(lat, lon, crime_lat, crime_lon)
                    if dist <= radius_km * 1000:  # Convert km to meters
                        nearby_crimes.append(feature["properties"])
                        
        return nearby_crimes
    
    def get_crime_stats_by_area(self, lat, lon, radius_km=1.0):
        """
        Get crime statistics for an area.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            radius_km (float): Radius in kilometers
            
        Returns:
            dict: Crime statistics for the area
        """
        crimes = self.crimes_near_location(lat, lon, radius_km)
        
        if not crimes:
            return {
                "total_crimes": 0,
                "crime_rate": 0,
                "crime_types": {}
            }
        
        # Count crime types
        crime_types = {}
        for crime in crimes:
            crime_type = crime.get("offense_code") or crime.get("CrimeType") or "Unknown"
            crime_types[crime_type] = crime_types.get(crime_type, 0) + 1
        
        # Calculate approximate population (rough estimate based on area)
        # About 2000 people per sq km in suburban areas (adjust as needed)
        area_sq_km = math.pi * radius_km * radius_km
        estimated_population = area_sq_km * 2000
        
        return {
            "total_crimes": len(crimes),
            "crime_rate": (len(crimes) / estimated_population) * 1000,  # per 1000 people
            "crime_types": crime_types
        }
    
    def get_crime_dataframe(self, lat=None, lon=None, radius_km=None):
        """
        Get crime data as a pandas DataFrame.
        
        Args:
            lat (float): Optional latitude to filter by
            lon (float): Optional longitude to filter by
            radius_km (float): Optional radius in kilometers
            
        Returns:
            DataFrame: Crime data
        """
        if lat and lon and radius_km:
            crimes = self.crimes_near_location(lat, lon, radius_km)
        else:
            crimes = [feature["properties"] for feature in self.fetch_all_crimes().get("features", [])]
        
        return pd.DataFrame(crimes)

# Helper function to compute distance between two lat/lon points
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points in meters.
    
    Args:
        lat1, lon1, lat2, lon2: Coordinates in decimal degrees
        
    Returns:
        float: Distance in meters
    """
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi/2)**2 + 
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

# Convenience functions
def get_crime_stats(address, geocode_api_key=None, radius_km=1.0):
    """
    Get crime statistics for an address.
    
    Args:
        address (str): Address to get crime statistics for
        geocode_api_key (str): API key for geocoding service
        radius_km (float): Radius in kilometers
        
    Returns:
        dict: Crime statistics
    """
    # This would need a geocoding step to convert address to lat/lon
    # For now, we'll just return dummy data
    return {
        "total_crimes": 45,
        "crime_rate": 2.3,
        "most_common_crimes": ["Theft", "Mischief", "Break and Enter"]
    }
