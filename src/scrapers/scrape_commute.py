"""
Module for scraping commute times using Google Maps Distance Matrix API.
"""
import requests
import pandas as pd
import time
import logging
from src.config import GOOGLE_MAPS_API_KEY, SCRAPE_DELAY, DEFAULT_DESTINATION
from src.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class CommuteTimeScraper(BaseScraper):
    """Scraper for Google Maps Distance Matrix API."""
    
    def __init__(self, api_key=GOOGLE_MAPS_API_KEY, delay=SCRAPE_DELAY):
        """Initialize the commute time scraper."""
        super().__init__(delay=delay)
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        
    def get_commute_time(self, origin, destination=DEFAULT_DESTINATION, mode="driving"):
        """
        Get commute time between two locations.
        
        Args:
            origin (str): Origin address
            destination (str): Destination address
            mode (str): Travel mode (driving, walking, bicycling, transit)
            
        Returns:
            dict: Dictionary with commute information
        """
        params = {
            "origins": origin,
            "destinations": destination,
            "mode": mode,
            "key": self.api_key
        }
        
        json_data = self.fetch_json(self.base_url, params=params)
        
        if not json_data or json_data.get("status") != "OK":
            logger.error(f"Error from Google Maps API: {json_data.get('status') if json_data else 'No data'}")
            return {"text": "N/A", "value": None}
            
        try:
            element = json_data["rows"][0]["elements"][0]
            if element["status"] != "OK":
                logger.error(f"Error for route: {element['status']}")
                return {"text": "N/A", "value": None}
                
            return {
                "text": element["duration"]["text"],
                "value": element["duration"]["value"],  # in seconds
                "distance_text": element["distance"]["text"],
                "distance_value": element["distance"]["value"]  # in meters
            }
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing Google Maps API response: {e}")
            return {"text": "N/A", "value": None}
    
    def scrape_commute_times(self, addresses, destination=DEFAULT_DESTINATION, mode="driving"):
        """
        Scrape commute times for multiple addresses.
        
        Args:
            addresses (list): List of origin addresses
            destination (str): Destination address
            mode (str): Travel mode
            
        Returns:
            DataFrame: DataFrame with commute information
        """
        results = []
        for addr in addresses:
            logger.info(f"Getting commute time from {addr} to {destination}")
            commute = self.get_commute_time(addr, destination, mode)
            
            results.append({
                "address": addr,
                "commute_time_text": commute["text"],
                "commute_time_seconds": commute["value"],
                "distance_text": commute.get("distance_text", "N/A"),
                "distance_value": commute.get("distance_value", None),
                "mode": mode
            })
        
        return pd.DataFrame(results)

def scrape_commute_data(addresses, destination=DEFAULT_DESTINATION, mode="driving", api_key=GOOGLE_MAPS_API_KEY):
    """
    Convenience function to scrape commute times.
    
    Args:
        addresses (list): List of addresses to calculate commute from
        destination (str): Destination address
        mode (str): Travel mode
        api_key (str): Google Maps API key
        
    Returns:
        DataFrame: DataFrame with commute information
    """
    scraper = CommuteTimeScraper(api_key=api_key)
    return scraper.scrape_commute_times(addresses, destination, mode)
