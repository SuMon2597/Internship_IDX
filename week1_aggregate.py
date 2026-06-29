# =============================================================================
# Week 1 – Monthly Dataset Aggregation
# IDX Exchange | Data Analyst Internship
#
# Concatenates all monthly CRMLS files from January 2024 through the most
# recently completed calendar month into two combined datasets, then filters
# both to PropertyType == 'Residential' only.
#
# Outputs:
#   - Combined_Listing.csv
#   - Combined_Sold.csv
# =============================================================================

import pandas as pd
import glob

# ── CONFIG: update these paths to match your folder structure ─────────────────
LISTING_DIR  = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\Week1\Listing"   # folder with CRMLSListing*.csv files
SOLD_DIR     = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\Week1\Sold"      # folder with CRMLSSold*.csv file
OUTPUT_DIR   = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\Week1"           # where to save the combined CSVs
# ─────────────────────────────────────────────────────────────────────────────


# =============================================================================
# LISTING
# =============================================================================

listing_files = glob.glob(LISTING_DIR + r"\CRMLSListing*.csv")
print(f"Found {len(listing_files)} Listing files")

# Read each monthly file and print its individual row count BEFORE concatenation
listing_frames = []
for f in listing_files:
    df = pd.read_csv(f, dtype=str, low_memory=False)
    print(f"  {f.split(chr(92))[-1]}: {len(df):,} rows")
    listing_frames.append(df)

# Concatenate all monthly files
combined_listing = pd.concat(listing_frames, axis=0, join="outer", ignore_index=True)
print(f"\nRow count AFTER  concatenation       (Listing): {len(combined_listing):,}")

# Filter to Residential only
print(f"Row count BEFORE Residential filter  (Listing): {len(combined_listing):,}")
combined_listing = combined_listing[combined_listing["PropertyType"] == "Residential"]
print(f"Row count AFTER  Residential filter  (Listing): {len(combined_listing):,}")

# Save
listing_output = OUTPUT_DIR + r"\Combined_Listing.csv"
combined_listing.to_csv(listing_output, index=False)
print(f"Saved → {listing_output}\n")


# =============================================================================
# SOLD
# =============================================================================

sold_files = glob.glob(SOLD_DIR + r"\CRMLSSold*.csv")
print(f"Found {len(sold_files)} Sold files")

# Read each monthly file and print its individual row count BEFORE concatenation
sold_frames = []
for f in sold_files:
    df = pd.read_csv(f, dtype=str, low_memory=False)
    print(f"  {f.split(chr(92))[-1]}: {len(df):,} rows")
    sold_frames.append(df)

# Concatenate all monthly files
combined_sold = pd.concat(sold_frames, axis=0, join="outer", ignore_index=True)
print(f"\nRow count AFTER  concatenation       (Sold): {len(combined_sold):,}")

# Filter to Residential only
print(f"Row count BEFORE Residential filter  (Sold): {len(combined_sold):,}")
combined_sold = combined_sold[combined_sold["PropertyType"] == "Residential"]
print(f"Row count AFTER  Residential filter  (Sold): {len(combined_sold):,}")

# Save
sold_output = OUTPUT_DIR + r"\Combined_Sold.csv"
combined_sold.to_csv(sold_output, index=False)
print(f"Saved → {sold_output}\n")

print("Done! Two combined CSVs created successfully.")