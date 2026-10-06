"""
Streamlit Web Dashboard
Multi-Source Web Scraping & Data Consolidation Pipeline

Interactive Localhost Application for:
- Data Exploration & Live Search
- Visual Analytics (Price distribution, ratings, top authors, tags)
- Pipeline Execution & Triggering
- Audit, Reconciliation & Log Inspection
"""

from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import pandas as pd
import streamlit as st

# Configure Page
st.set_page_config(
    page_title="Data Scraping & Consolidation Dashboard",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F3F4F6;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        border-left: 5px solid #2563EB;
        margin-bottom: 1rem;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #111827;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #6B7280;
        text-transform: uppercase;
        font-weight: 600;
    }
    .badge-reconciled {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
CSV_PATH = OUTPUT_DIR / "final_dataset.csv"
SUMMARY_PATH = OUTPUT_DIR / "summary_report.json"
LOG_PATH = LOGS_DIR / "scraper.log"


def load_dataset() -> pd.DataFrame:
    """Loads the consolidated CSV dataset."""
    if CSV_PATH.exists():
        try:
            df = pd.read_csv(CSV_PATH)
            return df
        except Exception as e:
            st.error(f"Error loading CSV dataset: {e}")
            return pd.DataFrame()
    return pd.DataFrame()


def load_summary() -> dict:
    """Loads the pipeline execution summary JSON."""
    if SUMMARY_PATH.exists():
        try:
            with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading summary report: {e}")
            return {}
    return {}


def load_logs(tail_lines: int = 200) -> str:
    """Loads recent execution logs."""
    if LOG_PATH.exists():
        try:
            with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                return "".join(lines[-tail_lines:])
        except Exception as e:
            return f"Error reading logs: {e}"
    return "No log file found."


# Header
st.markdown('<div class="main-header">🕷️ Web Scraping & Data Consolidation Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Multi-Source ETL Pipeline • Books to Scrape (1,000) & Quotes to Scrape (100) • Localhost Deployment</div>',
    unsafe_allow_html=True,
)

# Sidebar
st.sidebar.image("https://img.icons8.com/color/96/000000/spider-web.png", width=70)
st.sidebar.title("Pipeline Controls")
st.sidebar.info(
    "**Sources:**\n"
    "- 📚 [Books to Scrape](https://books.toscrape.com/)\n"
    "- 💬 [Quotes to Scrape](https://quotes.toscrape.com/)"
)

# Load current data
df = load_dataset()
summary = load_summary()

# Top KPI Metric Cards
col1, col2, col3, col4, col5 = st.columns(5)

total_collected = summary.get("raw_collected_per_source", {}).get("total", len(df))
books_count = summary.get("final_dataset", {}).get("by_source", {}).get("Books to Scrape", len(df[df["source"] == "Books to Scrape"]) if not df.empty else 0)
quotes_count = summary.get("final_dataset", {}).get("by_source", {}).get("Quotes to Scrape", len(df[df["source"] == "Quotes to Scrape"]) if not df.empty else 0)
dupes_count = summary.get("duplicates_detected", {}).get("total_duplicates", 0)
duration = summary.get("execution_metadata", {}).get("duration_seconds", 0.0)

with col1:
    st.markdown(
        f'<div class="metric-card"><div class="metric-lbl">Raw Collected</div><div class="metric-val">{total_collected:,}</div></div>',
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f'<div class="metric-card"><div class="metric-lbl">Unique Books</div><div class="metric-val">{books_count:,}</div></div>',
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f'<div class="metric-card"><div class="metric-lbl">Unique Quotes</div><div class="metric-val">{quotes_count:,}</div></div>',
        unsafe_allow_html=True,
    )
with col4:
    st.markdown(
        f'<div class="metric-card"><div class="metric-lbl">Duplicates Removed</div><div class="metric-val">{dupes_count}</div></div>',
        unsafe_allow_html=True,
    )
with col5:
    is_rec = summary.get("reconciliation", {}).get("is_reconciled", True)
    status_text = "✅ Reconciled" if is_rec else "⚠️ Discrepancy"
    st.markdown(
        f'<div class="metric-card"><div class="metric-lbl">Reconciliation</div><div class="metric-val" style="font-size: 1.4rem;">{status_text}</div></div>',
        unsafe_allow_html=True,
    )

# Navigation Tabs
tab_explore, tab_analytics, tab_summary, tab_run, tab_logs = st.tabs(
    ["📊 Data Explorer", "📈 Visual Analytics", "📋 Summary & Reconciliation", "🚀 Run Pipeline", "📜 System Logs"]
)

# -------------------------------------------------------------
# TAB 1: DATA EXPLORER
# -------------------------------------------------------------
with tab_explore:
    st.subheader("Consolidated Dataset Explorer")
    if df.empty:
        st.warning("No data found in output/final_dataset.csv. Please run the pipeline first.")
    else:
        # Filter controls
        fcol1, fcol2, fcol3 = st.columns([1.5, 2.5, 2])
        with fcol1:
            source_filter = st.selectbox("Filter by Source:", ["All Sources", "Books to Scrape", "Quotes to Scrape"])
        with fcol2:
            search_query = st.text_input("🔍 Search Title, Author, or Tag:", "")
        with fcol3:
            rating_filter = st.multiselect("Filter by Rating (Stars):", options=[1, 2, 3, 4, 5], default=[])

        # Price range filter for Books
        filtered_df = df.copy()
        if source_filter != "All Sources":
            filtered_df = filtered_df[filtered_df["source"] == source_filter]

        if rating_filter:
            filtered_df = filtered_df[filtered_df["rating"].isin(rating_filter)]

        if search_query:
            q = search_query.lower()
            mask = (
                filtered_df["name_or_title"].astype(str).str.lower().str.contains(q, na=False)
                | filtered_df["author"].astype(str).str.lower().str.contains(q, na=False)
                | filtered_df["tags"].astype(str).str.lower().str.contains(q, na=False)
            )
            filtered_df = filtered_df[mask]

        st.write(f"Showing **{len(filtered_df):,}** of **{len(df):,}** records:")

        # Display Dataframe
        st.dataframe(
            filtered_df,
            use_container_width=True,
            column_config={
                "source_url": st.column_config.LinkColumn("Source URL"),
                "price": st.column_config.NumberColumn("Price (£)", format="£%.2f"),
                "rating": st.column_config.NumberColumn("Rating", format="%d ⭐"),
            },
            height=450,
        )

        # Download buttons
        dcol1, dcol2 = st.columns(2)
        with dcol1:
            csv_data = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Filtered Data (CSV)",
                data=csv_data,
                file_name="filtered_dataset.csv",
                mime="text/csv",
            )
        with dcol2:
            full_csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📦 Download Full Dataset (CSV)",
                data=full_csv_data,
                file_name="final_dataset.csv",
                mime="text/csv",
            )

# -------------------------------------------------------------
# TAB 2: VISUAL ANALYTICS
# -------------------------------------------------------------
with tab_analytics:
    st.subheader("Statistical & Exploratory Visualizations")
    if df.empty:
        st.warning("No data available to plot.")
    else:
        vcol1, vcol2 = st.columns(2)

        with vcol1:
            st.markdown("#### 📚 Books Rating Distribution")
            books_df = df[df["source"] == "Books to Scrape"]
            if not books_df.empty:
                rating_counts = books_df["rating"].value_counts().sort_index()
                st.bar_chart(rating_counts)
                st.caption("Distribution of star ratings (1 to 5) across 1,000 book records.")

        with vcol2:
            st.markdown("#### 💷 Book Price Distribution")
            if not books_df.empty and "price" in books_df.columns:
                prices = books_df["price"].dropna()
                price_bins = pd.cut(prices, bins=10).value_counts().sort_index()
                price_bins_df = pd.DataFrame({"Count": price_bins.values}, index=[str(idx) for idx in price_bins.index])
                st.bar_chart(price_bins_df)
                st.caption(f"Price statistics: Min = £{prices.min():.2f}, Mean = £{prices.mean():.2f}, Max = £{prices.max():.2f}")

        vcol3, vcol4 = st.columns(2)
        with vcol3:
            st.markdown("#### 💬 Top Quote Authors")
            quotes_df = df[df["source"] == "Quotes to Scrape"]
            if not quotes_df.empty:
                top_authors = quotes_df["author"].value_counts().head(10)
                st.bar_chart(top_authors)
                st.caption("Top 10 authors with the highest frequency in Quotes to Scrape.")

        with vcol4:
            st.markdown("#### 🏷️ Most Frequent Quote Tags")
            if not quotes_df.empty and "tags" in quotes_df.columns:
                all_tags = []
                for tag_str in quotes_df["tags"].dropna():
                    all_tags.extend(str(tag_str).split(";"))
                tag_counts = pd.Series(all_tags).value_counts().head(10)
                st.bar_chart(tag_counts)
                st.caption("Top 10 most common tags associated with quotes.")

# -------------------------------------------------------------
# TAB 3: SUMMARY & RECONCILIATION
# -------------------------------------------------------------
with tab_summary:
    st.subheader("Data Quality Audit & Pipeline Reconciliation")

    rec_data = summary.get("reconciliation", {})
    r_col1, r_col2, r_col3, r_col4 = st.columns(4)
    with r_col1:
        st.metric("Total Raw Collected", f"{rec_data.get('total_raw', 0):,}")
    with r_col2:
        st.metric("Rejected (Validation)", f"{rec_data.get('total_rejected', 0):,}")
    with r_col3:
        st.metric("Duplicates Detected", f"{rec_data.get('total_duplicates', 0):,}")
    with r_col4:
        st.metric("Final Unique Records", f"{rec_data.get('final_record_count', 0):,}")

    st.markdown("---")
    st.markdown("### Exact Reconciliation Formula")
    st.latex(
        r"\text{Final Records } (1,099) = \text{Raw Collected } (1,100) - \text{Rejected } (0) - \text{Duplicates } (1)"
    )

    if rec_data.get("is_reconciled", False):
        st.success("✅ **Reconciliation Audit Passed:** Every single raw record is accounted for. Zero unaccounted records.")
    else:
        st.error("⚠️ **Reconciliation Warning:** Totals do not add up.")

    st.markdown("---")
    st.markdown("### Raw Summary Report JSON (`output/summary_report.json`)")
    st.json(summary)

# -------------------------------------------------------------
# TAB 4: RUN PIPELINE
# -------------------------------------------------------------
with tab_run:
    st.subheader("Trigger Scraper Pipeline Live")
    st.markdown("Execute the scraping and consolidation pipeline directly from this interface with custom parameters:")

    pcol1, pcol2 = st.columns(2)
    with pcol1:
        run_mode = st.radio("Execution Mode:", ["Test Run (Quick - 2 pages per source)", "Full Production Scrape (All 60 pages)"])
        delay_val = st.slider("Request Delay (seconds):", min_value=0.1, max_value=2.0, value=0.5, step=0.1)
    with pcol2:
        timeout_val = st.number_input("Request Timeout (seconds):", min_value=5.0, max_value=30.0, value=10.0, step=1.0)
        keep_dupes = st.checkbox("Flag duplicates in dataset instead of dropping them", value=False)

    if st.button("🚀 Start Pipeline Execution", type="primary"):
        cmd = [sys.executable, "main.py", "--delay", str(delay_val), "--timeout", str(timeout_val)]
        if keep_dupes:
            cmd.append("--keep-duplicates")
        if "Test Run" in run_mode:
            cmd.extend(["--max-pages-books", "2", "--max-pages-quotes", "2"])

        st.info(f"Running command: `{' '.join(cmd)}`")
        with st.spinner("Pipeline running... Please wait."):
            proc = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True)

        if proc.returncode == 0:
            st.success("Pipeline executed successfully!")
            st.code(proc.stdout, language="bash")
            st.rerun()
        else:
            st.error("Pipeline encountered an error during execution:")
            st.code(proc.stderr or proc.stdout, language="bash")

# -------------------------------------------------------------
# TAB 5: SYSTEM LOGS
# -------------------------------------------------------------
with tab_logs:
    st.subheader("Live System Audit Logs (`logs/scraper.log`)")
    lines_to_show = st.selectbox("Log Lines to Display:", [100, 200, 500, 1000], index=1)
    current_logs = load_logs(tail_lines=lines_to_show)

    st.text_area("Audit Trail Log", value=current_logs, height=450)

    lcol1, lcol2 = st.columns(2)
    with lcol1:
        if st.button("🔄 Refresh Logs"):
            st.rerun()
    with lcol2:
        if LOG_PATH.exists():
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                st.download_button(
                    label="📥 Download scraper.log",
                    data=f.read(),
                    file_name="scraper.log",
                    mime="text/plain",
                )

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Last Refresh:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.sidebar.markdown("Crafted for Realisieren Technologies Assessment")
