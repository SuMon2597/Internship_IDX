# =============================================================================
# Week 6 - Feature Engineering and Market Metrics
# IDX Exchange | Data Analyst Internship
#
# Reads the Week 4-5 cleaned outputs (Sold_Cleaned.csv / Listing_Cleaned.csv)
# and engineers the key market indicators that power the Tableau dashboards.
#
# Engineered metrics (per handbook table):
#   - price_ratio_vs_listprice          -> ClosePrice / ListPrice
#                                          (standard "sold-to-list" ratio)
#   - price_ratio_vs_originallistprice  -> ClosePrice / OriginalListPrice
#                                          (the "Price Ratio" row in the
#                                          handbook table, literally)
#   - close_to_orig_list_ratio          -> ClosePrice / OriginalListPrice
#                                          (the "Close to Original List
#                                          Ratio" row - IDENTICAL formula to
#                                          the row above per the handbook
#                                          text. Kept as its own column so
#                                          both handbook rows are literally
#                                          represented; flag this duplication
#                                          to your program coordinator and
#                                          confirm which one dashboards
#                                          should actually use)
#   - price_per_sqft (PPSF)             -> ClosePrice / LivingArea
#   - DaysOnMarket                      -> raw field, carried through as-is
#   - Year / Month / YrMo               -> derived from CloseDate
#   - listing_to_contract_days          -> PurchaseContractDate - ListingContractDate
#   - contract_to_close_days            -> CloseDate - PurchaseContractDate
#
# These metrics depend on ClosePrice / OriginalListPrice / PurchaseContractDate
# / CloseDate, which are typically only populated for SOLD records (active
# listings don't have a close date yet). Full engineering runs on the Sold
# dataset; only the fields that actually exist are computed for Listings.
#
# Also included: an optional school-district spatial join using the
# properties' Latitude/Longitude against the CA Dept. of Education 2024-25
# school district boundaries (data.ca.gov). This requires geopandas +
# shapely, which are NOT standard pandas dependencies - see add_school_
# districts() below for install notes. It is isolated so the rest of the
# script still runs and saves output even if geopandas isn't installed.
#
# Outputs (per dataset, where applicable):
#   {name}_engineered_sample.csv        -> first 25 rows showing new columns
#   {name}_Engineered.csv               -> full dataset with new columns
#   {name}_segment_PropertyType.csv     -> summary stats by PropertyType/SubType
#   {name}_segment_County.csv           -> summary stats by CountyOrParish/MLSAreaMajor
#   {name}_segment_Office.csv           -> summary stats by ListOffice/BuyerOffice
#   Sold_with_school_districts.csv      -> (optional) Sold data + SchoolDistrictName
# =============================================================================

import pandas as pd
import numpy as np
import os

INPUT_DIR  = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\IDX Intern\Week4-5"
OUTPUT_DIR = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\IDX Intern\Week6"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# GeoJSON download for CDE's "California School District Areas 2024-25" layer,
# the same dataset linked in the handbook's Week 6 section.
SCHOOL_DISTRICT_GEOJSON_URL = (
    "https://gis.data.ca.gov/api/download/v1/items/"
    "b0e3b936426a47ce9d9a2e77e2bb86cc/geojson?layers=0"
)


# ── Step 1: Price-based metrics ─────────────────────────────────────────────
def engineer_price_metrics(df, name):
    has_close = "ClosePrice" in df.columns
    has_list = "ListPrice" in df.columns
    has_orig = "OriginalListPrice" in df.columns
    has_area = "LivingArea" in df.columns

    print(f"\n=== {name}: Price-Based Metrics ===")

    if has_close and has_list:
        df["price_ratio_vs_listprice"] = df["ClosePrice"] / df["ListPrice"].replace(0, np.nan)
        print("  Added price_ratio_vs_listprice (ClosePrice / ListPrice)")
    else:
        print("  Skipped price_ratio_vs_listprice - ClosePrice or ListPrice not present")

    if has_close and has_orig:
        ratio = df["ClosePrice"] / df["OriginalListPrice"].replace(0, np.nan)
        # Both handbook rows ("Price Ratio" and "Close to Original List Ratio")
        # use this identical formula - saved under both names, see header note.
        df["price_ratio_vs_originallistprice"] = ratio
        df["close_to_orig_list_ratio"] = ratio
        print("  Added price_ratio_vs_originallistprice AND close_to_orig_list_ratio "
              "(both = ClosePrice / OriginalListPrice, per handbook)")
    else:
        print("  Skipped OriginalListPrice-based ratios - ClosePrice or OriginalListPrice not present")

    if has_close and has_area:
        df["price_per_sqft"] = df["ClosePrice"] / df["LivingArea"].replace(0, np.nan)
        print("  Added price_per_sqft (ClosePrice / LivingArea)")
    else:
        print("  Skipped price_per_sqft - ClosePrice or LivingArea not present")

    return df


# ── Step 2: Time-based metrics ──────────────────────────────────────────────
def engineer_time_metrics(df, name):
    has_close_date = "CloseDate" in df.columns
    has_listing_date = "ListingContractDate" in df.columns
    has_purchase_date = "PurchaseContractDate" in df.columns

    print(f"\n=== {name}: Time-Based Metrics ===")

    if has_close_date:
        df["CloseDate"] = pd.to_datetime(df["CloseDate"], errors="coerce")
        df["Year"] = df["CloseDate"].dt.year
        df["Month"] = df["CloseDate"].dt.month
        df["YrMo"] = df["CloseDate"].dt.to_period("M").astype(str)
        print("  Added Year, Month, YrMo (derived from CloseDate)")
    else:
        print("  Skipped Year/Month/YrMo - CloseDate not present")

    if has_listing_date and has_purchase_date:
        df["ListingContractDate"] = pd.to_datetime(df["ListingContractDate"], errors="coerce")
        df["PurchaseContractDate"] = pd.to_datetime(df["PurchaseContractDate"], errors="coerce")
        df["listing_to_contract_days"] = (
            df["PurchaseContractDate"] - df["ListingContractDate"]
        ).dt.days
        print("  Added listing_to_contract_days (PurchaseContractDate - ListingContractDate)")
    else:
        print("  Skipped listing_to_contract_days - ListingContractDate or PurchaseContractDate not present")

    if has_purchase_date and has_close_date:
        df["PurchaseContractDate"] = pd.to_datetime(df["PurchaseContractDate"], errors="coerce")
        df["contract_to_close_days"] = (
            df["CloseDate"] - df["PurchaseContractDate"]
        ).dt.days
        print("  Added contract_to_close_days (CloseDate - PurchaseContractDate)")
    else:
        print("  Skipped contract_to_close_days - PurchaseContractDate or CloseDate not present")

    # DaysOnMarket is the raw field per the handbook - carried through as-is,
    # just confirmed present/typed numeric here.
    if "DaysOnMarket" in df.columns:
        df["DaysOnMarket"] = pd.to_numeric(df["DaysOnMarket"], errors="coerce")
        print("  Confirmed DaysOnMarket present (raw field, numeric-typed)")
    else:
        print("  NOTE: DaysOnMarket not present in this dataset")

    return df


# ── Step 3: Segment analysis ────────────────────────────────────────────────
# One reusable helper: groups by the given columns and reports count plus
# median/mean for whichever engineered + core metrics are actually present.
def segment_summary(df, name, group_cols, label):
    present_group_cols = [c for c in group_cols if c in df.columns]
    if not present_group_cols:
        print(f"\n=== {name}: Segment Summary ({label}) ===")
        print(f"  Skipped - none of {group_cols} present in this dataset")
        return None

    metric_cols = [
        "ClosePrice", "price_ratio_vs_listprice", "price_ratio_vs_originallistprice",
        "close_to_orig_list_ratio", "price_per_sqft", "DaysOnMarket",
        "listing_to_contract_days", "contract_to_close_days",
    ]
    present_metrics = [c for c in metric_cols if c in df.columns]

    agg_dict = {m: ["median", "mean"] for m in present_metrics}
    grouped = df.groupby(present_group_cols).agg(agg_dict)
    grouped.columns = ["_".join(c) for c in grouped.columns]
    grouped["record_count"] = df.groupby(present_group_cols).size()
    grouped = grouped.reset_index().sort_values("record_count", ascending=False)

    path = os.path.join(OUTPUT_DIR, f"{name}_segment_{label}.csv")
    grouped.to_csv(path, index=False)

    print(f"\n=== {name}: Segment Summary ({label}) ===")
    print(f"  Grouped by: {present_group_cols}")
    print(f"  Metrics summarized: {present_metrics}")
    print(f"  Rows in summary: {len(grouped):,}")
    print(f"  Saved -> {path}")
    return grouped


# ── Step 4 (optional): School district spatial join ─────────────────────────
def add_school_districts(df, name):
    """
    Spatial join of property Latitude/Longitude against CA school district
    boundary polygons. This is NOT a simple pd.merge() - it requires
    geopandas + shapely to do a point-in-polygon lookup.

        pip install geopandas shapely
        (Windows users who hit GDAL/Fiona build errors: use
         conda install -c conda-forge geopandas instead)

    If geopandas isn't installed, this step is skipped with a message and
    the rest of the script's outputs are unaffected.
    """
    print(f"\n=== {name}: School District Spatial Join ===")

    if "Latitude" not in df.columns or "Longitude" not in df.columns:
        print("  Skipped - Latitude/Longitude not present in this dataset")
        return df

    try:
        import geopandas as gpd
        from shapely.geometry import Point
    except ImportError:
        print("  Skipped - geopandas/shapely not installed. Run:")
        print("    pip install geopandas shapely")
        return df

    print(f"  Downloading school district boundaries from:\n    {SCHOOL_DISTRICT_GEOJSON_URL}")
    districts = gpd.read_file(SCHOOL_DISTRICT_GEOJSON_URL)
    print(f"  Loaded {len(districts):,} school district polygons")

    # Ensure both layers share the same coordinate reference system (WGS84
    # lat/lon) before doing the spatial join.
    if districts.crs is None:
        districts = districts.set_crs(epsg=4326)
    else:
        districts = districts.to_crs(epsg=4326)

    coords = df.copy()
    coords["Latitude"] = pd.to_numeric(coords["Latitude"], errors="coerce")
    coords["Longitude"] = pd.to_numeric(coords["Longitude"], errors="coerce")

    valid = coords.dropna(subset=["Latitude", "Longitude"]).copy()
    print(f"  {len(valid):,} of {len(coords):,} rows have usable coordinates for the join")

    geometry = [Point(xy) for xy in zip(valid["Longitude"], valid["Latitude"])]
    points_gdf = gpd.GeoDataFrame(valid, geometry=geometry, crs="EPSG:4326")

    # Adjust "DistrictNam" / "DISTRICTNAME" etc. below to match whatever the
    # actual column name is in the downloaded layer - CDE datasets have
    # renamed this field across releases. Print districts.columns to check.
    name_col_candidates = [c for c in districts.columns if "district" in c.lower() and "name" in c.lower()]
    district_name_col = name_col_candidates[0] if name_col_candidates else districts.columns[0]
    print(f"  Using '{district_name_col}' as the school district name field "
          f"(available fields: {list(districts.columns)})")

    joined = gpd.sjoin(
        points_gdf, districts[[district_name_col, "geometry"]],
        how="left", predicate="within"
    ).rename(columns={district_name_col: "SchoolDistrictName"})

    joined = joined.drop(columns=["geometry", "index_right"], errors="ignore")

    matched = joined["SchoolDistrictName"].notna().sum()
    print(f"  Matched {matched:,} of {len(joined):,} geocoded rows to a school district")

    out_path = os.path.join(OUTPUT_DIR, f"{name}_with_school_districts.csv")
    joined.to_csv(out_path, index=False)
    print(f"  Saved -> {out_path}")

    return joined


# ── Run the full Week 6 pipeline for one dataset ────────────────────────────
def run_feature_engineering(name, input_filename, run_school_districts=False):
    print(f"\n{'=' * 70}")
    print(f"{name} DATASET")
    print(f"{'=' * 70}")

    df = pd.read_csv(os.path.join(INPUT_DIR, input_filename), low_memory=False)
    print(f"Loaded {len(df):,} rows, {df.shape[1]} columns from {input_filename}")

    df = engineer_price_metrics(df, name)
    df = engineer_time_metrics(df, name)

    # Sample output table showing the new columns populated correctly
    new_cols = [c for c in [
        "price_ratio_vs_listprice", "price_ratio_vs_originallistprice",
        "close_to_orig_list_ratio", "price_per_sqft", "DaysOnMarket",
        "Year", "Month", "YrMo", "listing_to_contract_days", "contract_to_close_days",
    ] if c in df.columns]
    id_cols = [c for c in ["ListingId", "PropertyType", "CloseDate"] if c in df.columns]
    sample_path = os.path.join(OUTPUT_DIR, f"{name}_engineered_sample.csv")
    df[id_cols + new_cols].head(25).to_csv(sample_path, index=False)
    print(f"\nSample output (first 25 rows, new columns) saved -> {sample_path}")

    # Segment summaries
    segment_summary(df, name, ["PropertyType", "PropertySubType"], "PropertyType")
    segment_summary(df, name, ["CountyOrParish", "MLSAreaMajor"], "County")
    segment_summary(df, name, ["ListOfficeName", "BuyerOfficeName"], "Office")

    # Full engineered dataset
    full_path = os.path.join(OUTPUT_DIR, f"{name}_Engineered.csv")
    df.to_csv(full_path, index=False)
    print(f"\nFull engineered dataset saved -> {full_path}  ({len(df):,} rows, {df.shape[1]} columns)")

    if run_school_districts:
        add_school_districts(df, name)

    return df


# ── Run for both datasets ───────────────────────────────────────────────────
# School district join only makes sense (and is only requested by the
# handbook) for the Sold dataset's dashboard use case - flip to True for
# Listing too if your program wants it there as well.
sold_df = run_feature_engineering("Sold", "Sold_Cleaned.csv", run_school_districts=True)
listing_df = run_feature_engineering("Listing", "Listing_Cleaned.csv", run_school_districts=False)

print("\nDone! Week 6 feature engineering and market metrics complete for both datasets.")
