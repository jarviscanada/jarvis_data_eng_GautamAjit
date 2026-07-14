# Financial Fraud Analytics on Azure Databricks

An end-to-end Azure Data Engineering project that ingests financial transaction data from multiple sources, builds a **Medallion Architecture (Bronze → Silver → Gold)** using Azure Databricks, and delivers an interactive fraud analytics dashboard. The pipeline is orchestrated using Databricks Jobs and demonstrates modern ELT best practices on Azure.

---

# Technologies Used

- Azure Databricks
- Azure SQL Database
- Azure Data Factory (ADF)
- Azure Data Lake Storage Gen2 (ADLS Gen2)
- Unity Catalog
- Lakeflow Connect
- Delta Lake
- Databricks Jobs
- Databricks Dashboards
- PySpark
- SQL
- JDBC

---

# Architecture

**Workflow**

```
CSV Files (Transactions, Cards)
        │
        ▼
Azure SQL Database
        │
 ┌──────┴─────────┐
 │                │
JDBC      Lakeflow Connect
 │                │
 └──────┬─────────┘
        │
        ▼

JSON Files (Users, MCC Codes, Fraud Labels)
        │
        ▼
Azure Data Lake Storage
        │
        ├──────── External Location
        │
        └──────── Azure Data Factory
                    │
                    ▼

           Azure Databricks
                  │
          Bronze → Silver → Gold
                  │
                  ▼
      Databricks Dashboard
                  │
                  ▼
         Databricks Job Workflow
```

---

# Dataset

This project uses the **Financial Transactions Dataset for Analytics**.

Datasets include:

| Dataset | Description |
|----------|-------------|
| transactions_data.csv | Financial transaction records |
| cards_data.csv | Credit/Debit card information |
| users_data.csv | Customer demographic data |
| mcc_codes.json | Merchant Category Codes |
| train_fraud_labels.json | Fraud labels |

---

# Project Setup

## Azure Resources

Create the following Azure resources:

- Azure SQL Database
- Azure Storage Account (ADLS Gen2)
- Azure Databricks Workspace
- Azure Data Factory

---

# Data Ingestion

## 1. Azure SQL Database

Upload:

- transactions_data.csv
- cards_data.csv

using the VS Code MSSQL extension.

---

## 2. JDBC Connection

Read the Transactions table stored in the Azure SQL Server database using JDBC.

```python
url = "<jdbc-url>"

df = (
    spark.read
        .format("jdbc")
        .option("url", url)
        .option("dbtable", "transactions")
        .option("user", username)
        .option("password", password)
        .load()
)

display(df)
```

---

## 3. Lakeflow Connect

Use Lakeflow Connect to ingest:

- cards_data.csv

into Databricks.

---

## 4. External Location

Upload

- users_data.csv

to Azure Data Lake Storage.

Create:

- Storage Credential
- External Location

using Unity Catalog.

---

## 5. Azure Data Factory

Copy the following files into Unity Catalog volume (ADLS Gen 2):

- mcc_codes.json
- train_fraud_labels.json

---

# Medallion Architecture

## Bronze Layer

Raw data ingestion.

Tables

- bronze.card_data
- bronze.users_data
- bronze.transactions_data

### Processing

- Raw ingestion
- Preserve schema 
---

## Silver Layer

Data cleansing and enrichment.

### Processing

- Remove duplicates
- Handle null values
- Standardize column names
- Convert data types
- Join fraud labels
- Join MCC descriptions

Tables

- silver.card_data
- silver.users_data
- silver.transactions_data

---

## Gold Layer

Business-ready analytical tables.

Gold tables answer the following business questions:

- Which day of the week has the highest fraud?
- Fraud rate trend over time
- Users with highest fraud count
- Weekly transaction anomalies
- Merchant category fraud rate
- Merchant fraud volume
- Fraud distribution by time of day
- Fraud vs non-fraud average transaction amount
- Merchant category with highest fraud amount
- Daily fraud losses
- Weekly fraudulent users
- Seasonal fraud trends
- User behavior before and after fraud
- High-value vs low-value fraud

---

# Project Structure

```
ETL_Databricks/
│
├── notebooks/
│   ├── Bronze_ETL.ipynb
│   ├── Silver_ETL.ipynb
│   ├── Gold_ETL.ipynb
│
├── dashboards/
│
├── miscellaneous/
│
├── README.md
│
└── .gitignore
```

---

# Dashboard

The dashboard is built using Gold tables and includes interactive filters.

Visualizations include:

- Fraud Trend
- Fraud by Weekday
- Fraud by Merchant Category
- Fraud Losses
- Fraud Distribution
- User Rankings
- High Value Fraud

---

# Workflow Orchestration

The workflow is orchestrated using **Databricks Jobs**.

Execution order:

```
Bronze Notebook
      │
      ▼
Silver Notebook
      │
      ▼
Gold Notebook
      │
      ▼
Dashboard Refresh
```

---

# Future Improvements

- Auto Loader
- Streaming Pipelines
- Delta Live Tables
- Change Data Capture (CDC)
- Machine Learning Fraud Detection
- CI/CD using Databricks Asset Bundles
- Monitoring and Alerting

---

# Learning Outcomes

This project demonstrates:

- Multi-source data ingestion
- Azure SQL integration
- Lakeflow Connect
- Azure Data Factory
- Unity Catalog
- External Locations
- Delta Lake
- Medallion Architecture
- PySpark ETL
- Databricks Dashboards
- Databricks Job Orchestration
