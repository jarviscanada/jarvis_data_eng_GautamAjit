# Credit Scoring Pipeline: A Machine Learning Project

## 1\. Introduction

### Business Objective

Home Credit is an international consumer finance provider serving customers with varying levels of traditional credit history. Many potential customers have limited or no conventional credit history, making it challenging to assess their repayment ability using traditional credit-scoring methods.

The objective of this project is to develop a machine learning model that predicts whether a loan applicant is likely to experience payment difficulties, using application data supplemented with credit bureau information.

\---

## 2\. Implementation

### 2.1 Exploratory Data Analysis (EDA)

Exploratory data analysis was conducted on `application\_train.csv` to understand the dataset structure, feature types, missingness, and target distribution.

The analysis included:

* Examining the **class imbalance** and overall target distribution.
* Comparing default rates across key applicant segments, including:

  * Contract type
  * Income type
  * Occupation
  * Organization type
* Analyzing distributions of important financial, demographic, employment, and external-source features.
* Identifying numerical features most strongly correlated with `TARGET`.
* Visualizing relationships between highly correlated features using correlation heatmaps.
* Integrating `bureau.csv` by calculating the number of bureau records per applicant and evaluating its relationship with default rates.

\---

### 2.2 Preprocessing \& Feature Engineering

Data quality issues were addressed by converting sentinel values, such as `DAYS\_EMPLOYED = 365243`, to missing values and evaluating other potential sentinel values.

A structured missing-data strategy was implemented, including:

* Removing features with excessive missingness.
* Adding missingness indicators where appropriate.
* Applying median and mode imputation.
* Evaluating whether missingness itself was predictive of `TARGET`.

Several applicant-level features were engineered to capture characteristics such as:

* Credit burden
* Income
* Employment
* Family structure
* Age
* External credit scores

The `bureau.csv` dataset was integrated to create aggregated credit-history features, including:

* Number of bureau records
* Number of active credits
* Credit history duration
* Overdue amounts

Categorical variables were subsequently encoded using **ordinal encoding, one-hot encoding, or frequency encoding**, depending on their characteristics and cardinality.

\---

### 2.3 Modeling

Three classification models were evaluated:

1. **Logistic Regression**
2. **Random Forest**
3. **LightGBM (`LGBMClassifier`)**

Model performance was compared using:

* AUROC
* AUPRC
* Gini coefficient
* KS statistic
* F1-score

The best-performing model was selected and its hyperparameters were optimized using `RandomizedSearchCV`. Model stability was further evaluated using **5-fold stratified cross-validation**.

The final model and preprocessing steps were packaged into an end-to-end `.pkl` pipeline using `joblib`. The pipeline is designed to accept raw application and bureau data and perform the required preprocessing and feature engineering before generating predictions.

\---

### 2.4 Explainability \& Model Monitoring

The final model was evaluated using AUROC, Gini, KS statistic, AUPRC, and F1-score at the selected classification threshold. **5-fold Stratified Cross-Validation** was also used to assess performance stability.

SHAP analysis was applied to explain both overall model behavior and individual predictions, including high-, borderline-, and low-risk applicants. For a high-risk applicant, the key factors contributing to the adverse prediction were identified and documented in an adverse action notice.

Population stability was assessed using **Population Stability Index (PSI)** across the top 10 features to identify potential distribution shifts between training and test populations. Features exceeding the defined PSI threshold were flagged for monitoring.

Model performance, feature importance, and population stability results were consolidated into a **model monitoring dashboard** for ongoing evaluation.

> A more detailed analysis of the model validation, explainability, and monitoring results can be found in the `report` folder.

\---

### 2.5 Pipeline Architecture

!\[Pipeline Architecture](pipeline.png)

\---

## 3\. Dataset Overview

**Source:** Kaggle — Home Credit Default Risk  
**Download:** [Kaggle Competition Dataset](https://www.kaggle.com/c/home-credit-default-risk/data)

The dataset contains approximately **307,000 loan applications** with **122 features** distributed across seven relational tables:

* `application\_train.csv`
* `bureau.csv`
* `bureau\_balance.csv`
* `credit\_card\_balance.csv`
* `installments\_payments.csv`
* `POS\_CASH\_balance.csv`
* `previous\_application.csv`

For this project, only the following two datasets are required:

* `application\_train.csv`
* `bureau.csv`

The target variable, `TARGET`, indicates whether a client experienced payment difficulties:

* `1` → Payment difficulties
* `0` → No payment difficulties

### Key Dataset Challenges

* Significant missing data across approximately **20% of the features**.
* Strong class imbalance, with approximately **8% of applications resulting in default**.
* Need to integrate information from multiple related data sources.
* High-cardinality categorical variables requiring specialized encoding.
* Potential population drift between training and future scoring populations.

\---

## 4\. Environment Setup \& Project Structure

### 4.1 Environment

The project requires **Python 3.9+** with Jupyter Notebook or JupyterLab.

Install the required dependencies using:

```bash
pip install numpy pandas matplotlib seaborn scikit-learn imbalanced-learn shap category\_encoders joblib scipy openpyxl lightgbm
```

Download `application\_train.csv` and `bureau.csv` from the Kaggle competition page and place both files in the project's `data` folder before running the notebooks.

\---

### 4.2 Folder Structure

```text
project/
│
├── data/
│   ├── application\_train.csv
│   ├── bureau.csv
│   └── ... intermediate/preprocessed CSV files
│
├── src/
│   ├── ... custom transformers
│   └── ... reusable helper functions
│
├── notebooks/
│   ├── 01\_EDA.ipynb
│   ├── 02\_feature\_engineering.ipynb
│   ├── 03\_preprocessing.ipynb
│   ├── 04\_modeling.ipynb
│   └── 05\_explainability.ipynb
│
├── report/
│   └── model\_documentation.md
│
├── pipeline.png
└── README.md
```

### Folder Descriptions

|Folder|Description|
|-|-|
|`data/`|Contains raw datasets and intermediate preprocessed/feature-engineered CSV files.|
|`src/`|Contains custom Python classes, transformers, and reusable helper functions used by the notebooks.|
|`notebooks/`|Contains the five notebooks used for EDA, preprocessing, modeling, and explainability.|
|`report/`|Contains detailed model documentation, validation results, and evaluation methodology.|

\---

## 5\. Instructions to Run the Project

### 5.1 Prerequisites

Before running the project, ensure that:

1. Python 3.9+ is installed.
2. All packages listed in the **Environment** section are installed.
3. `lightgbm` is installed, as the final model is an `LGBMClassifier`.
4. `application\_train.csv` and `bureau.csv` are available in the `data` folder.

### 5.2 Notebook Execution Order

The notebooks should be executed in the following order:

```text
01\_EDA.ipynb
      ↓
02\_feature\_engineering.ipynb
      ↓
03\_preprocessing.ipynb
      ↓
04\_modeling.ipynb
      ↓
05\_explainability.ipynb
```

The first three notebooks are primarily used for **exploration, preprocessing, and feature engineering**. At the end of `03\_preprocessing.ipynb`, preprocessed training and test datasets are saved as CSV files.

These preprocessed datasets are used by `04\_modeling.ipynb` for initial model comparison. However, the final production pipeline is built to operate on the **raw application and bureau datasets**, performing the required preprocessing and feature engineering internally.

> \*\*Important:\*\* The final pipeline expects the application and bureau data to be merged before being passed to the model. Make sure the bureau dataset is loaded into a DataFrame named `df\_bureau`, as the custom customer-data transformer expects this input. Also, `05\_explainability.ipynb` notebook expects two files - pipeline\_train.csv` and `pipeline\_test.csv` - to run. These files are nothing but the raw `application\_train.csv` split into train/test (80/20) in order to prevent data leakage during training. These files are created in the `04\_modeling.ipynb` notebook, just before the full pipeline is built.

\---

### 5.3 Customer Segmentation

The project also includes customer segmentation using a custom `ClusterSegment()` transformer.

The transformer requires the number of clusters to be manually specified:

```python
ClusterSegment(n\_clusters=2)
```

The optimal number of clusters was determined using **Elbow** and **Silhouette** analysis.

> \*\*Important:\*\* The number of clusters is currently a manual configuration. If the underlying population changes significantly due to population drift, the optimal number of clusters may also change and should be reassessed.

\---

## 6\. Future Improvements \& Limitations

### Future Improvements

* Incorporate the remaining five Home Credit datasets to identify additional predictive features.
* Automate model retraining when significant population drift is detected.
* Develop an automated mechanism for monitoring PSI and triggering retraining workflows when PSI exceeds the defined threshold.
* Automate the customer segmentation process and dynamically determine the appropriate number of clusters.
* Introduce a more production-oriented model deployment and monitoring architecture.

### Current Limitations

The pipeline is currently **tightly coupled to the existing dataset structure**. Changes to feature names, column types, or the available feature set may cause the pipeline to fail because preprocessing and feature engineering logic are specifically designed around the current dataset.

The customer segmentation component also requires the optimal number of clusters to be manually determined and supplied to the pipeline.

\---

## 7\. Technologies Used

* **Python 3.9+**
* **Jupyter Notebook / JupyterLab**
* **Pandas**
* **NumPy**
* **Scikit-learn**
* **LightGBM**
* **Imbalanced-learn**
* **SHAP**
* **Category Encoders**
* **Matplotlib**
* **Seaborn**
* **SciPy**
* **Joblib**
* **OpenPyXL**

