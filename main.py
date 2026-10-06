"""
Main Pipeline Entry Point
Multi-Source Web Scraping & Data Consolidation Pipeline

Executes the complete ETL workflow:
Scrape (Books & Quotes) -> Clean -> Validate -> Deduplicate -> Consolidate -> Export
"""

import argparse
import csv
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

from processing.cleaning import clean_record
from processing.deduplication import deduplicate_records
from processing.validation import validate_records
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

CSV_FIELDS = [
    "source",
    "name_or_title",
    "category",
    "price",
    "rating",
    "author",
    "tags",
    "description",
    "source_url",
    "scraped_at",
]


def setup_logging(log_file: Path) -> logging.Logger:
    """Configures simultaneous logging to console and a UTF-8 log file."""
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers to prevent duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (UTF-8 encoding)
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def parse_arguments() -> argparse.Namespace:
    """Defines and parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-Source Web Scraping & Data Consolidation Pipeline"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Polite delay between HTTP requests in seconds (default: 0.5)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP request timeout in seconds (default: 10.0)",
    )
    parser.add_argument(
        "--max-pages-books",
        type=int,
        default=None,
        help="Optional maximum number of pages to scrape for Books to Scrape",
    )
    parser.add_argument(
        "--max-pages-quotes",
        type=int,
        default=None,
        help="Optional maximum number of pages to scrape for Quotes to Scrape",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save final dataset and summary report (default: output)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="logs/scraper.log",
        help="Path for log file (default: logs/scraper.log)",
    )
    parser.add_argument(
        "--skip-books",
        action="store_true",
        help="Skip scraping Books to Scrape",
    )
    parser.add_argument(
        "--skip-quotes",
        action="store_true",
        help="Skip scraping Quotes to Scrape",
    )
    parser.add_argument(
        "--keep-duplicates",
        action="store_true",
        help="Retain duplicates in final output with an 'is_duplicate' flag instead of filtering them out",
    )
    return parser.parse_args()


def export_csv(records: List[Dict[str, Any]], output_path: Path, include_duplicate_flag: bool = False) -> None:
    """Writes consolidated records to a standard CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(CSV_FIELDS)
    if include_duplicate_flag and "is_duplicate" not in fieldnames:
        fieldnames.append("is_duplicate")

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in records:
            # Map None values to empty strings for clean CSV representation
            sanitized_row = {
                k: ("" if row.get(k) is None else row.get(k)) for k in fieldnames
            }
            writer.writerow(sanitized_row)


def export_summary(summary_data: Dict[str, Any], output_path: Path) -> None:
    """Writes execution summary metrics to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, mode="w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=4, ensure_ascii=False)


def run_pipeline(args: argparse.Namespace) -> None:
    """Executes the full end-to-end web scraping and consolidation pipeline."""
    output_dir = Path(args.output_dir)
    log_file = Path(args.log_file)
    logger = setup_logging(log_file)

    start_dt = datetime.now(timezone.utc)
    start_perf = time.perf_counter()

    logger.info("=" * 60)
    logger.info("Multi-Source Web Scraping & Data Consolidation Pipeline")
    logger.info("Started at: %s", start_dt.isoformat())
    logger.info("Configuration: delay=%.2fs, timeout=%.1fs", args.delay, args.timeout)
    logger.info("=" * 60)

    # 1. SCRAPING STAGE
    raw_records_by_source: Dict[str, List[dict]] = {
        "Books to Scrape": [],
        "Quotes to Scrape": [],
    }

    # Books Scraper
    if not args.skip_books:
        try:
            logger.info("--- Stage 1A: Scraping Books to Scrape ---")
            books_scraper = BooksScraper(
                delay=args.delay,
                timeout=args.timeout,
                max_pages=args.max_pages_books,
            )
            raw_books = books_scraper.scrape()
            raw_records_by_source["Books to Scrape"] = raw_books
            logger.info("Successfully scraped %d books.", len(raw_books))
        except Exception as exc:
            logger.error("Failed scraping Books to Scrape: %s", exc, exc_info=True)
    else:
        logger.info("Skipping Books to Scrape as requested.")

    # Quotes Scraper
    if not args.skip_quotes:
        try:
            logger.info("--- Stage 1B: Scraping Quotes to Scrape ---")
            quotes_scraper = QuotesScraper(
                delay=args.delay,
                timeout=args.timeout,
                max_pages=args.max_pages_quotes,
            )
            raw_quotes = quotes_scraper.scrape()
            raw_records_by_source["Quotes to Scrape"] = raw_quotes
            logger.info("Successfully scraped %d quotes.", len(raw_quotes))
        except Exception as exc:
            logger.error("Failed scraping Quotes to Scrape: %s", exc, exc_info=True)
    else:
        logger.info("Skipping Quotes to Scrape as requested.")

    all_raw_records: List[dict] = []
    for records in raw_records_by_source.values():
        all_raw_records.extend(records)

    raw_count_books = len(raw_records_by_source["Books to Scrape"])
    raw_count_quotes = len(raw_records_by_source["Quotes to Scrape"])
    total_raw = len(all_raw_records)

    logger.info("Scraping complete. Total raw records collected: %d", total_raw)

    # 2. CLEANING & STANDARDIZATION STAGE
    logger.info("--- Stage 2: Cleaning & Normalization ---")
    cleaned_records: List[dict] = []
    cleaned_by_source: Dict[str, int] = {"Books to Scrape": 0, "Quotes to Scrape": 0}

    for raw_rec in all_raw_records:
        cleaned = clean_record(raw_rec)
        cleaned_records.append(cleaned)
        src = cleaned.get("source", "Unknown")
        cleaned_by_source[src] = cleaned_by_source.get(src, 0) + 1

    logger.info("Cleaning complete. Cleaned %d records.", len(cleaned_records))

    # 3. VALIDATION STAGE
    logger.info("--- Stage 3: Data Validation ---")
    valid_records, rejected_records, reason_counts = validate_records(cleaned_records)
    logger.info(
        "Validation complete. Valid: %d, Rejected: %d",
        len(valid_records),
        len(rejected_records),
    )

    # 4. DEDUPLICATION STAGE
    logger.info("--- Stage 4: Duplicate Detection ---")
    final_records, duplicates, dup_counts = deduplicate_records(
        valid_records,
        flag_only=args.keep_duplicates,
    )
    total_duplicates = len(duplicates)
    logger.info(
        "Deduplication complete. Duplicates detected: %d (Keep-duplicates flag: %s).",
        total_duplicates,
        args.keep_duplicates,
    )

    # 5. CONSOLIDATION & OUTPUT STAGE
    logger.info("--- Stage 5: Consolidation & Export ---")
    csv_file = output_dir / "final_dataset.csv"
    export_csv(final_records, csv_file, include_duplicate_flag=args.keep_duplicates)
    logger.info("Exported consolidated dataset to: %s", csv_file)

    end_dt = datetime.now(timezone.utc)
    duration = round(time.perf_counter() - start_perf, 2)

    # Summary Report Compilation
    final_by_source: Dict[str, int] = {}
    for r in final_records:
        src = r.get("source", "Unknown")
        final_by_source[src] = final_by_source.get(src, 0) + 1

    is_reconciled = (
        len(final_records) == (total_raw - len(rejected_records) - (0 if args.keep_duplicates else total_duplicates))
    )

    summary_data = {
        "execution_metadata": {
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "duration_seconds": duration,
            "python_version": sys.version.split()[0],
            "settings": {
                "delay_seconds": args.delay,
                "timeout_seconds": args.timeout,
                "keep_duplicates_flagged": args.keep_duplicates,
            },
        },
        "raw_collected_per_source": {
            "Books to Scrape": raw_count_books,
            "Quotes to Scrape": raw_count_quotes,
            "total": total_raw,
        },
        "cleaned_records_per_source": {
            "Books to Scrape": cleaned_by_source.get("Books to Scrape", 0),
            "Quotes to Scrape": cleaned_by_source.get("Quotes to Scrape", 0),
            "total": len(cleaned_records),
        },
        "rejected_records": {
            "total_rejected": len(rejected_records),
            "by_reason": reason_counts,
        },
        "duplicates_detected": {
            "total_duplicates": total_duplicates,
            "by_source": {
                "Books to Scrape": dup_counts.get("Books to Scrape", 0),
                "Quotes to Scrape": dup_counts.get("Quotes to Scrape", 0),
            },
            "strategy": "flagged_in_dataset" if args.keep_duplicates else "filtered_out",
        },
        "final_dataset": {
            "total_records": len(final_records),
            "by_source": final_by_source,
            "output_csv": str(csv_file),
        },
        "reconciliation": {
            "total_raw": total_raw,
            "total_rejected": len(rejected_records),
            "total_duplicates": total_duplicates if not args.keep_duplicates else 0,
            "final_record_count": len(final_records),
            "is_reconciled": is_reconciled,
        },
    }

    json_file = output_dir / "summary_report.json"
    export_summary(summary_data, json_file)
    logger.info("Exported summary report to: %s", json_file)

    # Print summary to console
    print("\n" + "=" * 60)
    print("PIPELINE EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Total Raw Collected   : {total_raw} (Books: {raw_count_books}, Quotes: {raw_count_quotes})")
    print(f"Total Cleaned         : {len(cleaned_records)}")
    print(f"Rejected (Validation) : {len(rejected_records)} {reason_counts if reason_counts else ''}")
    print(f"Duplicates Detected   : {total_duplicates} (Action: {'Flagged' if args.keep_duplicates else 'Removed'})")
    print(f"Final Dataset Records : {len(final_records)}")
    print(f"Counts Reconciled     : {is_reconciled}")
    print(f"Total Duration        : {duration} seconds")
    print(f"Final CSV             : {csv_file.resolve()}")
    print(f"Summary JSON          : {json_file.resolve()}")
    print(f"Execution Log         : {log_file.resolve()}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    cli_args = parse_arguments()
    run_pipeline(cli_args)
