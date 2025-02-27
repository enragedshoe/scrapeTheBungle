"""
Module for scraping dynamic websites using Selenium.
"""
import time
import pandas as pd
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import os

# Add the parent directory to sys.path to allow for import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class DynamicScraper(BaseScraper):
    """
    Scraper for dynamic websites using Selenium.
    """
    
    def __init__(self, headless=True, delay=2, user_agent=None, chromedriver_path=None):
        """
        Initialize the dynamic scraper.
        
        Args:
            headless (bool): Whether to run browser in headless mode
            delay (int): Delay between actions in seconds
            user_agent (str): Browser user agent
            chromedriver_path (str): Path to chromedriver binary
        """
        super().__init__(delay=delay, user_agent=user_agent)
        self.headless = headless
        self.chromedriver_path = chromedriver_path
        self.driver = None
    
    def _setup_driver(self):
        """Set up Selenium webdriver."""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless")
            
        # Add user agent
        if self.user_agent:
            options.add_argument(f"user-agent={self.user_agent}")
        
        # Add additional options for stability
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Initialize the driver with service if path is provided
        if self.chromedriver_path:
            service = Service(executable_path=self.chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)
            
        # Set window size
        self.driver.set_window_size(1920, 1080)
    
    def load_page(self, url, wait_for_element=None, wait_time=10):
        """
        Load a page and wait for a specific element to appear.
        
        Args:
            url (str): URL to load
            wait_for_element (tuple): Element to wait for (By, selector)
            wait_time (int): Maximum time to wait in seconds
            
        Returns:
            bool: True if page loaded successfully, False otherwise
        """
        if not self.driver:
            self._setup_driver()
            
        try:
            self.driver.get(url)
            
            if wait_for_element:
                by, selector = wait_for_element
                WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((by, selector))
                )
            return True
        except Exception as e:
            logger.error(f"Error loading page {url}: {e}")
            return False
    
    def get_page_source(self):
        """
        Get the current page source.
        
        Returns:
            str: Page source HTML
        """
        if not self.driver:
            return None
        return self.driver.page_source
    
    def parse_with_soup(self):
        """
        Parse the current page with BeautifulSoup.
        
        Returns:
            BeautifulSoup: Parsed HTML
        """
        if not self.driver:
            return None
        return BeautifulSoup(self.driver.page_source, "html.parser")
    
    def find_elements(self, by, selector):
        """
        Find elements on the page.
        
        Args:
            by (selenium.webdriver.common.by.By): Method to locate elements
            selector (str): Selector string
            
        Returns:
            list: List of web elements
        """
        if not self.driver:
            return []
        return self.driver.find_elements(by, selector)
    
    def close(self):
        """Close the webdriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

def scrape_dynamic_content(url, element_class="listing", wait_time=10):
    """
    Convenience function to scrape a dynamic website.
    
    Args:
        url (str): URL to scrape
        element_class (str): CSS class of elements to extract
        wait_time (int): Time to wait for page to load
        
    Returns:
        DataFrame: Scraped data
    """
    scraper = DynamicScraper(headless=True)
    
    try:
        # Load the page and wait for listings to appear
        scraper.load_page(url, wait_for_element=(By.CLASS_NAME, element_class), wait_time=wait_time)
        
        # Get the page content with BeautifulSoup
        soup = scraper.parse_with_soup()
        if not soup:
            return pd.DataFrame()
        
        # Find all listing elements
        listings = soup.find_all("div", class_=element_class)
        
        data = []
        for listing in listings:
            # Extract data from each listing - replace these selectors with actual ones
            price = listing.find("span", class_="price").get_text(strip=True) if listing.find("span", class_="price") else "N/A"
            year_built = listing.find("span", class_="year-built").get_text(strip=True) if listing.find("span", class_="year-built") else "N/A"
            
            data.append({
                "price": price,
                "year_built": year_built
            })
        
        return pd.DataFrame(data)
    finally:
        # Always close the browser
        scraper.close()