# =============================================================================
# Weeks 2-3, Part 2 - Mortgage Rate Enrichment
# IDX Exchange | Data Analyst Internship
#
# Enriches both the combined Sold and Listing datasets by merging in the
# national 30-year fixed mortgage rate from the St. Louis Federal Reserve
# (FRED), joined on a monthly key.
#
# Steps (per handbook):
#   1. Fetch the MORTGAGE30US series directly from FRED
#   2. Resample weekly rates to monthly averages
#   3. Create a matching year_month key on both MLS datasets
#      (Sold keys off CloseDate, Listings key off ListingContractDate)
#   4. Merge the monthly rate onto both datasets (left join)
#   5. Validate: confirm no null rate_30yr_fixed values remain after the merge.
#      If any remain, the run FAILS LOUDLY and no output CSV is saved - this
#      guarantees a saved file never silently ships with unmatched rows.
#
# Outputs:
#   - Sold_With_Rates.csv
#   - Listing_With_Rates.csv
# =============================================================================

import pandas as pd
import os

INPUT_DIR  = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\IDX Intern\Week1"
OUTPUT_DIR = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\IDX Intern\Week2-3"

SOLD_PATH    = os.path.join(INPUT_DIR, "Combined_Sold.csv")
LISTING_PATH = os.path.join(INPUT_DIR, "Combined_Listing.csv")

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── Step 1-2: Fetch FRED data and resample weekly -> monthly averages ───────
def get_monthly_rates():
    """
    Download weekly 30-year mortgage rates from FRED and return monthly
    averages. FRED occasionally represents a missing weekly reading as a
    non-numeric placeholder (e.g. "."), so the rate column is explicitly
    coerced to numeric and any unparseable date/rate rows are dropped
    BEFORE the monthly average is computed - this prevents a single bad
    weekly value from silently distorting a month's average.
    """
    rates = pd.read_csv(FRED_URL)
    rates.columns = ["date", "rate_30yr_fixed"]

    rates["date"] = pd.to_datetime(rates["date"], errors="coerce")
    rates["rate_30yr_fixed"] = pd.to_numeric(rates["rate_30yr_fixed"], errors="coerce")

    before = len(rates)
    rates = rates.dropna(subset=["date", "rate_30yr_fixed"])
    dropped = before - len(rates)

    print(f"Step 1: Fetched {before:,} weekly observations from FRED "
          f"({rates['date'].min().date()} to {rates['date'].max().date()})")
    if dropped:
        print(f"  Dropped {dropped:,} row(s) with unparseable date/rate values")

    rates["year_month"] = rates["date"].dt.to_period("M")
    monthly = (
        rates.groupby("year_month", as_index=False)["rate_30yr_fixed"]
        .mean()
        .round({"rate_30yr_fixed": 3})
    )
    print(f"Step 2: Resampled to {len(monthly):,} monthly averages")
    return monthly


# ── Steps 3-5: Key, merge, validate, and save one dataset ───────────────────
def add_rates(name, input_path, date_column, monthly_rates, output_path):
    """
    Merge monthly mortgage rates into one MLS dataset (Sold or Listing) and
    save the result. The merge is only saved if EVERY row has a matching
    rate - if any row is missing a rate after the left join, the function
    raises an error and nothing is written to disk. This makes the
    "no null rate values after merge" validation a hard requirement rather
    than an informational warning.
    """
    data = pd.read_csv(input_path, dtype=str, low_memory=False)
    print(f"\nLoaded {name}: {len(data):,} rows, {data.shape[1]} columns")

    data[date_column] = pd.to_datetime(data[date_column], errors="coerce")
    data["year_month"] = data[date_column].dt.to_period("M")
    print(f"Step 3: year_month key created on {name} (from {date_column})")

    enriched = data.merge(monthly_rates, on="year_month", how="left")
    print(f"Step 4: Merged monthly mortgage rate onto {name} (left join)")

    missing_dates = enriched[date_column].isna().sum()
    missing_rates = enriched["rate_30yr_fixed"].isna().sum()

    print(f"\nStep 5: Validation - {name}")
    print(f"  Rows:                              {len(enriched):,}")
    print(f"  Missing/unparseable {date_column}:  {missing_dates:,}")
    print(f"  Rows without a matching rate:      {missing_rates:,}")

    if missing_rates:
        missing_months = (
            enriched.loc[enriched["rate_30yr_fixed"].isna(), "year_month"]
            .value_counts(dropna=False)
            .sort_index()
        )
        print("  Unmatched months (date outside FRED coverage or unparseable "
              f"{date_column}):")
        print(missing_months.to_string())
        raise ValueError(
            f"{name}: mortgage-rate merge has {missing_rates:,} unmatched "
            f"row(s); output was NOT saved."
        )

    print(f"  PASS: no null rate values in {name} after the merge.")

    enriched.to_csv(output_path, index=False)
    print(f"  Saved -> {output_path}")
    return enriched


# ── Run for both datasets ────────────────────────────────────────────────────
monthly_rates = get_monthly_rates()

RATES_OUT_PATH = os.path.join(OUTPUT_DIR, "week3_monthly_mortgage_rates.csv")
monthly_rates.to_csv(RATES_OUT_PATH, index=False)
print(f"Saved -> {RATES_OUT_PATH}")

sold_with_rates = add_rates(
    "Sold", SOLD_PATH, "CloseDate", monthly_rates,
    os.path.join(OUTPUT_DIR, "Sold_With_Rates.csv"),
)

listings_with_rates = add_rates(
    "Listing", LISTING_PATH, "ListingContractDate", monthly_rates,
    os.path.join(OUTPUT_DIR, "Listing_With_Rates.csv"),
)


# ── Preview ──────────────────────────────────────────────────────────────────
print("\nPreview (Sold):")
print(sold_with_rates[["CloseDate", "year_month", "ClosePrice", "rate_30yr_fixed"]].head())

print("\nPreview (Listings):")
print(listings_with_rates[["ListingContractDate", "year_month", "ListPrice", "rate_30yr_fixed"]].head())

print("\nValidation passed for both datasets: every row has a mortgage rate.")
print("Done! Weeks 2-3 Part 2 mortgage rate enrichment complete.")
