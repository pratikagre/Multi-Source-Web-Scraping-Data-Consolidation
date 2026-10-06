"""
Data Validation Module
Validates cleaned records against business rules and data integrity constraints.
"""

from collections import Counter
import logging
import math
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

VALID_SOURCES = {"Books to Scrape", "Quotes to Scrape"}


def validate_record(rec: dict) -> List[str]:
    """
    Validates a single cleaned record dictionary.
    Returns a list of problem strings. An empty list signifies a valid record.
    """
    problems: List[str] = []

    # 1. Source check
    source = rec.get("source")
    if source not in VALID_SOURCES:
        problems.append("unknown_source")

    # 2. Name or title presence check
    name_or_title = rec.get("name_or_title")
    if not name_or_title or not str(name_or_title).strip():
        problems.append("missing_name")

    # 3. Source URL format check
    source_url = rec.get("source_url")
    if not source_url or not str(source_url).startswith(("http://", "https://")):
        problems.append("invalid_url")

    # 4. Price check (if present, must be non-negative numeric)
    price = rec.get("price")
    if price is not None:
        if not isinstance(price, (int, float)) or math.isnan(price) or price < 0:
            problems.append("invalid_price")
    elif source == "Books to Scrape":
        # Books should have a valid price
        problems.append("missing_price")

    # 5. Rating check (if present, must be integer 1 to 5)
    rating = rec.get("rating")
    if rating is not None:
        if not isinstance(rating, int) or rating not in (1, 2, 3, 4, 5):
            problems.append("invalid_rating")

    # 6. Quotes-specific checks
    if source == "Quotes to Scrape":
        author = rec.get("author")
        if not author or not str(author).strip():
            problems.append("missing_author")

    return problems


def validate_records(
    records: List[dict],
) -> Tuple[List[dict], List[dict], Dict[str, int]]:
    """
    Validates a collection of cleaned records.
    Returns:
    - valid_records: list of passing records
    - rejected_records: list of rejected records (augmented with '_errors')
    - reason_counts: dictionary counting occurrences of each failure reason
    """
    valid_records: List[dict] = []
    rejected_records: List[dict] = []
    reason_counter: Counter = Counter()

    for rec in records:
        problems = validate_record(rec)
        if not problems:
            valid_records.append(rec)
        else:
            rec_with_errors = dict(rec)
            rec_with_errors["_validation_errors"] = problems
            rejected_records.append(rec_with_errors)
            for prob in problems:
                reason_counter[prob] += 1
            logger.warning(
                "Record rejected [%s]: %s (Title: %s)",
                rec.get("source", "Unknown"),
                problems,
                (rec.get("name_or_title") or "")[:40],
            )

    return valid_records, rejected_records, dict(reason_counter)
