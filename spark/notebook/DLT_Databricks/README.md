# AlphaVantage API Pipeline with Databricks Delta Live Tables

## Overview

This project demonstrates an end-to-end data engineering pipeline built on **Databricks** using the **Medallion Architecture (Bronze → Silver → Gold)**. The pipeline ingests daily stock market data from the **Alpha Vantage API**, processes it through Delta Live Tables (DLT), and produces analytical datasets that power an interactive dashboard.

The solution follows modern data engineering best practices, including data quality, layered transformations, workflow orchestration, and scalable Delta Lake storage.

---

## Architecture

```text
                 Alpha Vantage API
                        │
                        ▼
              Landing Data (JSON)
                        │
                        ▼
              Bronze DLT Pipeline
        (Raw Quotes & Company Information)
                        │
                        ▼
              Silver DLT Pipeline
     (Cleaned, Standardized, Enriched Data)
                        │
                        ▼
               Gold DLT Pipeline
      (Business Metrics & Trend Analysis)
                        │
                        ▼
           Databricks Dashboard
```

---

## Medallion Architecture

### Bronze Layer

The Bronze layer stores the raw data received directly from the Alpha Vantage API with minimal transformations.

Datasets include:

- Stock Quotes
- Company Information

Purpose:

- Preserve raw source data
- Enable replayability
- Maintain ingestion history

---

### Silver Layer

The Silver layer transforms and enriches the Bronze datasets by:

- Cleaning invalid records
- Standardizing column names
- Applying appropriate data types
- Joining quote data with company information
- Preparing datasets for downstream analytics

---

### Gold Layer

The Gold layer contains business-ready datasets optimized for reporting and dashboards.

Analytics include:

#### Price Trend Analysis

- Daily price change
- 7-day trend
- 30-day trend
- 90-day trend

#### Price Percentage Analysis

- Daily percentage change
- 7-day percentage trend
- 30-day percentage trend
- 90-day percentage trend

#### Volume Trend Analysis

- Daily trading volume
- 7-day volume trend
- 30-day volume trend
- 90-day volume trend

---

## Data Source

The project uses the **Alpha Vantage API**, a free stock market data provider.

Data collected includes:

- Latest stock quote
- Company overview
- Trading volume
- Price information

API limitations:

- 25 requests per day
- 5 requests per minute

---

## Technologies Used

- Databricks
- Delta Live Tables (DLT)
- Delta Lake
- Apache Spark
- PySpark
- Unity Catalog
- Databricks Workflows
- Databricks SQL Dashboard
- Python
- Alpha Vantage API

---

## Project Structure

```
.
├── landing/
│   └── *.ipynb               # API ingestion scripts
│
├── bronze/
│   ├── *.py                  # Bronze DLT pipelines
│
├── silver/
│   ├── *.py                  # Silver DLT pipelines
│
├── gold/
│   ├── *.py                  # Gold DLT pipelines
│
├── dashboard/
│   └── *.pdf                 # Dashboard screenshots/PDF exports
│
└── README.md
```
---

## Pipeline Workflow

The pipeline executes the following steps:

1. Retrieve stock quote data from Alpha Vantage.
2. Retrieve company information.
3. Store raw API responses in the Bronze layer.
4. Clean and enrich datasets in the Silver layer.
5. Generate analytical Gold tables.
6. Refresh dashboard datasets.
7. Execute automatically using Databricks Workflows.

---

## Dashboard

The dashboard visualizes key stock market metrics generated from the Gold layer, including:

- Daily price movement
- Price trend over 7, 30, and 90 days
- Daily percentage change
- Trading volume trends
- Company-level performance comparisons

Dashboard exports are available in the **dashboard/** directory.

---

## Data Pipeline Design Decisions

### Delta Live Tables

The project uses **Delta Live Tables (DLT)** to simplify pipeline development, automate dependency management, and improve data reliability.

### Medallion Architecture

The Bronze → Silver → Gold architecture provides:

- Clear separation of responsibilities
- Improved maintainability
- Incremental transformations
- Better scalability
  
---

## Future Improvements

Potential enhancements include:

- Historical stock price ingestion
- Streaming ingestion
- Additional technical indicators (RSI, MACD, Moving Averages)
- Alerting for abnormal price movement
- Data quality expectations in DLT
- CI/CD using Databricks Asset Bundles
- Automated unit testing
- Parameterized ticker symbols

---

## Author

**Gautam Radhakrishnan Ajit**

---

## License

This project is intended for educational and portfolio purposes.
