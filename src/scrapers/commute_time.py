"""
Module for calculating commute times using Google Maps Distance Matrix API.
"""
import requests
import pandas as pd
import time
import sys
import os

# Add the parent directory to sys.path to allow for import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import GOOGLE_MAPS_API_KEY, SCRAPE_DELAY, DEFAULT_DESTINATION

def get_commute_time(origin, destination=DEFAULT_DESTINATION, mode="driving", api_key=GOOGLE_MAPS_API_KEY):
    """
    Get the commute time between two locations using Google Maps API.
    
    Args:
        origin (str): Starting address or coordinates
        destination (str): Ending address or coordinates (defaults to config setting)
        mode (str): Travel mode ('driving', 'walking', 'transit', 'bicycling')
        api_key (str): Google Maps API key
        
    Returns:
        dict: Dictionary containing commute information
    """
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destination,
        "mode": mode,
        "key": api_key
    }
    try:
        resp = requests.get(base_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Check for valid response
        if data["status"] != "OK":
            print(f"Error from Google Maps API: {data['status']}")
            return {"text": "N/A", "value": None}

        # Parse out the commute time
        element = data["rows"][0]["elements"][0]
        if element["status"] != "OK":
            print(f"Error for route: {element['status']}")
            return {"text": "N/A", "value": None}
            
        return {
            "text": element["duration"]["text"],
            "value": element["duration"]["value"],  # in seconds
            "distance_text": element["distance"]["text"],
            "distance_value": element["distance"]["value"]  # in meters
        }
    except Exception as e:
        print(f"Error fetching commute time: {e}")
        return {"text": "N/A", "value": None}

def scrape_commute_data(addresses, workplace=DEFAULT_DESTINATION, mode="driving"):
    """
    Returns a DataFrame of addresses and commute times to a single workplace.
    
    Args:
        addresses (list): List of addresses to calculate commute from
        workplace (str): Destination address (defaults to config setting)
        mode (str): Travel mode (driving, walking, transit, bicycling)
        
    Returns:
        pandas.DataFrame: DataFrame with commute information
    """
    results = []
    for addr in addresses:
        commute = get_commute_time(addr, workplace, mode)
        
        # Add to results
        results.append({
            "address": addr,
            "commute_time_text": commute["text"],
            "commute_time_seconds": commute["value"],
            "distance_text": commute.get("distance_text", "N/A"),
            "distance_value": commute.get("distance_value", None),
            "mode": mode
        })
        
        # Sleep to avoid hitting rate limits
        time.sleep(SCRAPE_DELAY)

    return pd.DataFrame(results)

if __name__ == "__main__":
    # Test with sample addresses
    test_addresses = [
        "150 Elgin St, Ottawa, ON",
        "1385 Bank St, Ottawa, ON",
        "100 Bayshore Dr, Ottawa, ON"
    ]
    
    result_df = scrape_commute_data(test_addresses)
    print(result_df)
    result_df.to_csv("commute_times.csv", index=False)