"""
Web scraper for MOSIR Łańcut swimming pool occupancy data.
"""
import re
import logging
from typing import Optional, Tuple
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# URL to scrape
MOSIR_URL = "http://www.mosir-lancut.pl/asp/pl_start.asp?typ=14&menu=135&strona=1"

# Request headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def fetch_pool_occupancy() -> Optional[Tuple[int, int]]:
    """
    Fetches the current pool occupancy from the MOSIR website.
    
    Returns:
        Tuple of (current_count, max_capacity) if successful, None otherwise
    """
    try:
        # Fetch the webpage
        response = requests.get(MOSIR_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Look for the text "AKTUALNA LICZBA OSÓB NA BASENIE"
        # The format appears to be "XX/YY" where XX is current and YY is max
        text_content = soup.get_text()
        
        # Search for the pattern near the "AKTUALNA LICZBA OSÓB NA BASENIE" text
        # The pattern is usually something like "00/80" or "15/80"
        pattern = r'AKTUALNA\s+LICZBA\s+OSÓB\s+NA\s+BASENIE[^\d]*(\d+)\s*/\s*(\d+)'
        match = re.search(pattern, text_content, re.IGNORECASE | re.DOTALL)
        
        if match:
            current_count = int(match.group(1))
            max_capacity = int(match.group(2))
            logger.info(f"Successfully scraped occupancy: {current_count}/{max_capacity}")
            return (current_count, max_capacity)
        
        # Alternative: search for bold text containing numbers in XX/YY format
        # The website might have the data in a specific HTML element
        bold_elements = soup.find_all(['b', 'strong'])
        for elem in bold_elements:
            text = elem.get_text().strip()
            # Look for pattern like "00/80" or "15/80"
            match = re.search(r'(\d+)\s*/\s*(\d+)', text)
            if match:
                # Check if this element is near the "AKTUALNA LICZBA" text
                parent_text = elem.find_parent().get_text() if elem.find_parent() else ""
                if 'AKTUALNA' in parent_text.upper() or 'BASENIE' in parent_text.upper():
                    current_count = int(match.group(1))
                    max_capacity = int(match.group(2))
                    logger.info(f"Successfully scraped occupancy: {current_count}/{max_capacity}")
                    return (current_count, max_capacity)
        
        # Last resort: find any XX/YY pattern that might be the occupancy
        all_text = soup.get_text()
        matches = re.findall(r'(\d+)\s*/\s*(\d+)', all_text)
        if matches:
            # Take the first match that looks reasonable (max capacity between 50-200)
            for match in matches:
                current, max_cap = int(match[0]), int(match[1])
                if 50 <= max_cap <= 200:
                    logger.info(f"Found potential occupancy: {current}/{max_cap}")
                    return (current, max_cap)
        
        logger.warning("Could not find occupancy data in the expected format")
        return None
        
    except requests.RequestException as e:
        logger.error(f"Network error while fetching pool occupancy: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing pool occupancy data: {e}")
        return None
