"""
A more robust scraper for Realtor.ca that uses Selenium to bypass anti-scraping measures.
"""
import time
import random
import pandas as pd
import logging
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
# Add WebDriver Manager to auto-download the correct ChromeDriver
from webdriver_manager.chrome import ChromeDriverManager
# Add fake_useragent to generate random user agents
try:
    from fake_useragent import UserAgent
    HAS_FAKE_UA = True
except ImportError:
    HAS_FAKE_UA = False
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import USER_AGENT, SCRAPE_DELAY

logger = logging.getLogger(__name__)

class RealtorScraper:
    """
    A class to scrape real estate listings from Realtor.ca using Selenium.
    This approach is more robust against anti-scraping measures than direct API requests.
    """
    
    def __init__(self, headless=False, user_agent=USER_AGENT, delay=SCRAPE_DELAY):
        """
        Initialize the scraper.
        
        Args:
            headless (bool): Whether to run the browser in headless mode (default=False to debug)
            user_agent (str): User agent string to use
            delay (int): Delay between actions in seconds
        """
        # Running in non-headless mode so you can see what's happening
        self.headless = headless  
        self.user_agent = user_agent
        self.delay = delay
        self.driver = None
        
    def _setup_driver(self):
        """Set up the Selenium WebDriver with appropriate options."""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless")
        
        # Use random user agent if available, else use the provided one
        if HAS_FAKE_UA:
            ua = UserAgent(os='windows')
            user_agent = ua.random
            logger.info(f"Using random user agent: {user_agent}")
            options.add_argument(f"user-agent={user_agent}")
        elif self.user_agent:
            options.add_argument(f"user-agent={self.user_agent}")
        
        # Add additional options for stability and to avoid detection
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Disable images for faster loading
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        
        # Remove automation flags
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Initialize the driver with automatic ChromeDriver installation
        try:
            # Try using WebDriver Manager to automatically download and use the correct ChromeDriver
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            logger.info("Successfully initialized Chrome driver using WebDriver Manager")
        except Exception as e:
            # Fallback to standard initialization
            logger.warning(f"Failed to use WebDriver Manager: {e}. Falling back to standard initialization.")
            self.driver = webdriver.Chrome(options=options)
        
        # Set window size
        self.driver.set_window_size(1920, 1080)
        
        # Add a script to help avoid detection
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def search_properties(self, location, min_price=None, max_price=None, 
                          min_bedrooms=None, max_results=50):
        """
        Search for properties on Realtor.ca.
        
        Args:
            location (str): Location to search in (city, neighborhood, postal code)
            min_price (int): Minimum price
            max_price (int): Maximum price
            min_bedrooms (int): Minimum number of bedrooms
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of property dictionaries
        """
        if not self.driver:
            self._setup_driver()
            
        # Navigate to Realtor.ca
        logger.info(f"Navigating to Realtor.ca to search for: {location}")
        self.driver.get("https://www.realtor.ca/")
        
        try:
            # Increase wait time for page load
            logger.info("Waiting for main search page to load...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
            
            # More realistic human delay
            time.sleep(random.uniform(3, 5))
            
            # Try multiple search input selectors (the site may have changed)
            search_selectors = [
                ".searchHomeBoxWrap input[type='text']",
                ".locationText input",
                "input[placeholder*='address']",
                "input[placeholder*='location']",
                "input[placeholder*='search']",
                "#location",
                ".search-input"
            ]
            
            logger.info("Trying to find and interact with search box...")
            
            # Try each selector
            search_box = None
            for selector in search_selectors:
                try:
                    logger.info(f"Trying selector: {selector}")
                    search_box = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if search_box:
                        logger.info(f"Found search box with selector: {selector}")
                        break
                except Exception as e:
                    logger.info(f"Selector {selector} failed: {e}")
            
            if not search_box:
                # If we can't find the search box, try using JavaScript to set window.location
                logger.info("Search box not found, navigating directly to search URL...")
                encoded_location = location.replace(" ", "%20")
                self.driver.execute_script(f"window.location = 'https://www.realtor.ca/map#locationQuery={encoded_location}'")
                time.sleep(5)
                return
            
            # Click and interact with the search box
            search_box.click()
            
            # Clear any existing text
            search_box.clear()
            
            # Type location with random delays between keystrokes
            for char in location:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            # More realistic human delay
            time.sleep(random.uniform(2, 3))
            
            # Try different approaches to submit the search
            try:
                # Try to find and click the search button
                search_button_selectors = [
                    ".locationBtn", 
                    "button[type='submit']",
                    "button.search-button",
                    ".search-submit"
                ]
                
                for selector in search_button_selectors:
                    try:
                        search_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        search_button.click()
                        logger.info(f"Clicked search button with selector: {selector}")
                        break
                    except:
                        pass
                        
            except Exception as e:
                # If we can't find the button, press Enter
                logger.info(f"Search button not found, pressing Enter: {e}")
                search_box.send_keys(webdriver.Keys.RETURN)
            
            # Wait for search results page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".cardCon"))
            )
            
            # Apply filters if needed
            if min_price or max_price or min_bedrooms:
                try:
                    # Click on filters button
                    filter_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".filtersBtn"))
                    )
                    filter_button.click()
                    
                    # Wait for filter modal to appear
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".filterModal"))
                    )
                    
                    # Apply price filters
                    if min_price:
                        min_price_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='PriceMin']")
                        min_price_input.clear()
                        min_price_input.send_keys(str(min_price))
                        
                    if max_price:
                        max_price_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='PriceMax']")
                        max_price_input.clear()
                        max_price_input.send_keys(str(max_price))
                    
                    # Apply bedroom filter
                    if min_bedrooms:
                        bedroom_dropdown = self.driver.find_element(By.CSS_SELECTOR, "select[name='BedroomsMin']")
                        bedroom_dropdown.click()
                        bedroom_option = self.driver.find_element(By.CSS_SELECTOR, f"option[value='{min_bedrooms}']")
                        bedroom_option.click()
                    
                    # Apply filters
                    apply_button = self.driver.find_element(By.CSS_SELECTOR, ".applyFiltersBtn")
                    apply_button.click()
                    
                    # Wait for filtered results to load
                    time.sleep(3)
                    
                except (TimeoutException, NoSuchElementException) as e:
                    logger.warning(f"Error applying filters: {e}")
            
            # Scrape the results
            properties = []
            page = 1
            
            while len(properties) < max_results:
                logger.info(f"Scraping page {page} of results")
                
                # Find all property cards
                property_cards = self.driver.find_elements(By.CSS_SELECTOR, ".cardCon")
                
                if not property_cards:
                    logger.warning("No property cards found on page")
                    break
                
                # Process each property card
                for card in property_cards:
                    if len(properties) >= max_results:
                        break
                        
                    try:
                        # Extract basic info
                        address = card.find_element(By.CSS_SELECTOR, ".address").text.strip()
                        price = card.find_element(By.CSS_SELECTOR, ".listingCardPrice").text.strip()
                        
                        # Extract price value (remove $ and commas)
                        price_value = None
                        if price:
                            price_value = int(price.replace("$", "").replace(",", ""))
                        
                        # Try to get bedrooms
                        bedrooms = None
                        try:
                            beds_element = card.find_element(By.CSS_SELECTOR, ".listingCardIconNum.propertyIcon-Beds")
                            bedrooms = beds_element.text.strip()
                        except NoSuchElementException:
                            pass
                            
                        # Try to get bathrooms
                        bathrooms = None
                        try:
                            baths_element = card.find_element(By.CSS_SELECTOR, ".listingCardIconNum.propertyIcon-Baths")
                            bathrooms = baths_element.text.strip()
                        except NoSuchElementException:
                            pass
                        
                        # Create property dictionary
                        property_dict = {
                            "address": address,
                            "price": price_value,
                            "bedrooms": bedrooms,
                            "bathrooms": bathrooms,
                            "url": card.get_attribute("data-url")
                        }
                        
                        properties.append(property_dict)
                        
                    except (NoSuchElementException, Exception) as e:
                        logger.warning(f"Error processing property card: {e}")
                
                # Check if we need to go to next page
                if len(properties) < max_results:
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, ".paginationNext")
                        if "disabled" not in next_button.get_attribute("class"):
                            next_button.click()
                            time.sleep(random.uniform(2, 4))  # Wait for next page to load
                            page += 1
                        else:
                            break  # No more pages
                    except NoSuchElementException:
                        break  # No next button found
            
            return properties
            
        except Exception as e:
            logger.error(f"Error searching properties: {e}")
            return []
        
    def get_property_details(self, property_url):
        """
        Get detailed information for a specific property.
        
        Args:
            property_url (str): URL of the property detail page
            
        Returns:
            dict: Property details
        """
        if not self.driver:
            self._setup_driver()
            
        try:
            # Navigate to property page
            self.driver.get(property_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".propertyDetailsSectionContent"))
            )
            
            # Extract additional details
            details = {}
            
            # Base info
            details["address"] = self.driver.find_element(By.CSS_SELECTOR, ".address").text.strip()
            
            price_element = self.driver.find_element(By.CSS_SELECTOR, ".propertyDetailsPrice")
            price_text = price_element.text.strip()
            details["price"] = int(price_text.replace("$", "").replace(",", ""))
            
            # Property details section
            detail_sections = self.driver.find_elements(By.CSS_SELECTOR, ".propertyDetailsSectionContentRow")
            
            for section in detail_sections:
                try:
                    label = section.find_element(By.CSS_SELECTOR, ".propertyDetailsSectionContentLabel").text.strip()
                    value = section.find_element(By.CSS_SELECTOR, ".propertyDetailsSectionContentValue").text.strip()
                    
                    # Map common labels to standardized fields
                    if "Bedrooms" in label:
                        details["bedrooms"] = value
                    elif "Bathrooms" in label:
                        details["bathrooms"] = value
                    elif "Year Built" in label:
                        details["year_built"] = value
                    elif "Square Footage" in label or "Living Area" in label:
                        details["square_feet"] = value
                    elif "Property Tax" in label:
                        tax_value = value.replace("$", "").replace(",", "")
                        try:
                            details["property_tax"] = int(float(tax_value))
                        except ValueError:
                            details["property_tax"] = value
                    else:
                        # Store other details with standardized keys
                        key = label.lower().replace(" ", "_").replace(":", "")
                        details[key] = value
                        
                except NoSuchElementException:
                    continue
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting property details: {e}")
            return {}

def scrape_realtor_listings(location="Ottawa, ON", max_properties=50, min_price=None, max_price=None, min_bedrooms=None):
    """
    Scrape real estate listings from Realtor.ca.
    
    Args:
        location (str): Location to search in
        max_properties (int): Maximum number of properties to return
        min_price (int): Minimum price
        max_price (int): Maximum price
        min_bedrooms (int): Minimum number of bedrooms
        
    Returns:
        DataFrame: DataFrame with property listings
    """
    # Set headless=False to see the browser for debugging
    scraper = RealtorScraper(headless=False)
    
    # Print instructions for the user
    print("\n" + "="*80)
    print("IMPORTANT: A Chrome browser window will open to scrape Realtor.ca")
    print("Please do not close this window while scraping is in progress")
    print("This approach helps to avoid detection and blocking")
    print("="*80 + "\n")
    
    try:
        # Search for properties
        properties = scraper.search_properties(
            location=location,
            min_price=min_price,
            max_price=max_price,
            min_bedrooms=min_bedrooms,
            max_results=max_properties
        )
        
        if not properties:
            logger.warning("No properties found")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame(properties)
        
        # Get more details for each property (optional - can be slow)
        # This is commented out to avoid making too many requests
        # Uncomment to get more detailed information
        """
        detailed_properties = []
        for idx, row in df.iterrows():
            if 'url' in row and row['url']:
                logger.info(f"Getting details for property {idx+1}/{len(df)}")
                details = scraper.get_property_details(row['url'])
                detailed_properties.append(details)
                time.sleep(random.uniform(1, 3))  # Random delay
            else:
                detailed_properties.append({})
        
        # Create detailed DataFrame
        detailed_df = pd.DataFrame(detailed_properties)
        
        # Merge with original DataFrame
        if not detailed_df.empty:
            df = pd.concat([df, detailed_df], axis=1)
        """
        
        return df
        
    except Exception as e:
        logger.error(f"Error in scrape_realtor_listings: {e}")
        return pd.DataFrame()
    finally:
        scraper.close()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Test the scraper
    df = scrape_realtor_listings(
        location="Ottawa, ON",
        max_properties=10,
        min_price=300000,
        max_price=800000,
        min_bedrooms=2
    )
    
    print(f"Found {len(df)} properties")
    print(df.head())
    
    # Save to CSV
    if not df.empty:
        df.to_csv("realtor_listings.csv", index=False)