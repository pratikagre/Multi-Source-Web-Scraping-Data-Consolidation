"""
Data Cleaning and Standardization Module
Provides pure transformation functions for text, prices, ratings, tags, and URLs.
"""

from datetime import datetime, timezone
import re
from typing import Any, List, Optional, Union
from urllib.parse import urljoin, urlparse

RATING_MAP = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}

QUOTE_STRIP_CHARS = " \t\r\n\xa0\"'“”‘’«»"


def clean_text(value: Optional[Any]) -> Optional[str]:
    """
    Cleans general text by:
    - Converting non-strings (if applicable) or handling None
    - Replacing non-breaking spaces (\\xa0) with regular spaces
    - Collapsing all consecutive whitespace (spaces, tabs, newlines) into a single space
    - Stripping leading and trailing whitespace
    - Returning None if the string is empty
    """
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)

    # Replace non-breaking spaces and collapse all whitespace
    text = " ".join(value.replace("\xa0", " ").split())
    return text if text else None


def strip_quotes(value: Optional[str]) -> Optional[str]:
    """
    Strips leading and trailing straight and typographic/curly quotes,
    including whitespace, from quote text.
    """
    if value is None:
        return None
    text = clean_text(value)
    if not text:
        return None
    # Strip opening and closing quotes
    text = text.strip(QUOTE_STRIP_CHARS)
    return text if text else None


def clean_price(raw: Optional[Union[str, float, int]]) -> Optional[float]:
    """
    Extracts a numeric float value from raw price strings (e.g., '£51.77', '$19.99', '12,50').
    Returns a float rounded to 2 decimal places, or None if no valid number found.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return round(float(raw), 2)

    raw_str = str(raw).replace(",", "").strip()
    match = re.search(r"\d+(?:\.\d+)?", raw_str)
    if match:
        try:
            return round(float(match.group()), 2)
        except ValueError:
            return None
    return None


def clean_rating(raw: Optional[Union[str, int]]) -> Optional[int]:
    """
    Standardizes rating representations into integer values from 1 to 5.
    Accepts:
    - Words: 'One', 'Two', 'Three', 'Four', 'Five'
    - Class strings: 'star-rating Three'
    - Integers or integer strings: 3, '3'
    """
    if raw is None:
        return None

    if isinstance(raw, int) and 1 <= raw <= 5:
        return raw

    raw_str = str(raw).strip().lower()

    # Direct digit match
    if raw_str.isdigit() and 1 <= int(raw_str) <= 5:
        return int(raw_str)

    # Word match across tokens
    tokens = raw_str.split()
    for token in tokens:
        if token in RATING_MAP:
            return RATING_MAP[token]

    return None


def clean_tags(tags: Optional[Union[List[str], str]]) -> Optional[str]:
    """
    Standardizes tags into a sorted, semicolon-separated lowercase string.
    Removes duplicates, whitespace, and empty tags.
    Example: ['world', 'Change ', 'world'] -> 'change;world'
    """
    if not tags:
        return None

    tag_list: List[str] = []
    if isinstance(tags, list):
        tag_list = tags
    elif isinstance(tags, str):
        # Support semicolon or comma separation
        delimiters = re.split(r"[,;]", tags)
        tag_list = delimiters

    cleaned = set()
    for tag in tag_list:
        c = clean_text(tag)
        if c:
            cleaned.add(c.lower())

    if not cleaned:
        return None

    return ";".join(sorted(cleaned))


def normalize_url(url: Optional[str], base_url: Optional[str] = None) -> Optional[str]:
    """
    Resolves relative URLs against a base URL and ensures valid http/https scheme.
    """
    if not url or not isinstance(url, str):
        return None

    cleaned_url = url.strip()
    if base_url:
        cleaned_url = urljoin(base_url, cleaned_url)

    parsed = urlparse(cleaned_url)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return cleaned_url
    return None


def clean_record(raw: dict) -> dict:
    """
    Takes a raw scraped dictionary and applies standard transformations to map
    into the common consolidated schema.
    """
    source = clean_text(raw.get("source"))

    # Title or quote text
    raw_title = raw.get("name_or_title")
    if source == "Quotes to Scrape":
        name_or_title = strip_quotes(raw_title)
    else:
        name_or_title = clean_text(raw_title)

    category = clean_text(raw.get("category"))
    price = clean_price(raw.get("price_raw") if "price_raw" in raw else raw.get("price"))
    rating = clean_rating(raw.get("rating_raw") if "rating_raw" in raw else raw.get("rating"))
    author = clean_text(raw.get("author"))
    tags = clean_tags(raw.get("tags"))
    description = clean_text(raw.get("description"))
    source_url = normalize_url(raw.get("source_url"))

    scraped_at = raw.get("scraped_at")
    if not scraped_at:
        scraped_at = datetime.now(timezone.utc).isoformat()

    return {
        "source": source,
        "source_url": source_url,
        "name_or_title": name_or_title,
        "category": category,
        "price": price,
        "rating": rating,
        "author": author,
        "tags": tags,
        "description": description,
        "scraped_at": scraped_at,
    }
