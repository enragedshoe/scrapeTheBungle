"""
Module for merging data from different sources (real estate, crime, commute).
"""
import pandas as pd
import os
from src.config import OUTPUT_DIRECTORY, DEFAULT_OUTPUT_FILENAME

def load_dataframes(real_estate_file, commute_time_file, crime_data_file=None):
    """
    Load data from CSV files into pandas DataFrames.
    
    Args:
        real_estate_file (str): Path to real estate data CSV
        commute_time_file (str): Path to commute time data CSV
        crime_data_file (str): Path to crime data CSV (optional)
        
    Returns:
        tuple: Tuple of pandas DataFrames (real_estate_df, commute_df, crime_df)
    """
    # Handle empty files or files with errors
    try:
        real_estate_df = pd.read_csv(real_estate_file)
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        print(f"Warning: Real estate file {real_estate_file} is empty or invalid. Creating empty DataFrame.")
        real_estate_df = pd.DataFrame(columns=['address', 'price', 'year_built', 'square_feet', 'property_tax'])
    
    try:
        commute_df = pd.read_csv(commute_time_file)
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        print(f"Warning: Commute file {commute_time_file} is empty or invalid. Creating empty DataFrame.")
        commute_df = pd.DataFrame(columns=['address', 'commute_time_text', 'commute_time_seconds', 
                                            'distance_text', 'distance_value', 'mode'])
    
    crime_df = None
    if crime_data_file and os.path.exists(crime_data_file):
        try:
            crime_df = pd.read_csv(crime_data_file)
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            print(f"Warning: Crime data file {crime_data_file} is empty or invalid. Creating empty DataFrame.")
            crime_df = pd.DataFrame()
    
    return real_estate_df, commute_df, crime_df

def merge_real_estate_and_commute(real_estate_df, commute_df):
    """
    Merge real estate and commute data based on address.
    
    Args:
        real_estate_df (DataFrame): Real estate listings data
        commute_df (DataFrame): Commute times data
        
    Returns:
        DataFrame: Merged data
    """
    # Clean and standardize address fields for matching
    real_estate_df['address_clean'] = real_estate_df['address'].str.lower().str.strip()
    commute_df['address_clean'] = commute_df['address'].str.lower().str.strip()
    
    # Merge dataframes on cleaned address
    merged_df = pd.merge(
        real_estate_df, 
        commute_df, 
        left_on='address_clean', 
        right_on='address_clean', 
        how='left',
        suffixes=('', '_commute')
    )
    
    # Drop duplicate address columns and temporary columns
    if 'address_commute' in merged_df.columns:
        merged_df = merged_df.drop(columns=['address_commute'])
    merged_df = merged_df.drop(columns=['address_clean'])
    
    return merged_df

def add_crime_data(merged_df, crime_df):
    """
    Add crime data to the merged dataframe.
    
    Args:
        merged_df (DataFrame): Merged real estate and commute data
        crime_df (DataFrame): Crime data with location information
        
    Returns:
        DataFrame: Final merged dataframe with crime data
    """
    if crime_df is None:
        return merged_df
    
    # This would need to be implemented based on the actual crime data structure
    # For now, we'll just return the merged_df
    return merged_df

def create_final_dataset(real_estate_file, commute_time_file, crime_data_file=None, output_file=None):
    """
    Create the final merged dataset from all sources.
    
    Args:
        real_estate_file (str): Path to real estate data CSV
        commute_time_file (str): Path to commute time data CSV
        crime_data_file (str): Path to crime data CSV (optional)
        output_file (str): Output file path (optional)
        
    Returns:
        DataFrame: Final merged dataframe
    """
    # Load data
    real_estate_df, commute_df, crime_df = load_dataframes(
        real_estate_file, 
        commute_time_file, 
        crime_data_file
    )
    
    # Merge real estate and commute data
    merged_df = merge_real_estate_and_commute(real_estate_df, commute_df)
    
    # Add crime data if available
    final_df = add_crime_data(merged_df, crime_df)
    
    # Save to file if output_file specified
    if output_file:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        final_df.to_csv(output_file, index=False)
        print(f"Final dataset saved to {output_file}")
    
    return final_df

if __name__ == "__main__":
    # Example usage
    output_path = os.path.join(OUTPUT_DIRECTORY, DEFAULT_OUTPUT_FILENAME)
    
    # Sample input files - update these paths
    real_estate_file = "data/raw/ottawa_listings.csv"
    commute_time_file = "data/raw/commute_times.csv"
    
    final_df = create_final_dataset(
        real_estate_file,
        commute_time_file,
        output_file=output_path
    )
    
    print(f"Final dataset shape: {final_df.shape}")
    print(final_df.head())