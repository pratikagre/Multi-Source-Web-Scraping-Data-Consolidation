"""
Unit tests for data validation rules.
"""

from processing.validation import validate_record, validate_records


def test_valid_book_record():
    book = {
        "source": "Books to Scrape",
        "name_or_title": "A Light in the Attic",
        "category": "Poetry",
        "price": 51.77,
        "rating": 3,
        "author": None,
        "tags": None,
        "description": None,
        "source_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        "scraped_at": "2026-10-06T18:00:00Z",
    }
    assert validate_record(book) == []


def test_valid_quote_record():
    quote = {
        "source": "Quotes to Scrape",
        "name_or_title": "The world as we have created it is a process of our thinking.",
        "category": None,
        "price": None,
        "rating": None,
        "author": "Albert Einstein",
        "tags": "change;deep-thoughts;thinking;world",
        "description": None,
        "source_url": "https://quotes.toscrape.com/author/Albert-Einstein",
        "scraped_at": "2026-10-06T18:00:00Z",
    }
    assert validate_record(quote) == []


def test_invalid_source():
    rec = {
        "source": "Unknown Site",
        "name_or_title": "Something",
        "source_url": "https://example.com",
    }
    assert "unknown_source" in validate_record(rec)


def test_missing_name():
    rec = {
        "source": "Books to Scrape",
        "name_or_title": "",
        "source_url": "https://books.toscrape.com/book",
        "price": 10.0,
    }
    assert "missing_name" in validate_record(rec)


def test_invalid_url():
    rec = {
        "source": "Books to Scrape",
        "name_or_title": "Book Title",
        "source_url": "ftp://not-http.com",
        "price": 10.0,
    }
    assert "invalid_url" in validate_record(rec)


def test_invalid_price():
    # Negative price
    rec = {
        "source": "Books to Scrape",
        "name_or_title": "Book Title",
        "source_url": "https://books.toscrape.com/book",
        "price": -5.0,
    }
    assert "invalid_price" in validate_record(rec)


def test_missing_price_book():
    rec = {
        "source": "Books to Scrape",
        "name_or_title": "Book Title",
        "source_url": "https://books.toscrape.com/book",
        "price": None,
    }
    assert "missing_price" in validate_record(rec)


def test_invalid_rating():
    rec = {
        "source": "Books to Scrape",
        "name_or_title": "Book Title",
        "source_url": "https://books.toscrape.com/book",
        "price": 10.0,
        "rating": 6,  # Out of range 1-5
    }
    assert "invalid_rating" in validate_record(rec)


def test_missing_author_quote():
    rec = {
        "source": "Quotes to Scrape",
        "name_or_title": "Some inspirational quote",
        "source_url": "https://quotes.toscrape.com/quote/1",
        "author": None,
    }
    assert "missing_author" in validate_record(rec)


def test_validate_records_batch():
    valid = {
        "source": "Books to Scrape",
        "name_or_title": "Good Book",
        "source_url": "https://books.toscrape.com/book",
        "price": 12.0,
    }
    bad1 = {
        "source": "Books to Scrape",
        "name_or_title": "",  # missing name
        "source_url": "https://books.toscrape.com/book",
        "price": 12.0,
    }
    bad2 = {
        "source": "Bad Source",  # unknown source
        "name_or_title": "Bad",
        "source_url": "invalid-url",  # invalid url
    }

    valid_list, rejected_list, reasons = validate_records([valid, bad1, bad2])
    assert len(valid_list) == 1
    assert len(rejected_list) == 2
    assert reasons["missing_name"] == 1
    assert reasons["unknown_source"] == 1
    assert reasons["invalid_url"] == 1
