# Model Validation Summary: Consumer Risk Scoring Model

## Document Control \& Metadata

**Model Name:** Credit Scoring Pipeline Model

**Validation Date:** August 2026

**Status:** Subject to Management Review

**Document Path:** `reports/model\_documentation.md`

\---

## 1\. Model Purpose

**Business Problem:** Home Credit is an international consumer finance provider serving customers across multiple markets. A significant proportion of its prospective customers have limited or no conventional credit history, presenting challenges in accurately assessing their creditworthiness using traditional credit assessment methods. The objective of this project is to develop a machine learning model that predicts the likelihood of payment difficulties among loan applicants. The model leverages applicant-level information, supplemented by credit bureau data, to identify patterns associated with repayment risk and support more effective credit risk assessment.

**Target Variable:** Binary flag defined as `1` if borrower defaults; `0` otherwise.

**Decision Thresholds:**

* **High Risk (PD > 40%):** Auto-Decline
* **Medium Risk (20% < PD < 40% ):** Manual Underwriting / Stipulation Required
* **Low Risk (PD < 20%):** Auto-Approve

\---

## 2\. Methodology

**Pipeline Architecture:** The model is implemented as an end-to-end scikit-learn pipeline, integrating data preparation, feature engineering, preprocessing, customer segmentation, feature scaling, and classification into a single reproducible workflow.

The pipeline consists of the following sequential stages:

1. **Bureau Data Integration and Imputation – `BureauMergerAndImputer`:** Application-level data is combined with supplementary credit bureau information. Bureau-level records are aggregated and relevant missing values are addressed during this stage.
2. **High-Missingness Feature Removal – `DropHighMissingColumns`:** Features exceeding the predefined missing-value threshold are removed to reduce noise and improve model robustness.
3. **Missing-Value Indicators – `AddMissingIndicators`:** Indicator variables are created for selected features with missing observations, allowing the model to capture potential predictive information associated with missingness itself.
4. **Application Feature Engineering – `ApplicationFeatureEngineer`**
5. **Correlation-Based Feature Selection – `HighCorrelationFilter`:** Highly correlated features are identified and removed to reduce redundancy and improve the efficiency of the downstream modeling process.
6. **Categorical Feature Encoding – `FrequencyEncoder` and `DynamicPreprocessingPipeline`:** Categorical variables are transformed according to their characteristics. Ordinal encoding is applied to ordered categorical variables, one-hot encoding is used for selected low-cardinality variables, and frequency encoding is applied to higher-cardinality categorical variables.
7. **Customer Segmentation – `ClusterSegmenterWrapper`:** Customers are assigned to predefined behavioral/risk segments using a clustering-based segmentation component. The resulting `customer\_segment` variable is incorporated as an additional model feature.
8. **Feature Scaling – `StandardScaler`:** The resulting numerical feature set is standardized to ensure consistent feature scaling where required by the preprocessing workflow.
9. **Classification – `LGBMClassifier`:** The final feature matrix is passed to a LightGBM gradient-boosting classifier, which produces the predicted probability of payment difficulties for each loan applicant.

**Feature Set:** The preprocessing stages produce 110 model-ready features, consisting of numerical variables, engineered features, missingness indicators, encoded categorical variables, bureau-derived variables, and the customer segment variable. Additional domain-relevant features are derived from the application and bureau data. These include measures such as age, credit-to-income ratio, annuity-to-income ratio, credit term, income per household member, and aggregated external-source statistics.

**Hyperparameter Specifications:**

```text
n\_estimators=500,
learning\_rate=0.03,
num\_leaves=40,
subsample=0.8,
colsample\_bytree=0.9,
scale\_pos\_weight=12,
reg\_lambda=1,
reg\_alpha=0.1,
min\_child\_samples=100,
max\_depth=-1
```

\---

## 3\. Performance

Evaluated on test set to prevent data leakage \& compared against the baseline models (Logistic Regression \& Random Forest):

|Metric|Logistic Regression|Random Forest|LGBMClassifier\*|LGBMClassifier\* (5-fold CV on training set)|
|-|-:|-:|-:|-:|
|AUROC|0.7442 (±0.0035)|0.7425 (±0.0032)|0.7685|0.7627 (+/- 0.0009)|
|AUC-PR|0.2232 (±0.0040)|0.2208 (±0.0027)|0.2571|0.2476 (+/- 0.0061)|
|Gini Coefficient|0.4885|0.4850|0.5370|0.5253 (+/- 0.0018)|
|Kolmogorov-Smirnov (KS)|0.3631|0.3599|0.4004|0.3925 (+/- 0.0021)|
|F1 Score|0.2554|0.2606|0.3216|0.2738 (+/- 0.0012)|

**CV Results Summary:** 5-Fold stratified cross-validation exhibited minimal variance across folds (AUROC range: 0.7627 (+/- 0.0009)), confirming stability and resilience against overfitting.

\---

## 4\. Explainability \& Compliance

### Top 10 SHAP Features (by Mean SHAP Value)

1. `EXT\_SOURCE\_MEAN`: The mean of the three eternally sourced credit scores for an applicant.
2. `CREDIT\_TERM`: the total duration or length of a loan or credit agreement
3. `DAYS\_EMPLOYED`: Number of days employed
4. `NAME\_EDUCATION\_TYPE`: Highest academic degree of qualification
5. `EXT\_SOURCE\_3`: An externally sourced credit score
6. `AGE`: Age of the applicant.
7. `mean\_days\_credit`: Total credit trades opened in past 12 months
8. `AMT\_ANNUITY`: Loan Annuity
9. `EXT\_SOURCE\_1\_IS\_MISSING`: A missing indicator column which indicates whether the credit score value from Source 1 is missing or not.
10. `active\_count`: number of active loans/ credit lines.

### Sample Adverse Action Notice

Sample Adverse Action Notice for a high-risk applicant where the model predicted this person has a \~91% probability of defaulting:

> Our decision was made using an automated credit evaluation model. The primary factors contributing to this determination, ordered by their impact on the decision, are:

* #### Low Aggregate External Credit Rating (`EXT\_SOURCE\_MEAN = -2.005`, SHAP Impact: +1.09)

Your combined average score across external consumer reporting bureaus fell significantly below our minimum required approval threshold.

* #### Loan Term / Repayment Structure (`CREDIT\_TERM = 1.155`, SHAP Impact: +0.33)

The requested loan duration/repayment term length creates a elevated payment commitment relative to your risk profile.

* #### Recency / Maturity of Credit Bureau History (`mean\_days\_credit = 0.935`, SHAP Impact: +0.25)

The average age of your reported credit lines indicates a credit profile that is too recently established to meet baseline requirements.

* #### High Number of Active Open Accounts (`active\_count = 2.732`, SHAP Impact: +0.20)

You currently hold an excessive number of open, active credit obligations relative to our maximum allowance for new credit extensions.

\---

## 5\. Limitations \& Vulnerabilities

### Absence of Macroeconomic \& Time-Based Features

The model architecture does not incorporate explicit time-series attributes or macroeconomic indicator features (e.g., prevailing interest rates, unemployment metrics). Consequently, performance may degrade during macro economic shocks or sudden recessionary shifts without external underwriting adjustment overlays.

### Fair Lending \& Disparate Impact Unchecked

Formal disparate impact analysis and demographic bias assessments (e.g., evaluating Adverse Impact Ratios across protected classes) have not yet been performed. As a result, the model may reflect or perpetuate underlying biases present in the training data until a dedicated fair lending audit is completed.

### Rigid Schema \& Feature Coupling

The underlying saved pipeline artifact is strictly bound to the existing feature schema. Supplying additional data columns or altering input variables will break pipeline execution; incorporating new features or structural data changes requires full model retraining and re-validation.

### Data Quality Dependencies

High sensitivity to missing or delayed credit bureau records. Stale trade-line reporting (>60 days) can lead to temporary scoring inaccuracies

\---

## 6\. Monitoring \& Governance Plan

### Tracking Metrics \& Frequency

Monthly evaluation of performance metrics (AUROC, KS) and distribution stability.

### Population Stability Index (PSI) Thresholds \& Action Triggers

|PSI Threshold|Status|Action|
|-|-|-|
|**PSI < 0.10**|**Green (Stable)**|No action required; routine quarterly reporting.|
|**0.10 < PSI < 0.25**|**Yellow (Moderate Shift)**|Initiate root-cause analysis, perform feature-level Stability Index (CSI) audit, and increase monitoring frequency to bi-weekly.|
|**PSI > 0.25**|**Red (Significant Shift)**|Mandatory Model Retraining / Model Override Trigger. Alert Model Risk Management (MRM), implement conservative underwriting overlays, and initiate model recalibration.|

### Performance Drift Triggers

AUROC drop > 0.03 or KS drop > 5 from validation benchmark for two consecutive months triggers immediate model review.

