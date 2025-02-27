# File: real_estate_api.py

import requests
import time

# Optionally, if using an API with a key (like MappedBy or Houski), configure it here:
# API_KEY = "YOUR_API_KEY"

# Helper: define the search parameters for Ottawa region on Realtor.ca
# We use a bounding box covering Ottawa and surrounding area.
OTTAWA_BBOX_PARAMS = {
    "CultureId": 1,               # English
    "ApplicationId": 1,           # Public website
    "PropertySearchTypeId": 1,    # Residential properties
    "LatitudeMin": 45.0,          # approx south of Ottawa
    "LatitudeMax": 45.6,          # approx north of Ottawa
    "LongitudeMin": -76.5,        # approx west of Ottawa
    "LongitudeMax": -75.0,        # approx east of Ottawa
    "PriceMin": 0, "PriceMax": 0, # 0 means no min/max filter on price
    "RecordsPerPage": 50,         # max results per page (50 is allowed)
    "CurrentPage": 1,             # will iterate through pages
    "ViewType": "List",           # list view data
    "Sort": "6-D",                # optional: sort by Latest Listings
}

def fetch_listings_ottawa():
    """
    Fetches real estate listings for Ottawa and returns a list of properties 
    with basic info (price, MLS ID, etc.).
    """
    listings = []
    page = 1
    while True:
        # Update page number in params
        params = OTTAWA_BBOX_PARAMS.copy()
        params["CurrentPage"] = page
        # Realtor.ca API endpoint for property search
        url = "https://api2.realtor.ca/Listing.svc/PropertySearch_Post"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json",
            "Origin": "https://www.realtor.ca",
            "Referer": "https://www.realtor.ca/",
            "User-Agent": "Mozilla/5.0"  # set a user-agent to mimic a browser
        }
        response = requests.post(url, data=params, headers=headers)
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} on page {page}")
            break
        data = response.json()
        results = data.get("Results", [])
        if not results:
            # No more results (we’ve reached the end of listings)
            break
        listings.extend(results)
        # Stop if we hit the last page to avoid infinite loop
        total_matches = data.get("Paging", {}).get("TotalRecords", 0)
        if page * params["RecordsPerPage"] >= total_matches:
            break
        page += 1
        # Sleep to respect rate limits (avoid hitting the 50 calls/hour limit)
        time.sleep(1)  # adjust delay as needed
    return listings

def fetch_listing_details(mls_number, property_id):
    """
    Fetches detailed information for a single property listing given its MLS number and property ID.
    Returns a dictionary with additional fields like year built and property taxes.
    """
    url = "https://api2.realtor.ca/Listing.svc/PropertyDetails"
    params = {
        "CultureId": 1,
        "ApplicationId": 1,
        "ReferenceNumber": mls_number,  # MLS number
        "PropertyID": property_id      # internal property ID
    }
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    resp = requests.get(url, params=params, headers=headers)
    if resp.status_code != 200:
        return None
    return resp.json()

def get_ottawa_listings_with_details(max_properties=None):
    """
    Retrieves all Ottawa listings (or up to max_properties if specified), and returns a list of 
    dictionaries with key details: price, address, bedrooms, year_built, square_feet, property_taxes.
    """
    all_listings = fetch_listings_ottawa()
    detailed_listings = []
    count = 0
    for listing in all_listings:
        if max_properties and count >= max_properties:
            break
        prop = listing.get("Property", {})
        price = prop.get("Price")  # listing price
        address = prop.get("Address", {}).get("AddressText")
        mls_number = prop.get("MlsNumber")
        property_id = listing.get("Id")  # property ID for detail API
        # Basic fields from summary
        entry = {
            "price": price,
            "address": address,
            "mls_number": mls_number,
            "bedrooms": prop.get("Bedrooms"),
            "bathrooms": prop.get("BathroomTotal")
        }
        # Fetch detail for additional fields
        details = fetch_listing_details(mls_number, property_id)
        if details:
            property_details = details.get("PropertyDetails", {})
            # Year built (if available)
            entry["year_built"] = property_details.get("Building", {}).get("YearBuilt")
            # Floor area or square footage (if available)
            entry["square_feet"] = property_details.get("Building", {}).get("SizeInterior")  # e.g., "1500 sqft"
            # Property taxes (if available)
            taxes_info = property_details.get("Taxes", {})
            entry["property_tax"] = taxes_info.get("Annual") or taxes_info.get("Amount")
        else:
            entry["year_built"] = None
            entry["square_feet"] = None
            entry["property_tax"] = None
        detailed_listings.append(entry)
        count += 1
    return detailed_listings

# --- If using MappedBy or Houski instead of Realtor.ca, you could do something like: ---
# def fetch_property_by_address(address: str):
#     url = f"https://api.houski.ca/properties?api_key={API_KEY}&address={address}&city=ottawa&province_abbreviation=on&country_abbreviation=ca"
#     url += "&select=construction_year,interior_sq_m,property_taxes"
#     resp = requests.get(url)
#     return resp.json()
#
# The above would retrieve year built (construction_year), interior area (sq m), and property taxes for a given address via Houski API.
# Similar can be done for MappedBy if API key/token is provided.
