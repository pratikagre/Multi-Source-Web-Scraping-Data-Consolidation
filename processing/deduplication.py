"""
Duplicate Detection Module
Implements fuzzy/normalized fingerprint hashing to identify duplicate records
across varying casing, punctuation, and whitespace differences.
"""

import hashlib
import logging
import re
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


def make_fingerprint(rec: dict) -> str:
    """
    Constructs a deterministic SHA-256 fingerprint for a record.
    Normalization steps:
    1. Select domain-specific identifying fields:
       - Books to Scrape: source + name_or_title
       - Quotes to Scrape: source + author + first 50 chars of quote
    2. Convert to lowercase
    3. Strip all punctuation (retain only alphanumeric characters and whitespace)
    4. Collapse contiguous whitespace into single spaces
    5. Compute SHA-256 hex digest
    """
    source = rec.get("source") or ""
    title = rec.get("name_or_title") or ""

    if source == "Books to Scrape":
        key = f"{source} {title}"
    else:
        # Quotes: identify by author and the opening 50 characters of quote text
        author = rec.get("author") or ""
        key = f"{source} {author} {title[:50]}"

    # Lowercase & strip punctuation
    normalized_key = re.sub(r"[^\w\s]", "", key.lower())
    # Collapse multiple whitespaces
    normalized_key = " ".join(normalized_key.split())

    return hashlib.sha256(normalized_key.encode("utf-8")).hexdigest()


def deduplicate_records(
    records: List[dict],
    flag_only: bool = False,
) -> Tuple[List[dict], List[dict], Dict[str, int]]:
    """
    Identifies duplicate records in the dataset.

    Args:
        records: List of validated records.
        flag_only: If True, all records are returned with an 'is_duplicate' boolean flag.
                   If False (default), duplicates are filtered out, returning only unique records.

    Returns:
        Tuple of (output_records, duplicate_records, dup_counts_by_source)
    """
    seen_fingerprints: Set[str] = set()
    unique_records: List[dict] = []
    duplicate_records: List[dict] = []
    dup_counts_by_source: Dict[str, int] = {}

    for rec in records:
        fp = make_fingerprint(rec)
        source = rec.get("source", "Unknown")

        if fp in seen_fingerprints:
            duplicate_records.append(rec)
            dup_counts_by_source[source] = dup_counts_by_source.get(source, 0) + 1
            logger.info(
                "Duplicate detected in [%s]: %s",
                source,
                (rec.get("name_or_title") or "")[:40],
            )
            if flag_only:
                rec_copy = dict(rec)
                rec_copy["is_duplicate"] = True
                unique_records.append(rec_copy)
        else:
            seen_fingerprints.add(fp)
            if flag_only:
                rec_copy = dict(rec)
                rec_copy["is_duplicate"] = False
                unique_records.append(rec_copy)
            else:
                unique_records.append(rec)

    return unique_records, duplicate_records, dup_counts_by_source
