import requests
import time
import pandas as pd

# (Optional) bounding box coords for Ottawa area:
OTTAWA_BBOX_PARAMS = {
    "CultureId": 1,               # English
    "ApplicationId": 1,           # Public website
    "PropertySearchTypeId": 1,    # 1 = Residential
    "LatitudeMin": 45.0,
    "LatitudeMax": 45.6,
    "LongitudeMin": -76.5,
    "LongitudeMax": -75.0,
    "PriceMin": 0,
    "PriceMax": 0,
    "RecordsPerPage": 50,
    "CurrentPage": 1,
    "ViewType": "List",
    "Sort": "6-D",                # Sort by date, etc.
}

def fetch_listings_ottawa():
    """
    Fetch active listings from Realtor.ca for the Ottawa area, 
    using the 'PropertySearch_Post' endpoint.
    """
    listings = []
    page = 1
    while True:
        params = OTTAWA_BBOX_PARAMS.copy()
        params["CurrentPage"] = page
        url = "https://api2.realtor.ca/Listing.svc/PropertySearch_Post"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json",
            "Origin": "https://www.realtor.ca",
            "Referer": "https://www.realtor.ca",
            "User-Agent": "Mozilla/5.0",
        }

        response = requests.post(url, data=params, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Error: status {response.status_code} on page {page}")
            break

        data = response.json()
        results = data.get("Results", [])
        if not results:
            # No more results
            break

        listings.extend(results)
        total_records = data.get("Paging", {}).get("TotalRecords", 0)
        if page * params["RecordsPerPage"] >= total_records:
            # We've gotten all
            break

        page += 1
        # Sleep to avoid hitting rate limits 
        time.sleep(1)

    return listings


def fetch_listing_details(mls_number, property_id):
    """
    Fetch additional details (year built, taxes, etc.) for a single listing.
    """
    url = "https://api2.realtor.ca/Listing.svc/PropertyDetails"
    params = {
        "CultureId": 1,
        "ApplicationId": 1,
        "ReferenceNumber": mls_number,
        "PropertyID": property_id
    }
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    if resp.status_code != 200:
        print(f"Error fetching details for MLS {mls_number}: {resp.status_code}")
        return None
    return resp.json()


def scrape_ottawa_listings(max_properties=None):
    """
    High-level function to scrape up to 'max_properties' listings 
    and get data like price, year built, taxes, etc.
    Returns a pandas DataFrame.
    """
    raw_listings = fetch_listings_ottawa()
    data_rows = []
    count = 0

    for listing in raw_listings:
        if max_properties and count >= max_properties:
            break

        prop = listing.get("Property", {})
        address = prop.get("Address", {}).get("AddressText", "N/A")
        price = prop.get("Price")
        mls_num = prop.get("MlsNumber")
        property_id = listing.get("Id")

        row = {
            "address": address,
            "price": price,
            "mls_number": mls_num
        }

        detail_json = fetch_listing_details(mls_num, property_id)
        if detail_json:
            details = detail_json.get("PropertyDetails", {})
            building_info = details.get("Building", {})
            taxes_info = details.get("Taxes", {})

            row["year_built"] = building_info.get("YearBuilt")
            row["property_tax"] = taxes_info.get("Annual") or taxes_info.get("Amount")
            row["square_feet"] = building_info.get("SizeInterior")  # e.g. "1500 sqft"
        else:
            row["year_built"] = None
            row["property_tax"] = None
            row["square_feet"] = None

        data_rows.append(row)
        count += 1

    df = pd.DataFrame(data_rows)
    return df


if __name__ == "__main__":
    df_ottawa = scrape_ottawa_listings(max_properties=50)
    print(df_ottawa.head())
    # Save to CSV, etc.
    df_ottawa.to_csv("ottawa_listings.csv", index=False)
