# =============================================================================
# Week 1 – Monthly Dataset Aggregation
# IDX Exchange | Data Analyst Internship
#
# Concatenates all monthly CRMLS files into two combined datasets, then
# filters both to PropertyType == 'Residential' only.
#
# Outputs:
#   - Combined_Listing.csv
#   - Combined_Sold.csv
#   - week1_aggregation_row_counts.csv
# =============================================================================

import pandas as pd
import glob
import os

LISTING_DIR = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\IDX Intern\Listing"
SOLD_DIR    = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\IDX Intern\Sold"
OUTPUT_DIR  = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\IDX Intern"


def load_files(folder, prefix):
    """Read every monthly CSV for a dataset (Listing or Sold) into one list of DataFrames.

    Handles the Sold-specific quirk where some months only have a "_filled"
    version with 2 extra trailing columns — those get trimmed so every
    file has a matching schema before concatenation.
    """
    files = glob.glob(os.path.join(folder, f"{prefix}*.csv"))
    frames, log = [], []

    for f in files:
        name = os.path.basename(f)
        is_filled = "_filled" in name
        df = pd.read_csv(f, dtype=str, low_memory=False)
        if is_filled:
            df = df.iloc[:, :-2]  # drop 2 extra columns unique to _filled files
        frames.append(df)
        log.append({"filename": name, "rows_in_file": len(df)})
        print(f"  {name}{' [filled, trimmed]' if is_filled else ''}: {len(df):,} rows")

    return frames, log


def process_dataset(name, folder, prefix, output_path):
    """Load, concatenate, and Residential-filter one dataset. Returns the row-count log."""
    print(f"\n--- {name} ---")
    frames, log = load_files(folder, prefix)

    combined = pd.concat(frames, axis=0, join="outer", ignore_index=True)
    after_concat = len(combined)

    residential = combined[combined["PropertyType"] == "Residential"].copy()
    after_filter = len(residential)

    print(f"Rows after concat: {after_concat:,}")
    print(f"Rows after Residential filter: {after_filter:,}")

    residential.to_csv(output_path, index=False)
    print(f"Saved → {output_path}")

    for row in log:
        row.update(dataset=name, rows_after_concat=after_concat, rows_after_filter=after_filter)
    return log


# ── Run for both datasets ──────────────────────────────────────────────────
listing_log = process_dataset(
    "Listing", LISTING_DIR, "CRMLSListing", os.path.join(OUTPUT_DIR, "Combined_Listing.csv")
)
sold_log = process_dataset(
    "Sold", SOLD_DIR, "CRMLSSold", os.path.join(OUTPUT_DIR, "Combined_Sold.csv")
)

# ── Save row-count log ─────────────────────────────────────────────────────
counts_path = os.path.join(OUTPUT_DIR, "week1_aggregation_row_counts.csv")
pd.DataFrame(listing_log + sold_log).to_csv(counts_path, index=False)
print(f"\nSaved → {counts_path}")
print("Done!")
