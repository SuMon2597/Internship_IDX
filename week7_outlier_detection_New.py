"""
Week 7 - Outlier Detection and Data Quality
IDX Exchange Data Analyst Internship

Applies IQR-based outlier detection to key numeric fields (ClosePrice,
LivingArea, DaysOnMarket) on the Week 6 engineered datasets. Outliers are
FLAGGED, not deleted, so the raw dataset is preserved. A separate filtered
("clean") dataset is produced for downstream Tableau work.

Runs on BOTH the Sold and Listing engineered datasets, matching the
pattern used in every prior week's deliverable.
"""

import pandas as pd
import os

# ---------------------------------------------------------------
# Step 0 - Folder setup
# ---------------------------------------------------------------
INPUT_DIR  = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\IDX Intern\Week6"
OUTPUT_DIR = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\IDX Intern\Week7"

os.makedirs(OUTPUT_DIR, exist_ok=True)

FIELDS_TO_CHECK = ["ClosePrice", "LivingArea", "DaysOnMarket","price_ratio_vs_listprice", "price_ratio_vs_originallistprice",
    "close_to_orig_list_ratio"]


def run_outlier_detection(name, input_filename):
    """
    Runs the full Week 7 pipeline (IQR flagging, clean dataset, written
    comparison) for one dataset - "Sold" or "Listing".
    """
    print(f"\n{'=' * 70}")
    print(f"{name} DATASET")
    print(f"{'=' * 70}")

    input_path = os.path.join(INPUT_DIR, input_filename)
    df = pd.read_csv(input_path)
    print(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns from {input_filename}")

    # -----------------------------------------------------------
    # Step 1 - IQR bounds + flag columns (business rules applied first)
    # -----------------------------------------------------------
    # Business-rule invalids (should already be handled in Weeks 4-5, but
    # double-checking here keeps IQR from being distorted by impossible values)
    df["invalid_value_flag"] = (
        (df["ClosePrice"] <= 0)
        | (df["LivingArea"] <= 0)
        | (df["DaysOnMarket"] < 0)
    )

    iqr_bounds = {}
    comparison_lines = []

    for field in FIELDS_TO_CHECK:
        # Compute IQR only on business-rule-valid rows, so a handful of
        # zeros/negatives don't distort Q1/Q3
        valid = df.loc[~df["invalid_value_flag"], field]

        Q1 = valid.quantile(0.25)
        Q3 = valid.quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR

        iqr_bounds[field] = {"Q1": Q1, "Q3": Q3, "IQR": IQR,
                              "lower": lower, "upper": upper}

        flag_col = f"{field}_outlier_flag"
        df[flag_col] = (df[field] < lower) | (df[field] > upper)

        print(f"\n{field}:")
        print(f"  Q1={Q1:,.2f}  Q3={Q3:,.2f}  IQR={IQR:,.2f}")
        print(f"  Bounds: [{lower:,.2f}, {upper:,.2f}]")
        print(f"  Outliers flagged: {df[flag_col].sum()} "
              f"({df[flag_col].mean()*100:.2f}% of rows)")

    # Combined flag: any-field outlier OR invalid value
    outlier_cols = [f"{f}_outlier_flag" for f in FIELDS_TO_CHECK]
    df["any_outlier_flag"] = df[outlier_cols].any(axis=1) | df["invalid_value_flag"]

    # -----------------------------------------------------------
    # Step 2 - Save full flagged dataset (nothing deleted)
    # -----------------------------------------------------------
    flagged_path = os.path.join(OUTPUT_DIR, f"{name}_flagged_full.csv")
    df.to_csv(flagged_path, index=False)
    print(f"\nSaved full flagged dataset -> {flagged_path} "
          f"({df.shape[0]} rows, {df.shape[1]} columns)")

    # -----------------------------------------------------------
    # Step 3 - Build separate filtered ("clean") dataset
    # -----------------------------------------------------------
    df_clean = df[~df["any_outlier_flag"]].copy()
    clean_path = os.path.join(OUTPUT_DIR, f"{name}_filtered_clean.csv")
    df_clean.to_csv(clean_path, index=False)
    print(f"Saved filtered clean dataset -> {clean_path} "
          f"({df_clean.shape[0]} rows, {df_clean.shape[1]} columns)")

    # -----------------------------------------------------------
    # Step 4 - Written before/after comparison (printed AND saved to file)
    # -----------------------------------------------------------
    comparison_lines.append(f"{name} DATASET - BEFORE / AFTER COMPARISON")
    comparison_lines.append("=" * 60)
    comparison_lines.append(f"Row count before filtering: {df.shape[0]}")
    comparison_lines.append(f"Row count after filtering:  {df_clean.shape[0]}")
    removed = df.shape[0] - df_clean.shape[0]
    comparison_lines.append(
        f"Rows removed: {removed} ({removed / df.shape[0] * 100:.2f}%)"
    )
    comparison_lines.append("")
    comparison_lines.append("Median values before vs. after:")
    for field in FIELDS_TO_CHECK:
        before = df[field].median()
        after = df_clean[field].median()
        pct_change = (after - before) / before * 100 if before else float("nan")
        comparison_lines.append(
            f"  {field:15s} before={before:,.2f}  after={after:,.2f}  "
            f"(change: {pct_change:+.2f}%)"
        )
    comparison_lines.append("")
    comparison_lines.append("IQR bounds used per field:")
    for field, b in iqr_bounds.items():
        comparison_lines.append(
            f"  {field:15s} Q1={b['Q1']:,.2f}  Q3={b['Q3']:,.2f}  "
            f"IQR={b['IQR']:,.2f}  bounds=[{b['lower']:,.2f}, {b['upper']:,.2f}]"
        )

    comparison_text = "\n".join(comparison_lines)
    print("\n" + comparison_text)

    comparison_path = os.path.join(OUTPUT_DIR, f"{name}_before_after_comparison.txt")
    with open(comparison_path, "w") as f:
        f.write(comparison_text)
    print(f"\nSaved written comparison -> {comparison_path}")

    return df, df_clean


# ---------------------------------------------------------------
# Run for both datasets
# ---------------------------------------------------------------
sold_flagged, sold_clean = run_outlier_detection("Sold", "Sold_Engineered.csv")
listing_flagged, listing_clean = run_outlier_detection("Listing", "Listing_Engineered.csv")

print("\nDone! Week 7 outlier detection complete for both datasets.")
