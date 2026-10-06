# Multi-Source Web Scraping & Data Consolidation Pipeline

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Pytest%20(25%20passed)-brightgreen.svg)](tests/)

A robust, production-grade Python ETL pipeline designed to extract data from multiple heterogeneous web sources ([Books to Scrape](https://books.toscrape.com/) and [Quotes to Scrape](https://quotes.toscrape.com/)), normalize varying structural schemas into a unified data model, clean and validate fields, detect duplicates using fuzzy fingerprint hashing, and consolidate the results into an exportable dataset and summary report.

---

## 1. Architectural Overview

The pipeline implements a decoupled, multi-stage ETL (Extract, Transform, Load) architecture:

```
[Books to Scrape]  (50 pages / 1,000 books) ──┐
                                              ├──> [1. Scrape & Ingest]
[Quotes to Scrape] (10 pages / 100 quotes)  ──┘            │
                                                           ▼
                                                [2. Clean & Standardize]
                                                           │
                                                           ▼
                                                [3. Validate & Audit]
                                                           │
                                                           ▼
                                                [4. Deduplicate (SHA-256)]
                                                           │
                                                           ▼
                                                [5. Consolidate & Export]
                                                           │
                                           ┌───────────────┴───────────────┐
                                           ▼                               ▼
                               [output/final_dataset.csv]    [output/summary_report.json]
```

### Key Architectural Strengths:
1. **Separation of Concerns:** Scraper modules only handle HTTP requests and raw DOM extraction. Cleaning, validation, and deduplication modules are pure transformation functions independent of networking or file I/O.
2. **Resilience & Fault Tolerance:** Automatic retries with exponential backoff on transient HTTP status codes (`429, 500, 502, 503, 504`), graceful handling of individual record parsing failures, and complete source-level isolation so that a failure in one source does not abort the entire pipeline.
3. **Polite Web Crawling:** Configurable request throttling (`--delay 0.5s`) and realistic HTTP headers (`User-Agent`, `Accept`, `Accept-Language`).
4. **Dynamic Pagination:** Follows relative `next` page links dynamically using `urllib.parse.urljoin`, eliminating hardcoded page counts.
5. **Exact Metrics & Reconciliation:** Guarantees that every scraped record is accounted for:
   $$\text{Final Records} = \text{Raw Collected} - \text{Rejected} - \text{Duplicates}$$

---

## 2. Project Directory Structure

```
scraping_assignment/
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py        # Resilient HTTP session, retry logic, throttling, BaseScraper
│   ├── books_scraper.py       # Books to Scrape extractor & dynamic pagination
│   └── quotes_scraper.py      # Quotes to Scrape extractor & dynamic pagination
├── processing/
│   ├── __init__.py
│   ├── cleaning.py            # Pure functions: text, price, rating, tags, quote stripping, URL
│   ├── validation.py          # Data validation against constraints, reason-code auditing
│   └── deduplication.py       # SHA-256 fingerprinting & duplicate removal / flagging
├── tests/
│   ├── __init__.py
│   ├── test_cleaning.py       # Unit tests for text, price, rating, quote, URL cleaners
│   ├── test_validation.py     # Unit tests for validation rules & batch error reporting
│   ├── test_deduplication.py  # Unit tests for fingerprint normalization & duplicate detection
│   └── test_scrapers.py       # Unit tests for HTML parsers using fixture HTML (offline)
├── output/
│   ├── final_dataset.csv      # Consolidated CSV dataset (1,100 records)
│   └── summary_report.json    # Pipeline execution metrics & reconciliation statistics
├── logs/
│   └── scraper.log            # Timestamped execution log file (UTF-8)
├── main.py                    # CLI entry point orchestrating the end-to-end pipeline
├── requirements.txt           # Pinned project dependencies
├── README.md                  # Comprehensive technical documentation
└── AI_USAGE.md                # Transparency disclosure on AI tools and verification
```

---

## 3. Prerequisites & Environment Setup

### System Prerequisites
- **Operating System:** Windows, macOS, or Linux
- **Python Version:** Python 3.10, 3.11, or 3.12 (Tested on Python 3.12.4)

### Step 1: Clone or Navigate to the Project Directory
```bash
cd "Multi-Source Web Scraping & Data Consolidation"
```

### Step 2: Create and Activate a Virtual Environment
```bash
# Windows (PowerShell / Command Prompt)
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

---

## 4. How to Run the Pipeline

### Standard Execution (Scrape Both Sources End-to-End)
Runs the entire pipeline, scraping all 50 pages of Books to Scrape and 10 pages of Quotes to Scrape:
```bash
python main.py
```

### CLI Options & Custom Configuration
The pipeline includes a rich CLI built with `argparse`:

| Argument | Type | Default | Description |
|---|---|---|---|
| `--delay` | float | `0.5` | Delay in seconds between successive HTTP requests |
| `--timeout` | float | `10.0` | Request timeout threshold in seconds |
| `--max-pages-books` | int | `None` (all) | Limit the number of pages scraped for Books to Scrape |
| `--max-pages-quotes` | int | `None` (all) | Limit the number of pages scraped for Quotes to Scrape |
| `--output-dir` | string | `output` | Directory where `final_dataset.csv` and `summary_report.json` are written |
| `--log-file` | string | `logs/scraper.log` | Path to the output log file |
| `--skip-books` | flag | `False` | Skip scraping Books to Scrape |
| `--skip-quotes` | flag | `False` | Skip scraping Quotes to Scrape |
| `--keep-duplicates` | flag | `False` | Flag duplicates with an `is_duplicate` column instead of dropping them |

#### Example CLI Commands:
```bash
# Quick dry run on the first 2 pages of each source:
python main.py --max-pages-books 2 --max-pages-quotes 2

# Scrape with 1.0 second delay and keep duplicate records flagged:
python main.py --delay 1.0 --keep-duplicates

# Scrape only Quotes to Scrape:
python main.py --skip-books
```

---

## 5. Running the Test Suite

The test suite contains 25 isolated unit tests covering all data cleaning transformations, edge cases, validation rules, fingerprint normalization, and HTML parsing (using offline DOM fixtures):

```bash
pytest -v
```

Expected output:
```
tests/test_cleaning.py::test_clean_text PASSED
tests/test_cleaning.py::test_strip_quotes PASSED
tests/test_cleaning.py::test_clean_price PASSED
tests/test_cleaning.py::test_clean_rating PASSED
tests/test_cleaning.py::test_clean_tags PASSED
tests/test_cleaning.py::test_normalize_url PASSED
tests/test_cleaning.py::test_clean_record_book PASSED
tests/test_cleaning.py::test_clean_record_quote PASSED
tests/test_deduplication.py::test_fingerprint_normalization PASSED
tests/test_deduplication.py::test_duplicates_filter_mode PASSED
tests/test_deduplication.py::test_quotes_fingerprint_author_and_prefix PASSED
tests/test_deduplication.py::test_duplicates_flag_only_mode PASSED
tests/test_scrapers.py::test_parse_book PASSED
tests/test_scrapers.py::test_parse_quote PASSED
tests/test_scrapers.py::test_parse_book_missing_elements PASSED
tests/test_validation.py::test_valid_book_record PASSED
tests/test_validation.py::test_valid_quote_record PASSED
tests/test_validation.py::test_invalid_source PASSED
tests/test_validation.py::test_missing_name PASSED
tests/test_validation.py::test_invalid_url PASSED
tests/test_validation.py::test_invalid_price PASSED
tests/test_validation.py::test_missing_price_book PASSED
tests/test_validation.py::test_invalid_rating PASSED
tests/test_validation.py::test_missing_author_quote PASSED
tests/test_validation.py::test_validate_records_batch PASSED
============================= 25 passed in 0.23s ==============================
```

---

## 6. Website Exploration & Selector Findings

Before coding, both websites were inspected using browser developer tools and HTTP probe scripts:

| Feature / Field | Source 1: Books to Scrape (`https://books.toscrape.com/`) | Source 2: Quotes to Scrape (`https://quotes.toscrape.com/`) |
|---|---|---|
| **Base URL** | `https://books.toscrape.com/` | `https://quotes.toscrape.com/` |
| **Record Container** | `article.product_pod` (20 items/page, 50 pages = 1,000 items) | `div.quote` (10 items/page, 10 pages = 100 items) |
| **Title / Text** | `h3 > a` (Full title stored in `title` attribute; inner text is truncated with ellipsis `...`) | `span.text` (Inner text wrapped in typographic curly quotes `“...` and `...”`) |
| **Price** | `p.price_color` (Formatted as `£51.77`) | *Not Applicable* (`None`) |
| **Rating** | `p.star-rating` class attribute (e.g. `['star-rating', 'Three']`) | *Not Applicable* (`None`) |
| **Author** | *Not Applicable* (`None`) | `small.author` (e.g., `Albert Einstein`) |
| **Author / Detail Link** | `h3 > a[href]` (relative URL, e.g. `catalogue/a-light-in-the-attic_1000/index.html`) | `a[href*="/author/"]` (relative link to author biography page) |
| **Tags** | *Not Applicable* (`None`) | `div.tags a.tag` (Zero or more anchor tags per quote) |
| **Next Page Link** | `li.next > a` (Relative link, e.g. `catalogue/page-2.html` on page 1, `page-3.html` on page 2) | `li.next > a` (Relative link, e.g. `/page/2/`) |

---

## 7. Standardized Data Model

A unified schema was designed to cleanly represent records from both sources without inventing synthetic data:

| Column Name | Books to Scrape | Quotes to Scrape | Data Type | Example Value |
|---|---|---|---|---|
| `source` | `"Books to Scrape"` | `"Quotes to Scrape"` | `string` | `"Books to Scrape"` |
| `name_or_title` | Full Book Title | Cleaned Quote Text | `string` | `"A Light in the Attic"` |
| `category` | `None` (empty) | `None` (empty) | `string` / `null` | `""` |
| `price` | Numeric book price | `None` (empty) | `float` | `51.77` |
| `rating` | Integer star rating (1–5) | `None` (empty) | `integer` | `3` |
| `author` | `None` (empty) | Author Name | `string` | `"Albert Einstein"` |
| `tags` | `None` (empty) | Semicolon-delimited sorted tags | `string` | `"change;deep-thoughts;thinking"` |
| `description` | `None` (empty) | `None` (empty) | `string` / `null` | `""` |
| `source_url` | Full canonical product URL | Author Bio URL (or quote page) | `string` | `"https://books.toscrape.com/catalogue/..."` |
| `scraped_at` | ISO-8601 UTC Timestamp | ISO-8601 UTC Timestamp | `string` | `"2026-10-06T13:05:00Z"` |

> [!NOTE]
> In accordance with the technical assessment guidelines:
> - Listing-level scraping collects book titles, prices, ratings, URLs, and availability. Detailed categories and descriptions reside on individual product pages (~1,000 additional HTTP requests); to respect public practice server bandwidth, these are left empty and documented rather than fabricating synthetic data.
> - Quotes do not contain prices or ratings; these columns are appropriately populated with `None` / empty values.

---

## 8. Data Cleaning & Transformation Logic

Implemented in [`processing/cleaning.py`](processing/cleaning.py):
1. **Whitespace Normalization (`clean_text`):**
   - Replaces non-breaking spaces (`\xa0`) with standard spaces.
   - Collapses contiguous whitespace, newlines (`\n`), and tabs (`\t`) into a single space using `" ".join(val.split())`.
   - Strips leading and trailing padding.
2. **Quote Stripping (`strip_quotes`):**
   - Removes typographic curly quotes (`“`, `”`, `‘`, `’`) and ASCII quotes (`"`, `'`) along with boundary spaces, restoring pure quote prose.
3. **Price Conversion (`clean_price`):**
   - Uses regex `\d+(?:\.\d+)?` to extract numerical values from raw currency strings (`£51.77`, `$19.99`).
   - Converts the matched substring to an IEEE-754 `float` rounded to 2 decimal places.
4. **Rating Standardization (`clean_rating`):**
   - Maps word-based rating classes (`'One'`, `'Two'`, `'Three'`, `'Four'`, `'Five'`) to integer values (`1` to `5`).
   - Also parses numeric string digits (`'3' -> 3`).
5. **Tag Normalization (`clean_tags`):**
   - Converts tags to lowercase, trims whitespace, removes duplicates, sorts alphabetically, and joins them using a semicolon delimiter (e.g., `'change;deep-thoughts;world'`).
6. **URL Canonicalization (`normalize_url`):**
   - Resolves relative URLs using `urllib.parse.urljoin`.
   - Validates that the scheme is `http` or `https` and that a valid network location exists.

---

## 9. Validation Rules & Constraints

Implemented in [`processing/validation.py`](processing/validation.py). Each cleaned record is checked against data integrity constraints:

| Failure Reason Code | Rule Checked |
|---|---|
| `unknown_source` | `source` must be in `{"Books to Scrape", "Quotes to Scrape"}` |
| `missing_name` | `name_or_title` must not be null or blank |
| `invalid_url` | `source_url` must begin with `http://` or `https://` |
| `invalid_price` | If `price` is present, it must be numeric and $\ge 0$ |
| `missing_price` | If `source == "Books to Scrape"`, a valid price must be present |
| `invalid_rating` | If `rating` is present, it must be an integer in $\{1, 2, 3, 4, 5\}$ |
| `missing_author` | If `source == "Quotes to Scrape"`, an `author` must be present |

- Records with violations are separated from the main dataset, logged with `WARNING` level, and aggregated into `rejected_by_reason` in the summary report.

---

## 10. Duplicate Detection & Fingerprint Strategy

Implemented in [`processing/deduplication.py`](processing/deduplication.py):

### The Challenge
Exact string comparison fails when records vary by capitalization, extraneous whitespace, or trailing punctuation:
- `"Example Book Title"`
- `"  Example Book Title  "`
- `"EXAMPLE BOOK TITLE"`
- `"Example Book Title!"`

### Fingerprint Algorithm
1. **Identifier Extraction:**
   - **Books:** `source` + `name_or_title`
   - **Quotes:** `source` + `author` + `name_or_title[:50]` (first 50 characters of quote text)
2. **Canonical Normalization:**
   - Transform to lowercase: `.lower()`
   - Strip punctuation: `re.sub(r"[^\w\s]", "", key)`
   - Collapse whitespace: `" ".join(key.split())`
3. **Cryptographic Fingerprint:**
   - Compute SHA-256 hash: `hashlib.sha256(normalized.encode("utf-8")).hexdigest()`
4. **Deduplication Execution:**
   - Track seen fingerprints in a hash set.
   - First appearance is retained as `unique`; subsequent identical fingerprints are flagged or filtered out.

---

## 11. Error Handling & Reliability Strategy

- **Resilient Requests with Exponential Backoff:**
  Configured `urllib3.util.Retry` on `requests.Session` with `total=3`, `backoff_factor=1.0`, and retry status codes `(429, 500, 502, 503, 504)`.
- **Character Encoding Preservation:**
  Forces `response.encoding = response.apparent_encoding or "utf-8"` prior to accessing `.text`, preventing character corruption such as `Â£` instead of `£`.
- **Granular Error Scoping:**
  - *Record level:* Try/except wraps individual pod parsing; a malformed item is skipped without failing the page.
  - *Page level:* If a page fetch fails after all retries, the scraper logs the error and gracefully halts the source.
  - *Source level:* Scrapers run in separate try/except blocks in `main.py`; if one source is unavailable, the other still succeeds and produces a valid partial dataset.

---

## 12. Output Files & Metrics

After execution, the following artifacts are generated:

### 1. `output/final_dataset.csv`
A standardized CSV file containing:
- Cleaned book records ($1,000$ books)
- Cleaned quote records ($100$ quotes)
- Standardized columns: `source`, `name_or_title`, `category`, `price`, `rating`, `author`, `tags`, `description`, `source_url`, `scraped_at`.

### 2. `output/summary_report.json`
Comprehensive metadata documenting the entire run:
```json
{
    "execution_metadata": {
        "start_time": "2026-10-06T...",
        "end_time": "2026-10-06T...",
        "duration_seconds": 45.2,
        "python_version": "3.12.4"
    },
    "raw_collected_per_source": {
        "Books to Scrape": 1000,
        "Quotes to Scrape": 100,
        "total": 1100
    },
    "cleaned_records_per_source": {
        "Books to Scrape": 1000,
        "Quotes to Scrape": 100,
        "total": 1100
    },
    "rejected_records": {
        "total_rejected": 0,
        "by_reason": {}
    },
    "duplicates_detected": {
        "total_duplicates": 0,
        "by_source": {
            "Books to Scrape": 0,
            "Quotes to Scrape": 0
        },
        "strategy": "filtered_out"
    },
    "final_dataset": {
        "total_records": 1100,
        "by_source": {
            "Books to Scrape": 1000,
            "Quotes to Scrape": 100
        },
        "output_csv": "output\\final_dataset.csv"
    },
    "reconciliation": {
        "total_raw": 1100,
        "total_rejected": 0,
        "total_duplicates": 0,
        "final_record_count": 1100,
        "is_reconciled": true
    }
}
```

### 3. `logs/scraper.log`
Full audit trail of HTTP calls, pagination progress, record counts, and pipeline execution.

---

## 13. Assumptions & Known Limitations

1. **Category & Description Granularity:**
   Category and description for books exist only on individual book detail pages (`/catalogue/...`). Fetching them for all 1,000 books would require 1,000 additional HTTP requests (~8–10 minutes of execution time under polite crawling). To respect the public practice server, listing-level data is extracted, and category/description are left as `None` (empty in CSV).
2. **Source Data Uniqueness:**
   Both practice websites are statically curated with unique items across their pages. Consequently, standard runs on these websites yield 0 duplicates. To verify duplicate detection logic, comprehensive unit tests with synthetic duplicate fixtures are included in `tests/test_deduplication.py`.
3. **Dynamic Elements / JavaScript:**
   Both practice websites are server-rendered HTML. A lightweight `requests` + `BeautifulSoup` stack was selected over heavyweight headless browsers (Playwright/Selenium) for optimal performance and minimal memory footprint.

---

## 14. License

This project is created for educational and technical evaluation purposes.
