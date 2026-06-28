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

- Preparing a market intelligence report
