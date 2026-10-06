"""
Books to Scrape Scraper
Collects book catalog data from https://books.toscrape.com/ across all pages.
"""

from datetime import datetime, timezone
import logging
from typing import List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BOOKS_BASE_URL = "https://books.toscrape.com/"


class BooksScraper(BaseScraper):
    """Scraper for https://books.toscrape.com/."""

    SOURCE_NAME = "Books to Scrape"

    def __init__(
        self,
        base_url: str = BOOKS_BASE_URL,
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

    def parse_book(self, article: BeautifulSoup, page_url: str) -> Optional[dict]:
        """
        Extracts raw fields from a single book article.product_pod element.
        Catches errors per book to prevent crashing the page scrape.
        """
        try:
            link = article.select_one("h3 > a")
            price_el = article.select_one("p.price_color")
            rating_el = article.select_one("p.star-rating")
            avail_el = article.select_one("p.instock.availability")

            title = None
            book_url = None
            if link:
                # Full title is in 'title' attribute; text node is truncated with ellipsis
                title = link.get("title") or link.get_text(strip=True)
                href = link.get("href")
                if href:
                    book_url = urljoin(page_url, href)

            price_raw = price_el.get_text(strip=True) if price_el else None
            rating_raw = " ".join(rating_el.get("class", [])) if rating_el else None
            availability_raw = avail_el.get_text(strip=True) if avail_el else None

            return {
                "source": self.SOURCE_NAME,
                "source_url": book_url,
                "name_or_title": title,
                "category": None,  # Not present on listing page
                "price_raw": price_raw,
                "rating_raw": rating_raw,
                "author": None,  # Not applicable to books
                "tags": None,  # Not applicable to books
                "description": None,  # Not present on listing page
                "availability_raw": availability_raw,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            logger.warning("Error parsing book pod on %s: %s", page_url, exc)
            return None

    def parse_page(self, soup: BeautifulSoup, page_url: str) -> List[dict]:
        """Parses all book pods on a single page."""
        articles = soup.select("article.product_pod")
        records = []
        for article in articles:
            book_data = self.parse_book(article, page_url)
            if book_data:
                records.append(book_data)
        return records

    def scrape(self) -> List[dict]:
        """
        Iterates dynamically through all pagination pages, extracting books
        until no 'next' link is found or max_pages limit is reached.
        """
        current_url = self.base_url
        page_num = 1
        all_books = []

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
            all_books.extend(page_records)
            logger.info(
                "[%s] Page %d extracted %d records (running total: %d)",
                self.SOURCE_NAME,
                page_num,
                len(page_records),
                len(all_books),
            )

            # Discover next page link
            next_link = soup.select_one("li.next > a")
            if next_link and next_link.get("href"):
                current_url = urljoin(current_url, next_link["href"])
                page_num += 1
            else:
                logger.info("[%s] No next page link found. Reached final page (%d).", self.SOURCE_NAME, page_num)
                current_url = None

        logger.info("[%s] Scraping completed. Total records collected: %d", self.SOURCE_NAME, len(all_books))
        return all_books
