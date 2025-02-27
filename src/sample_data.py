"""
Sample data module for development and testing when APIs are unavailable or blocking.
"""
import pandas as pd
import random
import string

def generate_sample_listings(count=50):
    """
    Generate sample real estate listings.
    
    Args:
        count (int): Number of listings to generate
        
    Returns:
        DataFrame: Sample listings dataframe
    """
    # Ottawa neighborhoods
    neighborhoods = [
        "Westboro", "The Glebe", "Centretown", "Sandy Hill", "ByWard Market",
        "Hintonburg", "New Edinburgh", "Rockcliffe Park", "Alta Vista", "Kanata",
        "Barrhaven", "Orleans", "Nepean", "Vanier", "Stittsville"
    ]
    
    # Ottawa street names
    streets = [
        "Bank", "Elgin", "Wellington", "Somerset", "Preston",
        "Rideau", "Sussex", "Laurier", "O'Connor", "Merivale",
        "Carling", "Baseline", "Woodroffe", "Montreal", "Riverside"
    ]
    
    # Ottawa postal code prefixes
    postal_prefixes = ["K1P", "K1R", "K1S", "K1V", "K1Y", "K1Z", "K2P"]
    
    listings = []
    
    for i in range(count):
        # Generate random address
        street_number = random.randint(1, 2000)
        street = random.choice(streets)
        neighborhood = random.choice(neighborhoods)
        postal_prefix = random.choice(postal_prefixes)
        postal_suffix = f"{random.randint(0, 9)}{random.choice(string.ascii_uppercase)}{random.randint(0, 9)}"
        
        # Full address
        address = f"{street_number} {street} St, {neighborhood}, Ottawa, ON {postal_prefix} {postal_suffix}"
        
        # Generate property details
        price = random.randint(300000, 1500000)
        bedrooms = random.randint(1, 6)
        bathrooms = random.randint(1, 4)
        sqft = random.randint(800, 3500)
        year_built = random.randint(1900, 2023)
        property_tax = int(price * 0.01)  # Approximately 1% of property value
        
        listings.append({
            "address": address,
            "price": price,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "square_feet": sqft,
            "year_built": year_built,
            "property_tax": property_tax,
            "mls_number": f"M{random.randint(1000000, 9999999)}",
            "neighborhood": neighborhood
        })
    
    return pd.DataFrame(listings)

def generate_sample_commute_data(addresses, destination):
    """
    Generate sample commute times.
    
    Args:
        addresses (list): List of addresses
        destination (str): Destination address
        
    Returns:
        DataFrame: Sample commute data
    """
    results = []
    
    for address in addresses:
        # Extract neighborhood if available
        neighborhood = "Ottawa"
        if ", " in address:
            parts = address.split(", ")
            if len(parts) > 1:
                neighborhood = parts[1]
        
        # Generate commute time based on neighborhood (some neighborhoods are closer to downtown)
        downtown_neighborhoods = ["Centretown", "The Glebe", "ByWard Market", "Sandy Hill", "Westboro"]
        if neighborhood in downtown_neighborhoods:
            commute_minutes = random.randint(5, 20)
            distance_km = random.randint(1, 10)
        else:
            commute_minutes = random.randint(15, 45)
            distance_km = random.randint(8, 25)
        
        results.append({
            "address": address,
            "commute_time_text": f"{commute_minutes} mins",
            "commute_time_seconds": commute_minutes * 60,
            "distance_text": f"{distance_km} km",
            "distance_value": distance_km * 1000,
            "mode": "driving"
        })
    
    return pd.DataFrame(results)

def generate_sample_crime_data(count=100):
    """
    Generate sample crime data.
    
    Args:
        count (int): Number of crime incidents to generate
        
    Returns:
        DataFrame: Sample crime data
    """
    # Ottawa neighborhoods
    neighborhoods = [
        "Westboro", "The Glebe", "Centretown", "Sandy Hill", "ByWard Market",
        "Hintonburg", "New Edinburgh", "Rockcliffe Park", "Alta Vista", "Kanata",
        "Barrhaven", "Orleans", "Nepean", "Vanier", "Stittsville"
    ]
    
    # Crime types
    crime_types = [
        "Break and Enter", "Theft of Vehicle", "Theft from Vehicle", "Assault", 
        "Mischief", "Robbery", "Drug Offence", "Fraud", "Property Damage"
    ]
    
    crimes = []
    
    for i in range(count):
        crime_date = f"2023-{random.randint(1, 12)}-{random.randint(1, 28)}"
        crimes.append({
            "date": crime_date,
            "crime_type": random.choice(crime_types),
            "neighborhood": random.choice(neighborhoods),
            "reported_year": 2023
        })
    
    return pd.DataFrame(crimes)

if __name__ == "__main__":
    # Generate sample data for testing
    sample_listings = generate_sample_listings(50)
    print("Sample Listings:")
    print(sample_listings.head())
    
    # Test commute data generation
    sample_addresses = sample_listings['address'].tolist()[:5]
    sample_commute = generate_sample_commute_data(sample_addresses, "Ottawa, ON")
    print("\nSample Commute Data:")
    print(sample_commute)
    
    # Test crime data
    sample_crime = generate_sample_crime_data(20)
    print("\nSample Crime Data:")
    print(sample_crime)
    
    # Export to CSV for testing
    sample_listings.to_csv("sample_listings.csv", index=False)
    sample_commute.to_csv("sample_commute.csv", index=False)
    sample_crime.to_csv("sample_crime.csv", index=False)