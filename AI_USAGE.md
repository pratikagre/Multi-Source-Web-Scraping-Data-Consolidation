# AI Usage Disclosure (AI_USAGE.md)

In accordance with Section 11 of the assignment specification, this document provides a comprehensive and transparent record of AI tool usage, prompt interactions, code reviews, adjustments, and validation procedures implemented throughout this project.

---

## 1. AI Tools Used

| Tool Name | Developer / Provider | Primary Usage |
|---|---|---|
| **Google Antigravity AI Assistant** | Google DeepMind (Gemini 3.8 Flash) | Architecture planning, code drafting, unit test generation, debugging edge cases, documentation structuring |

---

## 2. Scope of AI Assistance

AI was utilized as an interactive pair programmer for:
1. **Pipeline Architecture & Design:** Formulating the 5-stage ETL workflow (Extract $\to$ Clean $\to$ Validate $\to$ Deduplicate $\to$ Consolidate).
2. **Selector Verification & DOM Inspection:** Identifying potential selector quirks (e.g. truncated book titles, curly quotes on Quotes to Scrape).
3. **Drafting Pure Cleaning Functions:** Developing regular expressions for price extraction, tag sorting, and rating mapping.
4. **Duplicate Detection Strategy:** Formulating the fingerprint normalization algorithm (lowercase, punctuation stripping, whitespace collapsing, and SHA-256 hashing).
5. **Unit Test Scaffolding:** Generating comprehensive test cases across cleaning, validation, deduplication, and parser modules.
6. **Documentation Formatting:** Structuring clear Markdown tables and setup guides for `README.md`.

---

## 3. Representative Prompts

Below are key prompts used during the development lifecycle:

### Prompt 1: Resilient HTTP Client Architecture
> *"How should I design a reusable BaseScraper class using requests.Session with urllib3.util.Retry for exponential backoff on HTTP status codes 429, 500, 502, 503, 504, including polite rate limiting and dynamic pagination using relative next links?"*

### Prompt 2: Text Normalization and Curly Quote Stripping
> *"In Quotes to Scrape, the quote text contains Unicode curly quotation marks ('“' and '”') and non-breaking spaces (\xa0). Write a Python cleaning function that collapses all whitespace, replaces \xa0 with standard spaces, and strips both curly and standard quotation marks from the start and end of the quote."*

### Prompt 3: Fuzzy Duplicate Fingerprinting
> *"Write a duplicate detection function that normalizes record identifiers across case, punctuation, and extra whitespace, generating a deterministic SHA-256 fingerprint so that 'Example Book Title', ' Example Book Title ', and 'EXAMPLE BOOK TITLE!' map to the exact same hash."*

### Prompt 4: Unit Test Suite Design
> *"Generate comprehensive pytest test cases for data cleaning and validation, testing valid records, invalid prices, missing required fields, and out-of-range ratings without relying on network requests."*

---

## 4. Key Review Decisions & Important Code Changes

The AI output was subjected to rigorous human review and code auditing. Several critical modifications and corrections were introduced:

### 1. HTTP Character Encoding Fix
- **Initial AI Output:** Used `response.text` directly without checking encoding.
- **Problem Discovered:** Requests defaulted to `ISO-8859-1` on Books to Scrape because the server response headers did not explicitly set a UTF-8 charset. This corrupted the British Pound symbol (`£`) into `Â£` or `\ufffd`.
- **Correction Made:** Explicitly set `response.encoding = response.apparent_encoding or "utf-8"` immediately upon receiving the response before accessing `.text`.

### 2. Truncated Title Attribute Fallback
- **Initial AI Output:** Extracted book titles using `link.get_text(strip=True)`.
- **Problem Discovered:** On the listing page of Books to Scrape, long titles are truncated with an ellipsis in the link text (e.g., `A Light in the ...`), whereas the complete, unclipped title is stored in the `title` attribute: `<a title="A Light in the Attic">`.
- **Correction Made:** Updated `BooksScraper.parse_book()` to read `link.get("title")` first, falling back to `link.get_text(strip=True)` only if the attribute is absent.

### 3. Avoiding Excessive Requests for Categories and Descriptions
- **Initial AI Output:** Proposed issuing an additional HTTP request for every book to fetch categories and descriptions from product detail pages.
- **Problem Discovered:** Making 1,000 supplementary requests to a public practice server would introduce significant latency (~8–10 minutes with polite delay) and place unnecessary strain on the hosting infrastructure.
- **Correction Made:** In line with the assignment guidance tip, book categories and descriptions were defined as optional (`None`) in the standardized schema, preserving bandwidth and polite scraping principles while clearly documenting the rationale.

### 4. Robust Typographic Quote Stripping
- **Initial AI Output:** Used `text.strip('"\'')`, which only removes standard ASCII quotes.
- **Problem Discovered:** Left curly quotes (`“` and `”`) intact on all scraped quotes.
- **Correction Made:** Expanded `QUOTE_STRIP_CHARS` to include `“`, `”`, `‘`, `’`, `«`, `»`, `\xa0`, and whitespace.

### 5. Strict Data Reconciliation in Summary Report
- **Initial AI Output:** Calculated totals independently in the JSON summary, which could lead to discrepancies if duplicates were flagged rather than removed.
- **Correction Made:** Built explicit reconciliation logic checking:
  $$\text{Final Count} = \text{Raw Collected} - \text{Rejected} - \text{Duplicates}$$
  Added an `is_reconciled: bool` field to the report for automated audit verification.

---

## 5. Verification & Testing Methodology

The final implementation was systematically verified through multiple layers of testing:

1. **Unit Testing:**
   - 25 automated unit tests executed via `pytest -v` across:
     - `test_cleaning.py` (text normalization, quote stripping, price regex, rating mapping, tags, URLs)
     - `test_validation.py` (business rules, error reason aggregation, fail-safe isolation)
     - `test_deduplication.py` (fingerprint hashing, duplicate detection, flag-only vs filter modes)
     - `test_scrapers.py` (HTML DOM parsing with mock HTML fixtures, testing missing tags)
2. **Live Integration Run:**
   - Executed `python main.py` against both live target sites.
   - Successfully scraped all 50 pages of Books to Scrape ($1,000$ books) and all 10 pages of Quotes to Scrape ($100$ quotes).
   - Confirmed output CSV generation (`output/final_dataset.csv`, $1,100$ records) and JSON summary (`output/summary_report.json`).
3. **Data Integrity Audit:**
   - Checked that CSV price columns contain only numeric float values or blanks.
   - Verified that ratings are integers between 1 and 5.
   - Verified that all source URLs are valid, fully-resolved HTTP/HTTPS links.
   - Confirmed the summary report math reconciles with $100\%$ accuracy.
