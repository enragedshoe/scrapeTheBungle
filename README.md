# Real Estate Comparison Tool

A Python-based web scraping tool to help compare home listings in various neighborhoods. The tool scrapes real estate listing data and combines it with commute times and crime rates to help with home buying decisions.

## Features

- Scrapes real estate listing data from Realtor.ca
- Calculates commute times to specified locations using Google Maps API
- Retrieves neighborhood crime data from Ottawa crime map
- Merges all data into a structured format for easy comparison
- Provides a web interface for searching and viewing results

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/scrapeTheBungle.git
   cd scrapeTheBungle
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your Google Maps API key:
   - You need a Google Maps API key with Distance Matrix API enabled
   - Add your API key to the `src/config.py` file

## Usage

### Command Line Interface

Run the main script:

```
python src/main.py --max-listings 50 --destination "Ottawa, ON, Canada"
```

Options:
- `--max-listings`: Maximum number of listings to scrape (default: 50)
- `--destination`: Destination address for commute calculations (default: Ottawa, ON, Canada)
- `--output`: Custom output file path

### Web Interface

Start the Flask web server:

```
python frontend/app.py
```

Then open a browser and go to: http://localhost:5000

## Project Structure

- `src/`: Core application code
  - `scrapers/`: Web scraping modules
  - `config.py`: Configuration settings
  - `main.py`: Main application script
  - `merge_data.py`: Data processing utilities
- `frontend/`: Flask web application
- `data/`: Directory for storing scraped data
  - `raw/`: Raw data from scrapers
  - `processed/`: Processed and merged data
- `logs/`: Application logs

## Dependencies

- Python 3.8+
- Requests
- BeautifulSoup4
- Pandas
- Selenium
- Flask

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Always respect websites' terms of service and robots.txt files when scraping. Check the legality of web scraping in your jurisdiction.