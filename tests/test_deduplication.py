"""
Unit tests for duplicate detection and fingerprinting.
"""

from processing.deduplication import deduplicate_records, make_fingerprint


def test_fingerprint_normalization():
    rec1 = {"source": "Books to Scrape", "name_or_title": "Example Book Title"}
    rec2 = {"source": "Books to Scrape", "name_or_title": " Example Book Title "}
    rec3 = {"source": "Books to Scrape", "name_or_title": "EXAMPLE BOOK TITLE"}
    rec4 = {"source": "Books to Scrape", "name_or_title": "Example Book Title!"}

    fp1 = make_fingerprint(rec1)
    fp2 = make_fingerprint(rec2)
    fp3 = make_fingerprint(rec3)
    fp4 = make_fingerprint(rec4)

    assert fp1 == fp2 == fp3 == fp4


def test_duplicates_filter_mode():
    base = {"source": "Books to Scrape", "author": None, "source_url": "https://books.toscrape.com/1"}
    records = [
        {**base, "name_or_title": "Example Book Title"},
        {**base, "name_or_title": "  Example Book Title  "},
        {**base, "name_or_title": "EXAMPLE BOOK TITLE"},
        {**base, "name_or_title": "Another Unique Book"},
    ]

    unique, dupes, counts = deduplicate_records(records, flag_only=False)
    assert len(unique) == 2
    assert len(dupes) == 2
    assert counts["Books to Scrape"] == 2
    assert unique[0]["name_or_title"] == "Example Book Title"
    assert unique[1]["name_or_title"] == "Another Unique Book"


def test_quotes_fingerprint_author_and_prefix():
    rec1 = {
        "source": "Quotes to Scrape",
        "author": "Albert Einstein",
        "name_or_title": "The world as we have created it is a process of our thinking. Extra text 1.",
    }
    rec2 = {
        "source": "Quotes to Scrape",
        "author": "albert einstein",
        "name_or_title": "the world as we have created it is a process of our thinking! Extra text 2.",
    }
    rec3 = {
        "source": "Quotes to Scrape",
        "author": "Jane Austen",
        "name_or_title": "The person, be it gentleman or lady, who has not pleasure in a good novel...",
    }

    fp1 = make_fingerprint(rec1)
    fp2 = make_fingerprint(rec2)
    fp3 = make_fingerprint(rec3)

    # First 50 chars match after normalization
    assert fp1 == fp2
    assert fp1 != fp3


def test_duplicates_flag_only_mode():
    base = {"source": "Books to Scrape", "author": None, "source_url": "https://books.toscrape.com/1"}
    records = [
        {**base, "name_or_title": "Unique Book"},
        {**base, "name_or_title": "Unique Book"},
    ]

    all_recs, dupes, counts = deduplicate_records(records, flag_only=True)
    assert len(all_recs) == 2
    assert len(dupes) == 1
    assert all_recs[0]["is_duplicate"] is False
    assert all_recs[1]["is_duplicate"] is True
