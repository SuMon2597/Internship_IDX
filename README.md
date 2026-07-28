# IDX Exchange MLS Analytics Project

## Project Purpose

This repository supports the IDX Exchange Data Analyst Internship project.  
The goal is to build an end-to-end real estate analytics workflow using Python and Tableau.

The workflow starts with MLS listing and sold transaction data, prepares the data for analysis, and later supports Tableau dashboards and market intelligence reporting.

## Program Workflow

This project follows the internship pipeline:

1. Data extraction
2. Monthly dataset aggregation
3. Data validation and cleaning
4. Feature engineering and market metrics
5. Tableau dashboard development
6. Market insights and reporting

## Data Source

The project uses monthly MLS listing and sold transaction files generated from the CoreLogic Trestle API through the IDX Exchange data pipeline.

Example monthly file outputs:

- `CRMLSListingYYYYMM.csv`
- `CRMLSSoldYYYYMM.csv`

Raw CSV files are stored locally and are not uploaded to GitHub because MLS transaction data is confidential.

## Repository Files

| File | Purpose |
|---|---|
| `crmls_listed.py` | Extracts monthly MLS listing data |
| `crmls_sold.py` | Extracts monthly MLS sold transaction data |
| `README.md` | Project documentation |

## Current Workflow

Run the two Python extraction scripts for the required week or month.
Use crmls_listed.py to update listings.csv.
Use crmls_sold.py to update sold.csv.
Store raw MLS CSV files locally.
Keep confidential data files out of GitHub.
Use the updated CSV files for aggregation, cleaning, analysis, and Tableau dashboard development.

## Week 1 – Monthly Dataset Aggregation

Built a Python script (`week1_aggregate.py`) that pulls all monthly CRMLS Listing and Sold CSV files (Jan 2024 – June 2026, 30 months each) from local folders, concatenates them into two combined datasets, and filters both to `PropertyType == 'Residential'` only.

**Key details:**
- Handled a data quirk where some months only have a `"_filled"` file variant with 2 extra trailing columns — these were trimmed automatically so schemas matched before concatenation.
- Ran a diagnostic check comparing an exact-match filter against a case/whitespace-normalized match, confirming no near-miss `PropertyType` variants were being silently dropped by the filter.

**Outputs:**

| File | Description |
|---|---|
| `Combined_Listing.csv` | 967,164 rows → 615,646 rows after Residential filter |
| `Combined_Sold.csv` | 665,440 rows → 447,987 rows after Residential filter |
| `week1_aggregation_row_counts.csv` | Per-file row-count log for both datasets |

---

## Weeks 2–3, Part 1 – Dataset Structuring and Validation

Built a second script (`week2_3_validation.py`) that reads the Week 1 combined outputs and documents the data across four areas.

### Dataset Understanding
- Row/column counts and data types per dataset
- Heuristic classification of columns into market-analysis vs. metadata fields

### Missing Value Analysis
- Full null-count summary table per column
- Separate report flagging any columns above 90% missing

### Numeric Distribution Review
- Percentile statistics (min, p25, median, mean, p75, p99, max) for 9 key fields: `ClosePrice`, `ListPrice`, `OriginalListPrice`, `LivingArea`, `LotSizeAcres`, `BedroomsTotal`, `BathroomsTotalInteger`, `DaysOnMarket`, `YearBuilt`
- IQR-based extreme-outlier counts for each field
- Histogram + boxplot image generated per field, per dataset

### Filtering Confirmation
- Re-verified the Week 1 Residential filter held in the combined files
- Documented unique property types found
- Saved the validated dataset as a new CSV

**Outputs:** 34 files total (16 CSVs + 18 PNGs) covering both Listing and Sold datasets.

---

## Weeks 2-3, Part 2 – Mortgage Rate Enrichment

Built a second script (`week2_3_mortgage_enrichment.py`) that enriches the Week 1 combined outputs with the national 30-year fixed mortgage rate from FRED, joined on a monthly key.

### Rate Retrieval
- Fetched the MORTGAGE30US series directly from FRED
- Coerced dates and rates to proper numeric/datetime types, dropping any unparseable weekly readings before averaging
- Resampled weekly rates to monthly averages

### Dataset Enrichment
- Sold dataset keyed off `CloseDate`; Listing dataset keyed off `ListingContractDate`
- Left-merged the monthly rate onto both combined datasets

### Validation
- Confirmed no null `rate_30yr_fixed` values remain after the merge
- Merge is a hard requirement — if any row is left unmatched, the run fails and no output is saved, rather than saving a partially-matched file

**Outputs**: 3 files total (1 monthly rates CSV + 2 enriched datasets covering both Listing and Sold).
## Weeks 4-5 – Data Cleaning and Preparation

Built a script (`week4_5_data_cleaning.py`) that takes the Week 2-3 mortgage-enriched outputs (`Sold_With_Rates.csv` / `Listing_With_Rates.csv`) and prepares an analysis-ready dataset. Nothing is deleted - bad or unusual records are flagged with `True`/`False` columns instead, so every original row remains visible for review.

### Date Conversion
- Converted `CloseDate`, `PurchaseContractDate`, `ListingContractDate`, and `ContractStatusChangeDate` to proper datetime, only where present in each dataset

### Column Cleanup
- Dropped reviewed redundant/unnecessary columns via `COLUMNS_TO_DROP` (empty by default until manually reviewed against Week 2-3's `{name}_field_categories.csv`)

### Missing Value Handling
- Core fields retained even if partially missing, per Weeks 2-3 guidance
- No columns dropped for missingness alone; columns above 90% missing are reported, not removed

### Numeric Typing
- Ensured `ClosePrice`, `ListPrice`, `OriginalListPrice`, `LivingArea`, `LotSizeAcres`, `BedroomsTotal`, `BathroomsTotalInteger`, `DaysOnMarket`, `YearBuilt` are properly typed as numeric

### Invalid Value Flags (flagged, not removed)
- `invalid_closeprice_flag` - ClosePrice <= 0
- `invalid_livingarea_flag` - LivingArea <= 0
- `invalid_daysonmarket_flag` - DaysOnMarket < 0
- `invalid_bedrooms_flag` - BedroomsTotal < 0
- `invalid_bathrooms_flag` - BathroomsTotalInteger < 0

### Date Consistency Flags
- `listing_after_close_flag` - ListingContractDate > CloseDate
- `purchase_after_close_flag` - PurchaseContractDate > CloseDate
- `negative_timeline_flag` - ListingContractDate > PurchaseContractDate

### Geographic Quality Flags
- `missing_coordinates_flag` - Latitude or Longitude is null
- `sentinel_zero_flag` - Latitude = 0 or Longitude = 0
- `positive_longitude_flag` - Longitude > 0 (should be negative for CA)
- `implausible_coordinates_flag` - coordinates fall outside a CA bounding box (lat 32.0-42.5, lon -124.5 to -114.0)

**Outputs:** 10 files total (5 per dataset - `{name}_Cleaned.csv`, `{name}_row_counts.csv`, `{name}_dtype_confirmation.csv`, `{name}_date_consistency_flags.csv`, `{name}_geographic_quality.csv`) covering both Listing and Sold datasets.

---

## Week 6 – Feature Engineering and Market Metrics

Built a script (`week6_feature_engineering.py`) that takes the Week 4-5 cleaned outputs (`Sold_Cleaned.csv` / `Listing_Cleaned.csv`) and engineers the key market indicators that power the Tableau dashboards. Full engineering runs on the Sold dataset, since most metrics depend on `ClosePrice`, `OriginalListPrice`, `PurchaseContractDate`, and `CloseDate` - fields generally only populated for sold records; only what's actually present is computed for Listings.

### Price-Based Metrics
- `price_ratio_vs_listprice` = ClosePrice / ListPrice (standard sold-to-list ratio)
- `price_ratio_vs_originallistprice` = ClosePrice / OriginalListPrice (the handbook's "Price Ratio" row, literally)
- `close_to_orig_list_ratio` = ClosePrice / OriginalListPrice - **identical formula** to the row above per the handbook text; saved under both names since the handbook lists them as two separate metrics. Needs confirmation from the program on which one dashboards should actually use.
- `price_per_sqft` = ClosePrice / LivingArea

### Time-Based Metrics
- `Year`, `Month`, `YrMo` - derived from CloseDate
- `listing_to_contract_days` = PurchaseContractDate - ListingContractDate
- `contract_to_close_days` = CloseDate - PurchaseContractDate
- `DaysOnMarket` - raw field, carried through and confirmed numeric

### Segment Analysis
Reusable `segment_summary()` helper groups by given columns and reports record count plus median/mean for every engineered + core metric present:
- PropertyType / PropertySubType
- CountyOrParish / MLSAreaMajor
- ListOfficeName / BuyerOfficeName

### School District Spatial Join (optional, Sold only)
- Point-in-polygon join of property Latitude/Longitude against CA Dept. of Education 2024-25 school district boundaries (data.ca.gov GeoJSON)
- Requires `geopandas` + `shapely` (not standard pandas dependencies) - isolated so the rest of the script still runs and saves output if they aren't installed
- Only run on the Sold dataset (`run_school_districts=True`); toggle for Listing if needed

**Outputs:** Per dataset - `{name}_engineered_sample.csv` (first 25 rows, new columns only), `{name}_Engineered.csv` (full dataset), `{name}_segment_PropertyType.csv`, `{name}_segment_County.csv`, `{name}_segment_Office.csv`. Plus `Sold_with_school_districts.csv` for the Sold dataset only.

