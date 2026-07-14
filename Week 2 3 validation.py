# =============================================================================
# Weeks 2-3, Part 1 - Dataset Structuring and Validation
# IDX Exchange | Data Analyst Internship
#
# Reads the Week 1 combined outputs (Combined_Listing.csv / Combined_Sold.csv)
# and covers the full Weeks 2-3 page, not just the boxed Deliverable summary:
#
# Dataset Understanding:
#   - Rows/columns + dtypes                     -> {name}_dataset_structure.csv
#   - Market analysis vs. metadata field split   -> {name}_field_categories.csv
#
# Missing Value Analysis:
#   - Null-count summary table                   -> {name}_null_count_summary.csv
#   - Columns >90% null flagged                   -> {name}_columns_over_90pct_null.csv
#
# Numeric Distribution Review (9 fields: ClosePrice, ListPrice,
# OriginalListPrice, LivingArea, LotSizeAcres, BedroomsTotal,
# BathroomsTotalInteger, DaysOnMarket, YearBuilt):
#   - Percentile summary + IQR outlier counts     -> {name}_numeric_distribution.csv
#   - Histogram + boxplot per field                -> {name}_{field}_distribution.png
#
# Deliverable box requirements (unique property types, filtering logic,
# filtered CSV):
#   - Unique property types found                 -> {name}_unique_property_types.csv
#   - The filtering logic applied                  -> {name}_filtering_logic.csv
#   - Filtered dataset saved as new CSV             -> {name}_Validated.csv
#
# No rows are dropped or modified in this script - it only *documents* the
# data (outlier flags are counted, not removed). The Residential filter was
# already applied in Week 1; the filtering-logic step here re-confirms it
# rather than re-applying it. Actual cleaning happens in Weeks 4-5.
# =============================================================================



import pandas as pd
import os

import matplotlib
matplotlib.use("Agg")  # headless backend - no display needed to save PNGs
import matplotlib.pyplot as plt

INPUT_DIR  = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\IDX Intern\Week1"
OUTPUT_DIR = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\IDX Intern\Week2-3"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# All 9 fields named in the "Numeric Distribution Review" section.
# ClosePrice, LivingArea, and DaysOnMarket (a subset of these 9) are the
# three the boxed Deliverable text calls out by name for the summary table -
# they're covered here too since they're part of this same list.
ALL_NUMERIC_FIELDS = [
    "ClosePrice", "ListPrice", "OriginalListPrice", "LivingArea",
    "LotSizeAcres", "BedroomsTotal", "BathroomsTotalInteger",
    "DaysOnMarket", "YearBuilt",
]

# Heuristic keyword lists used to split columns into "market analysis" vs.
# "metadata" fields. This is a best-effort classification based on common
# MLS/RESO field naming conventions - not an official CRMLS schema mapping.
# Review the saved {name}_field_categories.csv and manually reclassify any
# column that lands in the wrong bucket for your actual dataset.
METADATA_KEYWORDS = [
    "key", "id", "modificationtimestamp", "timestamp", "originatingsystem",
    "sourcesystem", "listagentkey", "listofficekey", "buyeragentkey",
    "buyerofficekey", "mlsstatus", "standardstatus", "photoscount",
    "photosurl", "media", "virtualtour", "internetaddressdisplay",
    "showinginstructions", "documentavailable", "buildingareasource",
    "listingcontractdate", "offmarketdate", "createdate",
]
MARKET_ANALYSIS_KEYWORDS = [
    "price", "area", "bedroom", "bathroom", "daysonmarket", "yearbuilt",
    "lotsize", "county", "city", "zip", "propertytype", "propertysubtype",
    "closedate", "purchasecontractdate", "latitude", "longitude",
    "garagespaces", "stories", "pool", "view",
]


# ── Dataset Understanding: structure summary ────────────────────────────────
def document_structure(df, name):
    rows, cols = df.shape
    dtype_df = df.dtypes.reset_index().rename(columns={"index": "column", 0: "dtype"})
    dtype_df.insert(0, "dataset", name)
    dtype_df.insert(1, "total_rows", rows)
    dtype_df.insert(2, "total_columns", cols)

    path = os.path.join(OUTPUT_DIR, f"{name}_dataset_structure.csv")
    dtype_df.to_csv(path, index=False)

    print(f"\n=== {name}: Dataset Structure ===")
    print(f"Rows: {rows:,}   Columns: {cols}")
    print(f"Saved -> {path}")
    return dtype_df


# ── Dataset Understanding: market analysis vs. metadata fields ─────────────
def categorize_fields(df, name):
    rows = []
    for col in df.columns:
        col_lower = col.lower()
        is_metadata = any(kw in col_lower for kw in METADATA_KEYWORDS)
        is_market = any(kw in col_lower for kw in MARKET_ANALYSIS_KEYWORDS)

        if is_metadata and not is_market:
            category = "metadata"
        elif is_market and not is_metadata:
            category = "market_analysis"
        elif is_market and is_metadata:
            category = "market_analysis"  # market relevance wins on overlap
        else:
            category = "uncategorized_review_manually"

        rows.append({"dataset": name, "column": col, "category": category})

    category_df = pd.DataFrame(rows)
    path = os.path.join(OUTPUT_DIR, f"{name}_field_categories.csv")
    category_df.to_csv(path, index=False)

    print(f"\n=== {name}: Market Analysis vs. Metadata Fields (heuristic) ===")
    print(category_df["category"].value_counts())
    print("NOTE: heuristic classification - review the saved CSV and "
          "manually reclassify any 'uncategorized_review_manually' columns.")
    print(f"Saved -> {path}")
    return category_df


# ── 1. Unique property types found ──────────────────────────────────────────
def document_property_types(df, name):
    counts = (
        df["PropertyType"]
        .fillna("(missing)")
        .astype(str)
        .str.strip()
        .replace("", "(blank)")
        .value_counts(dropna=False)
        .reset_index()
    )
    counts.columns = ["PropertyType", "row_count"]
    counts["row_percent"] = (counts["row_count"] / len(df) * 100).round(2)

    path = os.path.join(OUTPUT_DIR, f"{name}_unique_property_types.csv")
    counts.to_csv(path, index=False)

    print(f"\n=== {name}: Unique Property Types Found ===")
    print(counts)
    print(f"Saved -> {path}")
    return counts


# ── 2. The filtering logic applied ──────────────────────────────────────────
def document_filtering_logic(df, name):
    unique_types = df["PropertyType"].dropna().unique()
    only_residential = set(unique_types) == {"Residential"}

    summary = pd.DataFrame([{
        "dataset": name,
        "filter_applied": "PropertyType == 'Residential'",
        "filter_stage": f"Applied upstream in Week 1 (week1_aggregate.py) before "
                         f"Combined_{name}.csv was saved",
        "rows_in_this_file": len(df),
        "unique_property_types_found_here": ", ".join(sorted(unique_types)),
        "confirmed_residential_only": only_residential,
    }])

    path = os.path.join(OUTPUT_DIR, f"{name}_filtering_logic.csv")
    summary.to_csv(path, index=False)

    print(f"\n=== {name}: Filtering Logic Applied ===")
    print("Filter: PropertyType == 'Residential' (applied in Week 1, before this file existed)")
    print(f"Confirmed residential-only in this file: {only_residential}")
    if not only_residential:
        print(f"  WARNING: non-Residential rows found: {sorted(unique_types)}")
    print(f"Saved -> {path}")
    return summary


# ── 3. Null-count summary table ─────────────────────────────────────────────
def null_count_summary(df, name):
    null_counts = df.isnull().sum()
    null_pct = (null_counts / len(df) * 100).round(2)

    summary = pd.DataFrame({
        "column": null_counts.index,
        "dtype": df.dtypes.astype(str).values,
        "null_count": null_counts.values,
        "null_percent": null_pct.values,
        "non_null_count": (len(df) - null_counts).values,
    }).sort_values(by=["null_percent", "null_count"], ascending=False).reset_index(drop=True)

    path = os.path.join(OUTPUT_DIR, f"{name}_null_count_summary.csv")
    summary.to_csv(path, index=False)

    print(f"\n=== {name}: Null Count Summary (Top 10 highest-missing columns) ===")
    print(summary.head(10))
    print(f"Saved -> {path}")
    return summary


# ── 4. Missing value report: columns above 90% null ─────────────────────────
def flag_high_missing(null_summary, name):
    high_missing = null_summary[null_summary["null_percent"] > 90].copy()

    path = os.path.join(OUTPUT_DIR, f"{name}_columns_over_90pct_null.csv")
    high_missing.to_csv(path, index=False)

    print(f"\n=== {name}: Columns Above 90% Null ===")
    print("No columns above 90% missing." if high_missing.empty else high_missing)
    print(f"Saved -> {path}")
    return high_missing


# ── 5. Numeric distribution summary + IQR outlier counts (9 fields) ────────
def numeric_distribution(df, name):
    rows = []
    for col in ALL_NUMERIC_FIELDS:
        if col not in df.columns:
            rows.append({"field": col, "status": "COLUMN NOT FOUND"})
            continue

        series = pd.to_numeric(df[col], errors="coerce")
        non_null = series.dropna()

        if non_null.empty:
            rows.append({
                "field": col, "status": "NO NUMERIC VALUES",
                "count": 0, "missing_count": int(series.isna().sum()),
            })
            continue

        q1, q3 = non_null.quantile(0.25), non_null.quantile(0.75)
        iqr = q3 - q1
        lower_bound, upper_bound = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outlier_count = int(((non_null < lower_bound) | (non_null > upper_bound)).sum())

        rows.append({
            "field": col, "status": "OK",
            "count": int(non_null.count()),
            "missing_count": int(series.isna().sum()),
            "min": non_null.min(),
            "p25": q1,
            "median": non_null.median(),
            "mean": non_null.mean(),
            "p75": q3,
            "p99": non_null.quantile(0.99),
            "max": non_null.max(),
            "iqr_lower_bound": lower_bound,
            "iqr_upper_bound": upper_bound,
            "extreme_outlier_count": outlier_count,
            "extreme_outlier_pct": round(outlier_count / len(non_null) * 100, 2),
        })

    distribution = pd.DataFrame(rows)
    for col in distribution.columns:
        if col not in ["field", "status"]:
            distribution[col] = pd.to_numeric(distribution[col], errors="coerce").round(2)

    path = os.path.join(OUTPUT_DIR, f"{name}_numeric_distribution.csv")
    distribution.to_csv(path, index=False)

    print(f"\n=== {name}: Numeric Distribution Summary (with IQR outlier flags) ===")
    print(distribution)
    print(f"Saved -> {path}")
    return distribution


# ── Numeric Distribution Review: histograms + boxplots per field ───────────
def generate_distribution_plots(df, name):
    saved_paths = []
    for col in ALL_NUMERIC_FIELDS:
        if col not in df.columns:
            continue

        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if series.empty:
            continue

        # Clip to the 1st-99th percentile just for plotting so a handful of
        # extreme outliers don't flatten the whole chart - the outlier counts
        # themselves (uncapped) are already recorded in the CSV above.
        p01, p99 = series.quantile(0.01), series.quantile(0.99)
        plot_series = series[(series >= p01) & (series <= p99)]

        fig, (ax_hist, ax_box) = plt.subplots(1, 2, figsize=(10, 4))

        ax_hist.hist(plot_series, bins=40, color="#4C72B0", edgecolor="white")
        ax_hist.set_title(f"{name}: {col} - Histogram (1st-99th pct)")
        ax_hist.set_xlabel(col)
        ax_hist.set_ylabel("Count")

        ax_box.boxplot(series, vert=True)
        ax_box.set_title(f"{name}: {col} - Boxplot (full range)")
        ax_box.set_ylabel(col)

        fig.tight_layout()
        path = os.path.join(OUTPUT_DIR, f"{name}_{col}_distribution.png")
        fig.savefig(path, dpi=120)
        plt.close(fig)

        saved_paths.append(path)
        print(f"Saved -> {path}")

    return saved_paths


# ── 6. Save the filtered dataset as a new CSV ───────────────────────────────
def save_validated(df, name):
    path = os.path.join(OUTPUT_DIR, f"{name}_Validated.csv")
    df.to_csv(path, index=False)
    print(f"\n=== {name}: Filtered Dataset Saved ===")
    print(f"Rows: {len(df):,}")
    print(f"Saved -> {path}")
    return path


# ── Run the full Weeks 2-3 Part 1 checklist for one dataset ────────────────
def run_validation(name, input_filename):
    print(f"\n{'=' * 70}")
    print(f"{name} DATASET")
    print(f"{'=' * 70}")

    df = pd.read_csv(os.path.join(INPUT_DIR, input_filename), dtype=str, low_memory=False)
    print(f"Loaded {len(df):,} rows, {df.shape[1]} columns from {input_filename}")

    # Dataset Understanding
    document_structure(df, name)
    categorize_fields(df, name)

    # Deliverable box: property types + filtering logic
    document_property_types(df, name)
    document_filtering_logic(df, name)

    # Missing Value Analysis
    null_summary = null_count_summary(df, name)
    flag_high_missing(null_summary, name)

    # Numeric Distribution Review
    numeric_distribution(df, name)
    generate_distribution_plots(df, name)

    # Deliverable box: save filtered dataset
    save_validated(df, name)


# ── Run for both datasets ───────────────────────────────────────────────────
run_validation("Listing", "Combined_Listing.csv")
run_validation("Sold", "Combined_Sold.csv")

print("\nDone! Weeks 2-3 Part 1 validation complete for both Listing and Sold.")