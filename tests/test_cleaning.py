"""
Unit tests for data cleaning functions.
"""

from processing.cleaning import (
    clean_price,
    clean_rating,
    clean_record,
    clean_tags,
    clean_text,
    normalize_url,
    strip_quotes,
)


def test_clean_text():
    assert clean_text(None) is None
    assert clean_text("") is None
    assert clean_text("   ") is None
    assert clean_text(" Hello \n World \t ") == "Hello World"
    assert clean_text("Non-breaking\xa0space\xa0here") == "Non-breaking space here"
    assert clean_text(123) == "123"


def test_strip_quotes():
    assert strip_quotes(None) is None
    assert strip_quotes("") is None
    # Curly double quotes
    assert strip_quotes("“The world is a book.”") == "The world is a book."
    # Straight quotes
    assert strip_quotes('"To be or not to be"') == "To be or not to be"
    assert strip_quotes("'Single quote'") == "Single quote"
    # Mixed whitespace and curly quotes
    assert strip_quotes("  “ Quoted with spaces ”  ") == "Quoted with spaces"


def test_clean_price():
    assert clean_price(None) is None
    assert clean_price("") is None
    assert clean_price("£51.77") == 51.77
    assert clean_price("$19.99") == 19.99
    assert clean_price("1,250.50") == 1250.50
    assert clean_price("Price: 42.00 EUR") == 42.00
    assert clean_price(25) == 25.0
    assert clean_price(14.95) == 14.95
    assert clean_price("N/A") is None
    assert clean_price("free") is None


def test_clean_rating():
    assert clean_rating(None) is None
    assert clean_rating("") is None
    assert clean_rating("One") == 1
    assert clean_rating("two") == 2
    assert clean_rating("THREE") == 3
    assert clean_rating("four") == 4
    assert clean_rating("Five") == 5
    assert clean_rating("star-rating Three") == 3
    assert clean_rating(4) == 4
    assert clean_rating("5") == 5
    assert clean_rating("Zero") is None
    assert clean_rating("Six") is None
    assert clean_rating("Unrated") is None


def test_clean_tags():
    assert clean_tags(None) is None
    assert clean_tags([]) is None
    assert clean_tags("") is None
    # Deduplication, trimming, lowercasing, sorting
    result = clean_tags(["World", "change ", "world", "Deep-Thoughts"])
    assert result == "change;deep-thoughts;world"
    # String input with comma
    assert clean_tags("books, reading, Books") == "books;reading"


def test_normalize_url():
    assert normalize_url(None) is None
    assert normalize_url("") is None
    assert (
        normalize_url("https://books.toscrape.com/index.html")
        == "https://books.toscrape.com/index.html"
    )
    # Joining relative URL
    base = "https://books.toscrape.com/catalogue/category/books_1/"
    relative = "../../a-light-in-the-attic_1000/index.html"
    expected = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    assert normalize_url(relative, base_url=base) == expected
    # Invalid schemes
    assert normalize_url("javascript:void(0);") is None
    assert normalize_url("ftp://example.com/file.txt") is None


def test_clean_record_book():
    raw_book = {
        "source": "Books to Scrape",
        "name_or_title": "  A Light in the Attic  ",
        "category": None,
        "price_raw": "£51.77",
        "rating_raw": "star-rating Three",
        "author": None,
        "tags": None,
        "description": None,
        "source_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        "scraped_at": "2026-10-06T18:00:00Z",
    }
    cleaned = clean_record(raw_book)
    assert cleaned["source"] == "Books to Scrape"
    assert cleaned["name_or_title"] == "A Light in the Attic"
    assert cleaned["price"] == 51.77
    assert cleaned["rating"] == 3
    assert cleaned["author"] is None
    assert cleaned["tags"] is None
    assert cleaned["source_url"] == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"


def test_clean_record_quote():
    raw_quote = {
        "source": "Quotes to Scrape",
        "name_or_title": " “The world as we have created it is a process of our thinking.” ",
        "category": None,
        "price_raw": None,
        "rating_raw": None,
        "author": " Albert Einstein ",
        "tags": ["change", "deep-thoughts", "thinking", "world"],
        "description": None,
        "source_url": "https://quotes.toscrape.com/author/Albert-Einstein",
        "scraped_at": "2026-10-06T18:00:00Z",
    }
    cleaned = clean_record(raw_quote)
    assert cleaned["source"] == "Quotes to Scrape"
    assert (
        cleaned["name_or_title"]
        == "The world as we have created it is a process of our thinking."
    )
    assert cleaned["price"] is None
    assert cleaned["rating"] is None
    assert cleaned["author"] == "Albert Einstein"
    assert cleaned["tags"] == "change;deep-thoughts;thinking;world"
    assert cleaned["source_url"] == "https://quotes.toscrape.com/author/Albert-Einstein"
