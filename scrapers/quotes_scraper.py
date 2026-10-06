"""
Quotes to Scrape Scraper
Collects quote data from https://quotes.toscrape.com/ across all pages.
"""

from datetime import datetime, timezone
import logging
from typing import List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

QUOTES_BASE_URL = "https://quotes.toscrape.com/"


class QuotesScraper(BaseScraper):
    """Scraper for https://quotes.toscrape.com/."""

    SOURCE_NAME = "Quotes to Scrape"

    def __init__(
        self,
        base_url: str = QUOTES_BASE_URL,
        session=None,
        delay: float = 0.5,
        timeout: float = 10.0,
        max_pages: Optional[int] = None,
    ):
        super().__init__(
            base_url=base_url,
            session=session,
            delay=delay,
            timeout=timeout,
            max_pages=max_pages,
        )

    def parse_quote(self, quote_div: BeautifulSoup, page_url: str) -> Optional[dict]:
        """
        Extracts raw fields from a single quote div.quote element.
        Catches errors per quote to prevent crashing the page scrape.
        """
        try:
            text_el = quote_div.select_one("span.text")
            author_el = quote_div.select_one("small.author")
            author_link_el = quote_div.find("a", href=lambda h: bool(h and "/author/" in h))
            tag_els = quote_div.select("div.tags a.tag")

            quote_text = text_el.get_text() if text_el else None
            author_name = author_el.get_text(strip=True) if author_el else None

            # Source URL: Prefer author detail bio URL; fallback to page URL
            source_url = None
            if author_link_el and author_link_el.get("href"):
                source_url = urljoin(page_url, author_link_el["href"])
            else:
                source_url = page_url

            tags = [t.get_text(strip=True) for t in tag_els if t.get_text(strip=True)]

            return {
                "source": self.SOURCE_NAME,
                "source_url": source_url,
                "name_or_title": quote_text,
                "category": None,  # Not applicable to quotes
                "price_raw": None,  # Not applicable to quotes
                "rating_raw": None,  # Not applicable to quotes
                "author": author_name,
                "tags": tags,
                "description": None,  # Not applicable to quotes
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            logger.warning("Error parsing quote element on %s: %s", page_url, exc)
            return None

    def parse_page(self, soup: BeautifulSoup, page_url: str) -> List[dict]:
        """Parses all quote divs on a single page."""
        quote_divs = soup.select("div.quote")
        records = []
        for qd in quote_divs:
            quote_data = self.parse_quote(qd, page_url)
            if quote_data:
                records.append(quote_data)
        return records

    def scrape(self) -> List[dict]:
        """
        Iterates dynamically through all pagination pages, extracting quotes
        until no 'next' link is found or max_pages limit is reached.
        """
        current_url = self.base_url
        page_num = 1
        all_quotes = []

        logger.info("Starting scrape for %s at %s", self.SOURCE_NAME, current_url)

        while current_url:
            if self.max_pages and page_num > self.max_pages:
                logger.info("Reached max_pages limit of %d. Stopping.", self.max_pages)
                break

            logger.info("[%s] Scraping page %d: %s", self.SOURCE_NAME, page_num, current_url)
            soup = self.fetch_page(current_url)
            if not soup:
                logger.error("Failed to retrieve page %d at %s. Halting source scrape.", page_num, current_url)
                break

            page_records = self.parse_page(soup, current_url)
            all_quotes.extend(page_records)
            logger.info(
                "[%s] Page %d extracted %d records (running total: %d)",
                self.SOURCE_NAME,
                page_num,
                len(page_records),
                len(all_quotes),
            )

            # Discover next page link
            next_link = soup.select_one("li.next > a")
            if next_link and next_link.get("href"):
                current_url = urljoin(current_url, next_link["href"])
                page_num += 1
            else:
                logger.info("[%s] No next page link found. Reached final page (%d).", self.SOURCE_NAME, page_num)
                current_url = None

        logger.info("[%s] Scraping completed. Total records collected: %d", self.SOURCE_NAME, len(all_quotes))
        return all_quotes
