"""
Base Scraper Module
Provides a resilient HTTP session, retry logic, rate limiting, and base scraper class.
"""

import logging
import time
from typing import Optional, Tuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "ScrapingAssignment/1.0 (Educational Scraping Pipeline; Python 3.12)"
DEFAULT_STATUS_FORCELIST = (429, 500, 502, 503, 504)


def create_session(
    user_agent: str = DEFAULT_USER_AGENT,
    retries: int = 3,
    backoff_factor: float = 1.0,
    status_forcelist: Tuple[int, ...] = DEFAULT_STATUS_FORCELIST,
) -> requests.Session:
    """
    Creates a requests.Session configured with standard headers and
    automatic exponential backoff retries for transient HTTP errors.
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    )

    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class BaseScraper:
    """
    Abstract base scraper class encapsulating networking, rate limiting,
    and page fetching.
    """

    def __init__(
        self,
        base_url: str,
        session: Optional[requests.Session] = None,
        delay: float = 0.5,
        timeout: float = 10.0,
        max_pages: Optional[int] = None,
    ):
        self.base_url = base_url
        self.session = session or create_session()
        self.delay = delay
        self.timeout = timeout
        self.max_pages = max_pages

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetches an HTML page, enforces polite delay, ensures UTF-8 encoding,
        and returns a BeautifulSoup object. Returns None on failure.
        """
        if self.delay > 0:
            time.sleep(self.delay)

        try:
            logger.info("Fetching URL: %s", url)
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Ensure proper encoding for currency symbols and quotes
            response.encoding = response.apparent_encoding or "utf-8"
            return BeautifulSoup(response.text, "lxml")

        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out for %s: %s", url, exc)
            return None
        except requests.exceptions.HTTPError as exc:
            logger.error("HTTP error fetching %s: %s", url, exc)
            return None
        except requests.exceptions.RequestException as exc:
            logger.error("Network error fetching %s: %s", url, exc)
            return None
        except Exception as exc:
            logger.error("Unexpected error fetching %s: %s", url, exc, exc_info=True)
            return None

    def scrape(self) -> list[dict]:
        """Subclasses must implement the scrape method."""
        raise NotImplementedError("Subclasses must implement the scrape method.")
