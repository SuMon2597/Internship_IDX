"""
Week 7 - Outlier Detection and Data Quality
IDX Exchange Data Analyst Internship

Applies IQR-based outlier detection to key numeric fields (ClosePrice,
LivingArea, DaysOnMarket) on the Week 6 engineered dataset. Outliers are
FLAGGED, not deleted, so the raw dataset is preserved. A separate filtered
("clean") dataset is produced for downstream Tableau work.
"""

import pandas as pd

# ---------------------------------------------------------------
# Step 0 - Load the Week 6 output (post feature-engineering dataset)
# ---------------------------------------------------------------
INPUT_PATH = r"C:\Users\Summe\OneDrive - Drexel University\0.4 Drexel Summer 2026\IDX Intern\Week6\Sold_Engineered.csv"
df = pd.read_csv(INPUT_PATH)

print(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns")

FIELDS_TO_CHECK = ["ClosePrice", "LivingArea", "DaysOnMarket"]

# ---------------------------------------------------------------
# Step 1 - IQR bounds + flag columns (business rules applied first)
# ---------------------------------------------------------------
# Business-rule invalids (should already be handled in Weeks 4-5, but
# double-checking here keeps IQR from being distorted by impossible values)
df["invalid_value_flag"] = (
    (df["ClosePrice"] <= 0)
    | (df["LivingArea"] <= 0)
    | (df["DaysOnMarket"] < 0)
)

iqr_bounds = {}

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

# ---------------------------------------------------------------
# Step 2 - Save full flagged dataset (nothing deleted)
# ---------------------------------------------------------------
df.to_csv("sold_flagged_full.csv", index=False)
print(f"\nSaved full flagged dataset: sold_flagged_full.csv "
      f"({df.shape[0]} rows, {df.shape[1]} columns)")

# ---------------------------------------------------------------
# Step 3 - Build separate filtered ("clean") dataset
# ---------------------------------------------------------------
df_clean = df[~df["any_outlier_flag"]].copy()
df_clean.to_csv("sold_filtered_clean.csv", index=False)
print(f"Saved filtered clean dataset: sold_filtered_clean.csv "
      f"({df_clean.shape[0]} rows, {df_clean.shape[1]} columns)")

# ---------------------------------------------------------------
# Step 4 - Written before/after comparison
# ---------------------------------------------------------------
print("\n" + "=" * 60)
print("BEFORE / AFTER COMPARISON")
print("=" * 60)
print(f"Row count before filtering: {df.shape[0]}")
print(f"Row count after filtering:  {df_clean.shape[0]}")
removed = df.shape[0] - df_clean.shape[0]
print(f"Rows removed: {removed} ({removed / df.shape[0] * 100:.2f}%)")

print("\nMedian values before vs. after:")
for field in FIELDS_TO_CHECK:
    before = df[field].median()
    after = df_clean[field].median()
    pct_change = (after - before) / before * 100 if before else float("nan")
    print(f"  {field:15s} before={before:,.2f}  after={after:,.2f}  "
          f"(change: {pct_change:+.2f}%)")
