# Global E‑Commerce KPI Dashboard with Predictive Insights

This repository contains a complete, end‑to‑end BI project: synthetic data generation, SQL schema & views,
Power BI model starter measures, and documentation.

## Structure
```
ecommerce-bi-forecast/
  data/
    raw/                # CSV datasets to import
  db/
    schema_and_views.sql
  powerbi/
    starter_measures.dax
  etl/
    generate_synthetic_data.py  # synthetic data generator
  model/
    (forecast notebooks later)
  docs/
    (case study & process map later)
```
## Datasets
- `orders.csv` – transactional orders with shipping & delivery outcomes
- `customers.csv` – customer signup cohort and region
- `marketing.csv` – daily spend & sessions by region and channel
- `returns.csv` – return events with reason and refund

Date range: 2023-01-01 to 2025-08-31

## Getting Started
1. Load CSVs from `data/raw` into Power BI.
2. Import or paste the measures from `powerbi/starter_measures.dax`.
3. (Optional) Load into a SQL database and run `db/schema_and_views.sql` to create views.
4. Build visuals and slicers: Date, Region, Country, Channel.
