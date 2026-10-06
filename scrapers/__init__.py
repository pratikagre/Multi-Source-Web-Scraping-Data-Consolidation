"""Scrapers package for Books to Scrape and Quotes to Scrape."""

from scrapers.base_scraper import BaseScraper, create_session
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

__all__ = ["BaseScraper", "create_session", "BooksScraper", "QuotesScraper"]
