# =============================================================================
# Weeks 4-5 - Data Cleaning and Preparation
# IDX Exchange | Data Analyst Internship
#
# Reads the Week 2-3 mortgage-enriched outputs (Sold_With_Rates.csv /
# Listing_With_Rates.csv) and prepares an analysis-ready dataset per dataset:
#
#   - Converts date fields to proper datetime
#   - Drops reviewed redundant/unnecessary columns (see COLUMNS_TO_DROP below)
#   - Reports missing values (core fields are kept even if partially missing,
#     per Weeks 2-3 guidance - no columns are dropped here for missingness
#     alone)
#   - Ensures numeric fields are properly typed
#   - FLAGS (does not delete) invalid numeric values: ClosePrice <= 0,
#     LivingArea <= 0, DaysOnMarket < 0, negative Bedrooms/Bathrooms
#   - Flags date-order violations: listing_after_close_flag,
#     purchase_after_close_flag, negative_timeline_flag
#   - Flags geographic issues: missing coordinates, 0/0 sentinel values,
#     positive Longitude (CA should be negative), out-of-state/implausible
#     coordinates
#
# Nothing is deleted from the saved output based on these flags - flagging
# preserves every record while making bad data visible, consistent with the
# non-destructive approach used in Weeks 2-3. Actual removal is a decision
# for a later phase (e.g. Week 7 outlier handling), not this script.
#
# Outputs (per dataset):
#   {name}_row_counts.csv              -> before/after row counts
#   {name}_dtype_confirmation.csv      -> dtype of every column after typing
#   {name}_date_consistency_flags.csv  -> counts for each date-order flag
#   {name}_geographic_quality.csv      -> counts for each geographic flag
#   {name}_Cleaned.csv                 -> the analysis-ready dataset (flagged,
#                                          not filtered)
# =============================================================================

import pandas as pd
import os

INPUT_DIR = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\IDX Intern\Week2-3\mortage enrichment files"
OUTPUT_DIR = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\IDX Intern\Week4-5"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Columns to drop as "unnecessary or redundant" ───────────────────────────
# Review {name}_field_categories.csv from Weeks 2-3 first. Anything flagged
# "metadata" there (system keys, timestamps, media URLs, etc.) is a
# candidate. Fill this in AFTER reviewing your actual columns - left empty
# by default so nothing is dropped without a deliberate decision.
COLUMNS_TO_DROP = [
    # "ListingKey", "ListOfficeKey", "PhotosURL", "VirtualTourURLUnbranded",
]

# All date fields named in the handbook. Not every dataset has every field
# (Listings typically won't have CloseDate/PurchaseContractDate) - each is
# only converted/used if present in that specific dataset.
DATE_FIELDS = ["CloseDate", "PurchaseContractDate", "ListingContractDate",
               "ContractStatusChangeDate"]

NUMERIC_FIELDS = ["ClosePrice", "ListPrice", "OriginalListPrice", "LivingArea",
                   "LotSizeAcres", "BedroomsTotal", "BathroomsTotalInteger",
                   "DaysOnMarket", "YearBuilt"]

# California latitude/longitude bounds used for the "implausible coordinates"
# check - a loose bounding box, not a precise state boundary.
CA_LAT_RANGE = (32.0, 42.5)
CA_LON_RANGE = (-124.5, -114.0)


# ── Step 1: Convert date fields to datetime ─────────────────────────────────
def convert_dates(df, name):
    present = [c for c in DATE_FIELDS if c in df.columns]
    for col in present:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    print(f"\n=== {name}: Date Conversion ===")
    print(f"Converted: {present}")
    missing = [c for c in DATE_FIELDS if c not in df.columns]
    if missing:
        print(f"Not present in this dataset (skipped): {missing}")
    return df


# ── Step 2: Drop reviewed redundant columns ──────────────────────────────────
def drop_redundant_columns(df, name):
    cols_to_drop = [c for c in COLUMNS_TO_DROP if c in df.columns]
    before_cols = df.shape[1]
    df = df.drop(columns=cols_to_drop)
    print(f"\n=== {name}: Redundant Column Removal ===")
    print(f"Columns before: {before_cols}   Dropped: {cols_to_drop}   "
          f"Columns after: {df.shape[1]}")
    if not COLUMNS_TO_DROP:
        print("NOTE: COLUMNS_TO_DROP is empty - review "
              f"{name}_field_categories.csv from Weeks 2-3 and fill it in.")
    return df


# ── Step 3: Missing value handling (report only, no drops) ─────────────────
def report_missing_values(df, name):
    null_pct = (df.isnull().sum() / len(df) * 100).round(2)
    high_missing = null_pct[null_pct > 90]
    print(f"\n=== {name}: Missing Value Handling ===")
    print("Decision: core fields are retained even if partially missing "
          "(per Weeks 2-3 guidance). No columns dropped for missingness alone.")
    if high_missing.empty:
        print("No columns above 90% missing.")
    else:
        print("Columns above 90% missing (retained, but flagged for awareness):")
        print(high_missing)
    return df


# ── Step 4: Ensure numeric fields are properly typed ────────────────────────
def type_numeric_fields(df, name):
    present = [c for c in NUMERIC_FIELDS if c in df.columns]
    for col in present:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    print(f"\n=== {name}: Numeric Typing ===")
    print(f"Typed as numeric: {present}")
    return df


# ── Step 5: Flag (not remove) invalid numeric values ────────────────────────
def flag_invalid_numeric_values(df, name):
    flags_added = []

    if "ClosePrice" in df.columns:
        df["invalid_closeprice_flag"] = df["ClosePrice"] <= 0
        flags_added.append("invalid_closeprice_flag")

    if "LivingArea" in df.columns:
        df["invalid_livingarea_flag"] = df["LivingArea"] <= 0
        flags_added.append("invalid_livingarea_flag")

    if "DaysOnMarket" in df.columns:
        df["invalid_daysonmarket_flag"] = df["DaysOnMarket"] < 0
        flags_added.append("invalid_daysonmarket_flag")

    if "BedroomsTotal" in df.columns:
        df["invalid_bedrooms_flag"] = df["BedroomsTotal"] < 0
        flags_added.append("invalid_bedrooms_flag")

    if "BathroomsTotalInteger" in df.columns:
        df["invalid_bathrooms_flag"] = df["BathroomsTotalInteger"] < 0
        flags_added.append("invalid_bathrooms_flag")

    print(f"\n=== {name}: Invalid Numeric Value Flags ===")
    for flag in flags_added:
        print(f"  {flag}: {int(df[flag].sum()):,} row(s) flagged")
    return df


# ── Step 6: Date consistency flags ───────────────────────────────────────────
def date_consistency_flags(df, name):
    has_listing = "ListingContractDate" in df.columns
    has_purchase = "PurchaseContractDate" in df.columns
    has_close = "CloseDate" in df.columns

    df["listing_after_close_flag"] = (
        (df["ListingContractDate"] > df["CloseDate"])
        if has_listing and has_close else False
    )
    df["purchase_after_close_flag"] = (
        (df["PurchaseContractDate"] > df["CloseDate"])
        if has_purchase and has_close else False
    )
    df["negative_timeline_flag"] = (
        (df["ListingContractDate"] > df["PurchaseContractDate"])
        if has_listing and has_purchase else False
    )

    summary = pd.DataFrame([{
        "dataset": name,
        "listing_after_close_flag": int(df["listing_after_close_flag"].sum()),
        "purchase_after_close_flag": int(df["purchase_after_close_flag"].sum()),
        "negative_timeline_flag": int(df["negative_timeline_flag"].sum()),
        "fields_available": f"ListingContractDate={has_listing}, "
                             f"PurchaseContractDate={has_purchase}, "
                             f"CloseDate={has_close}",
    }])

    path = os.path.join(OUTPUT_DIR, f"{name}_date_consistency_flags.csv")
    summary.to_csv(path, index=False)

    print(f"\n=== {name}: Date Consistency Flags ===")
    print(summary.to_string(index=False))
    print(f"Saved -> {path}")
    return df


# ── Step 7: Geographic data checks ───────────────────────────────────────────
def geographic_checks(df, name):
    has_lat = "Latitude" in df.columns
    has_lon = "Longitude" in df.columns

    if has_lat:
        df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    if has_lon:
        df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")

    df["missing_coordinates_flag"] = (
        (df["Latitude"].isna() | df["Longitude"].isna())
        if has_lat and has_lon else True
    )
    df["sentinel_zero_flag"] = (
        ((df["Latitude"] == 0) | (df["Longitude"] == 0))
        if has_lat and has_lon else False
    )
    df["positive_longitude_flag"] = (
        (df["Longitude"] > 0) if has_lon else False
    )
    df["implausible_coordinates_flag"] = (
        (~df["Latitude"].between(*CA_LAT_RANGE) |
         ~df["Longitude"].between(*CA_LON_RANGE))
        if has_lat and has_lon else False
    )

    summary = pd.DataFrame([{
        "dataset": name,
        "missing_coordinates_flag": int(df["missing_coordinates_flag"].sum()),
        "sentinel_zero_flag": int(df["sentinel_zero_flag"].sum()),
        "positive_longitude_flag": int(df["positive_longitude_flag"].sum()),
        "implausible_coordinates_flag": int(df["implausible_coordinates_flag"].sum()),
        "fields_available": f"Latitude={has_lat}, Longitude={has_lon}",
    }])

    path = os.path.join(OUTPUT_DIR, f"{name}_geographic_quality.csv")
    summary.to_csv(path, index=False)

    print(f"\n=== {name}: Geographic Data Quality ===")
    print(summary.to_string(index=False))
    print(f"Saved -> {path}")
    return df


# ── Run the full Weeks 4-5 checklist for one dataset ────────────────────────
def run_cleaning(name, input_filename):
    print(f"\n{'=' * 70}")
    print(f"{name} DATASET")
    print(f"{'=' * 70}")

    df = pd.read_csv(os.path.join(INPUT_DIR, input_filename), dtype=str, low_memory=False)
    rows_before, cols_before = df.shape
    print(f"Loaded {rows_before:,} rows, {cols_before} columns from {input_filename}")

    df = convert_dates(df, name)
    df = drop_redundant_columns(df, name)
    df = report_missing_values(df, name)
    df = type_numeric_fields(df, name)
    df = flag_invalid_numeric_values(df, name)
    df = date_consistency_flags(df, name)
    df = geographic_checks(df, name)

    rows_after, cols_after = df.shape

    # Row/column count log
    counts = pd.DataFrame([{
        "dataset": name,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "columns_before": cols_before,
        "columns_after": cols_after,
    }])
    counts_path = os.path.join(OUTPUT_DIR, f"{name}_row_counts.csv")
    counts.to_csv(counts_path, index=False)
    print(f"\n=== {name}: Row/Column Counts ===")
    print(counts.to_string(index=False))
    print(f"Saved -> {counts_path}")

    # Dtype confirmation
    dtype_df = df.dtypes.reset_index().rename(columns={"index": "column", 0: "dtype"})
    dtype_path = os.path.join(OUTPUT_DIR, f"{name}_dtype_confirmation.csv")
    dtype_df.to_csv(dtype_path, index=False)
    print(f"Saved -> {dtype_path}")

    # Save cleaned (flagged, not filtered) dataset
    out_path = os.path.join(OUTPUT_DIR, f"{name}_Cleaned.csv")
    df.to_csv(out_path, index=False)
    print(f"\n=== {name}: Cleaned Dataset Saved ===")
    print(f"Rows: {len(df):,}   Columns: {df.shape[1]}")
    print(f"Saved -> {out_path}")


# ── Run for both datasets ───────────────────────────────────────────────────
run_cleaning("Sold", "Sold_With_Rates.csv")
run_cleaning("Listing", "Listing_With_Rates.csv")

print("\nDone! Weeks 4-5 data cleaning and preparation complete for both datasets.")
