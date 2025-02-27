"""
Main module for the real estate comparison tool.
"""
import os
import sys
import argparse
import pandas as pd
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to allow for import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.scrape_realtor import scrape_ottawa_listings
from src.crime_data_api import get_crime_stats  # Changed from crimes_near_location
from src.scrapers.commute_time import scrape_commute_data
from src.merge_data import create_final_dataset
from src.config import GOOGLE_MAPS_API_KEY, DEFAULT_DESTINATION, OUTPUT_DIRECTORY, DEFAULT_OUTPUT_FILENAME

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Real Estate Comparison Tool")
    parser.add_argument("--max-listings", type=int, default=50, 
                      help="Maximum number of listings to scrape")
    parser.add_argument("--destination", type=str, default=DEFAULT_DESTINATION,
                      help="Destination address for commute calculations")
    parser.add_argument("--output", type=str, 
                      help="Output file path (default: data/processed/real_estate_data.csv)")
    return parser.parse_args()

def main():
    """Main function to run the complete workflow."""
    args = parse_args()
    
    print("Starting real estate comparison tool...")
    
    # Create data directories if they don't exist
    raw_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    processed_dir = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    # 1. Scrape real estate listings
    print("\n1. Scraping real estate listings...")
    realtor_df = scrape_ottawa_listings(max_properties=args.max_listings)
    realtor_csv = os.path.join(raw_dir, "realtor_data.csv")
    realtor_df.to_csv(realtor_csv, index=False)
    print(f"  ✓ Scraped {len(realtor_df)} listings")
    
    # 2. Calculate commute times for each address
    print("\n2. Calculating commute times...")
    
    # Check if realtor_df is empty or missing the address column
    if realtor_df.empty:
        logger.warning("No real estate listings found. Using sample addresses for commute calculation.")
        # Use sample addresses instead
        addresses = [
            "150 Elgin St, Ottawa, ON",
            "1385 Bank St, Ottawa, ON",
            "100 Bayshore Dr, Ottawa, ON"
        ]
    else:
        # Make sure the column exists
        if 'address' not in realtor_df.columns:
            col_names = list(realtor_df.columns)
            logger.warning(f"'address' column not found in realtor data. Available columns: {col_names}")
            # If there's no 'address' column but we have data, try to find a similar column
            address_like_cols = [col for col in col_names if 'addr' in col.lower()]
            if address_like_cols:
                # Use the first column that looks like an address column
                address_col = address_like_cols[0]
                logger.info(f"Using '{address_col}' instead of 'address'")
                addresses = realtor_df[address_col].tolist()
            else:
                # Fall back to sample addresses
                addresses = [
                    "150 Elgin St, Ottawa, ON",
                    "1385 Bank St, Ottawa, ON",
                    "100 Bayshore Dr, Ottawa, ON"
                ]
        else:
            addresses = realtor_df['address'].tolist()
    
    commute_df = scrape_commute_data(addresses, args.destination)
    commute_csv = os.path.join(raw_dir, "commute_data.csv")
    commute_df.to_csv(commute_csv, index=False)
    print(f"  ✓ Calculated commute times for {len(commute_df)} addresses")
    
    # 3. Merge data
    print("\n3. Merging data...")
    output_file = args.output or os.path.join(processed_dir, DEFAULT_OUTPUT_FILENAME)
    final_df = create_final_dataset(
        realtor_csv,
        commute_csv,
        output_file=output_file
    )
    print(f"  ✓ Created final dataset with {len(final_df)} properties")
    
    print(f"\nProcess complete! Final data saved to: {output_file}")
    print("\nSample of the data:")
    print(final_df.head())

if __name__ == "__main__":
    main()