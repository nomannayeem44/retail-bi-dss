# Data and Method

## Expected local layout

```text
retail-bi-dss/
  src/assessment2_etl.py
  src/assessment2_analysis.py
  data/raw/retail-source.xlsx
  data/processed/
  outputs/charts/
```

The ETL expects the source worksheet named `RetailStore Dataset `, including its trailing space. Input data is deliberately absent. Never substitute a different dataset without reviewing its schema and date representation.

Run order, after reviewing the scripts and supplying authorised data: ETL, then descriptive analysis. These instructions have not been execution-tested in this package. The scripts write derived results under this project only. Dependencies are pandas, openpyxl and matplotlib; a tested version lock has not yet been established.

## Controls to check

- Source row count and original financial field meanings.
- Mixed Excel/string date interpretation against the supplied assessment documentation.
- Transaction-key uniqueness without deleting rows merely because invoice IDs repeat.
- Fact/dimension relationships and KPI totals compared with source controls.
- Any differences between saved screenshots and a future fresh run.

## Public release boundary

Current candidates are this documentation, the user-authored dashboard screenshot and sanitised AI-assisted code. Raw data, processed row-level data, the PBIX semantic model, reports with student identifiers, peer responses and unreviewed AI transcripts are excluded. Data/image sharing terms and the final file set remain subject to review and user approval.
