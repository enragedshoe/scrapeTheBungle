"""
Flask web application for the real estate comparison tool.
"""
from flask import Flask, render_template, request
import pandas as pd
import os
import sys
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

# Add the parent directory to sys.path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.scrape_realtor import scrape_ottawa_listings  # Original scraper (uses API)
from src.scrapers.realtor_scraper import scrape_realtor_listings  # New Selenium-based scraper
from src.scrapers.commute_time import scrape_commute_data
from src.merge_data import create_final_dataset
from src.config import GOOGLE_MAPS_API_KEY, DEFAULT_DESTINATION
# Import sample data generation
from src.sample_data import generate_sample_listings, generate_sample_commute_data

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    """
    Display the form for searching real estate listings.
    """
    return render_template("index.html")

@app.route("/results", methods=["POST"])
def show_results():
    """
    Process form data, run scrapers, and display results.
    """
    # Get form data
    max_listings = int(request.form.get("max_listings", 50))
    search_location = request.form.get("search_location", "Ottawa, ON")
    search_radius = int(request.form.get("search_radius", 10))
    price_min = request.form.get("price_min", "0")
    price_max = request.form.get("price_max", "1000000")
    bedrooms = request.form.get("bedrooms", "any")
    bathrooms = request.form.get("bathrooms", "any")
    commute_destination = request.form.get("commute_destination", DEFAULT_DESTINATION)
    commute_mode = request.form.get("commute_mode", "driving")
    
    # Log the search parameters
    logger.info(f"Search parameters: location={search_location}, radius={search_radius}km, "
                f"price={price_min}-{price_max}, bedrooms={bedrooms}, bathrooms={bathrooms}, "
                f"commute to={commute_destination}, mode={commute_mode}")
    
    # Create data directories if they don't exist
    raw_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
    processed_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    # Run scrapers
    try:
        # Always use sample data due to API limitations
        use_sample_data = True
        error_encountered = False
        
        # 1. Try to scrape real estate listings using Selenium-based scraper
        try:
            logger.info("Attempting to scrape real estate listings with Selenium...")
            # Parse the price values
            min_price_val = int(price_min) if price_min and price_min.isdigit() else None
            max_price_val = int(price_max) if price_max and price_max.isdigit() else None
            min_bedrooms_val = int(bedrooms) if bedrooms != "any" and bedrooms.isdigit() else None
            
            # Use the Selenium-based scraper
            realtor_df = scrape_realtor_listings(
                location=search_location,
                max_properties=max_listings,
                min_price=min_price_val,
                max_price=max_price_val,
                min_bedrooms=min_bedrooms_val
            )
            
            # Check if we got data back
            if realtor_df.empty:
                logger.warning("Empty DataFrame returned from Selenium scraper - switching to sample data")
                use_sample_data = True
            else:
                use_sample_data = False
                logger.info(f"Successfully scraped {len(realtor_df)} listings using Selenium")
        except Exception as e:
            logger.error(f"Error scraping real estate data with Selenium: {e}")
            error_encountered = True
            use_sample_data = True
            
        # Use sample data if we need to
        if use_sample_data:
            logger.info("Using sample data instead of real API data")
            # Generate sample listings based on form parameters
            min_price = int(price_min) if price_min and price_min.isdigit() else 0
            max_price = int(price_max) if price_max and price_max.isdigit() else 1500000
            min_bedrooms = int(bedrooms) if bedrooms.isdigit() else 1
            
            realtor_df = generate_sample_listings(count=max_listings)
            logger.info(f"Generated {len(realtor_df)} sample listings")
            
            # Apply filters to sample data
            if min_price > 0:
                realtor_df = realtor_df[realtor_df['price'] >= min_price]
            if max_price > 0:
                realtor_df = realtor_df[realtor_df['price'] <= max_price]
            if bedrooms != "any" and bedrooms.isdigit():
                realtor_df = realtor_df[realtor_df['bedrooms'] >= int(bedrooms)]
            if bathrooms != "any" and bathrooms.isdigit():
                realtor_df = realtor_df[realtor_df['bathrooms'] >= int(bathrooms)]
                
            logger.info(f"After filtering: {len(realtor_df)} sample listings")
        
        # Save data
        realtor_csv = os.path.join(raw_dir, "realtor_data.csv")
        realtor_df.to_csv(realtor_csv, index=False)
        
        # 2. Get commute times for each listing
        if realtor_df.empty:
            # Handle empty results
            return render_template(
                "results.html", 
                table_html="<p>No properties found matching your criteria.</p>",
                listing_count=0,
                max_price=price_max,
                min_bedrooms=bedrooms,
                min_bathrooms=bathrooms,
                commute_destination=commute_destination,
                commute_mode=commute_mode
            )
        
        # Get addresses
        addresses = realtor_df['address'].tolist()
        
        # Try to use real commute data if possible
        try:
            if not use_sample_data and not error_encountered:
                logger.info("Attempting to get real commute data...")
                commute_df = scrape_commute_data(addresses, commute_destination, commute_mode)
                if commute_df.empty:
                    raise Exception("Empty commute DataFrame")
            else:
                raise Exception("Using sample data for consistency")
        except Exception as e:
            logger.warning(f"Using sample commute data: {e}")
            # Use sample commute data
            commute_df = generate_sample_commute_data(addresses, commute_destination)
            logger.info(f"Generated {len(commute_df)} sample commute records")
        
        # Save commute data
        commute_csv = os.path.join(raw_dir, "commute_data.csv")
        commute_df.to_csv(commute_csv, index=False)
        
        # 3. Merge data
        output_file = os.path.join(processed_dir, "search_results.csv")
        final_df = create_final_dataset(
            realtor_csv,
            commute_csv,
            output_file=output_file
        )
        
        # 4. Prepare data for display
        # First check what columns we actually have
        available_columns = final_df.columns.tolist()
        logger.info(f"Available columns in final data: {available_columns}")
        
        # Define the desired columns
        desired_columns = [
            'address', 'price', 'bedrooms', 'bathrooms', 'year_built', 
            'square_feet', 'property_tax', 'neighborhood',
            'commute_time_text', 'distance_text'
        ]
        
        # Only use columns that actually exist in the DataFrame
        display_columns = [col for col in desired_columns if col in available_columns]
        
        if not display_columns:
            logger.warning("No display columns available in data")
            # Create a basic result with a message
            return render_template(
                "results.html", 
                table_html="<p>No property data available. This could be due to scraping restrictions.</p>",
                listing_count=0,
                max_price=price_max,
                min_bedrooms=bedrooms,
                min_bathrooms=bathrooms,
                commute_destination=commute_destination,
                commute_mode=commute_mode
            )
            
        display_df = final_df[display_columns].copy()
        
        # Format the data for display
        column_rename = {
            'address': 'Address',
            'price': 'Price',
            'year_built': 'Year Built',
            'square_feet': 'Square Feet',
            'property_tax': 'Property Tax',
            'commute_time_text': 'Commute Time',
            'distance_text': 'Distance',
            'bedrooms': 'Bedrooms',
            'bathrooms': 'Bathrooms',
            'neighborhood': 'Neighborhood'
        }
        
        # Only rename columns that exist
        rename_dict = {k: v for k, v in column_rename.items() if k in display_df.columns}
        display_df = display_df.rename(columns=rename_dict)
        
        # Format price values with dollar sign and commas
        if 'Price' in display_df.columns:
            display_df['Price'] = display_df['Price'].apply(lambda x: f"${x:,}" if pd.notnull(x) else "N/A")
            
        # Format property tax with dollar sign and commas
        if 'Property Tax' in display_df.columns:
            display_df['Property Tax'] = display_df['Property Tax'].apply(lambda x: f"${x:,}" if pd.notnull(x) else "N/A")
        
        # Create HTML table
        table_html = display_df.to_html(
            index=False, 
            border=1,
            classes="table table-striped table-hover",
            escape=False
        )
        
        # Render template with data
        return render_template(
            "results.html", 
            table_html=table_html,
            listing_count=len(display_df),
            max_price=price_max,
            min_bedrooms=bedrooms,
            min_bathrooms=bathrooms,
            commute_destination=commute_destination,
            commute_mode=commute_mode
        )
        
    except Exception as e:
        # Handle errors
        error_message = f"<p>Error processing your request: {str(e)}</p>"
        return render_template(
            "results.html", 
            table_html=error_message,
            listing_count=0
        )

if __name__ == "__main__":
    # Run Flask in debug mode for local development
    port = 8080  # Using port 8080 instead of 5000
    print(f"\n{'='*80}")
    print(f"STARTING WEB SERVER ON PORT {port}")
    print(f"Open your browser to: http://localhost:{port}")
    print(f"{'='*80}\n")
    print("Note: You need to enable 'Places API' and 'Maps JavaScript API' in Google Cloud Console")
    print("      for the autocomplete to work. Currently only Distance Matrix API is enabled.\n")
    
    # Enable detailed logging - this will show all requests in the terminal
    import logging
    from logging import StreamHandler
    
    # Log Flask messages
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.INFO)
    log.addHandler(StreamHandler())
    
    # Also log all requests to the server
    @app.before_request
    def log_request_info():
        logger.info(f"Request: {request.method} {request.path} {request.form.to_dict() if request.form else ''}")
    
    @app.after_request
    def log_response_info(response):
        logger.info(f"Response: {response.status_code}")
        return response
    
    app.run(debug=True, host="0.0.0.0", port=port)