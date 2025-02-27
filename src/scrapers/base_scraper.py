"""
Base scraper classes and utilities for the real estate comparison tool.
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../logs/scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BaseScraper:
    """Base class for all scrapers with common functionality."""
    
    def __init__(self, delay=2, user_agent=None):
        """
        Initialize the base scraper.
        
        Args:
            delay (int): Delay between requests in seconds to avoid rate limiting
            user_agent (str): User agent string to use for requests
        """
        self.delay = delay
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
    
    def make_request(self, url, method="get", params=None, data=None, headers=None, timeout=10):
        """
        Make an HTTP request with error handling and rate limiting.
        
        Args:
            url (str): URL to request
            method (str): HTTP method (get, post)
            params (dict): URL parameters for GET requests
            data (dict): Form data for POST requests
            headers (dict): Additional headers
            timeout (int): Request timeout in seconds
            
        Returns:
            requests.Response: Response object or None if request failed
        """
        # Sleep to avoid hitting rate limits
        time.sleep(self.delay)
        
        # Update headers if provided
        if headers:
            self.session.headers.update(headers)
        
        try:
            if method.lower() == "get":
                response = self.session.get(url, params=params, timeout=timeout)
            elif method.lower() == "post":
                response = self.session.post(url, data=data, params=params, timeout=timeout)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
    
    def save_data(self, df, filename, output_dir="../data/raw"):
        """
        Save DataFrame to CSV file.
        
        Args:
            df (DataFrame): Data to save
            filename (str): Filename to save to
            output_dir (str): Directory to save to
            
        Returns:
            str: Path to saved file
        """
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        df.to_csv(output_path, index=False)
        logger.info(f"Data saved to {output_path}")
        return output_path

class HTMLScraper(BaseScraper):
    """Scraper for HTML content using BeautifulSoup."""
    
    def parse_html(self, html_content):
        """
        Parse HTML content using BeautifulSoup.
        
        Args:
            html_content (str): HTML content to parse
            
        Returns:
            BeautifulSoup: Parsed HTML
        """
        return BeautifulSoup(html_content, "html.parser")
    
    def scrape_url(self, url, params=None):
        """
        Scrape URL and return BeautifulSoup object.
        
        Args:
            url (str): URL to scrape
            params (dict): URL parameters
            
        Returns:
            BeautifulSoup: Parsed HTML or None if request failed
        """
        response = self.make_request(url, params=params)
        if response:
            return self.parse_html(response.text)
        return None

class APIScraper(BaseScraper):
    """Scraper for JSON APIs."""
    
    def fetch_json(self, url, params=None, data=None, method="get"):
        """
        Fetch JSON data from API.
        
        Args:
            url (str): API URL
            params (dict): URL parameters
            data (dict): POST data
            method (str): HTTP method
            
        Returns:
            dict: JSON response or None if request failed
        """
        response = self.make_request(url, method=method, params=params, data=data)
        if response:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"Failed to parse JSON: {e}")
                return None
        return None