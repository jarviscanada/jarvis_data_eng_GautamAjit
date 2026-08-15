"""
feature_engineering.py
----------------------
Custom transformers, aggregations, and feature creation classes.
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


def process_bureau_data(df_bureau: pd.DataFrame) -> pd.DataFrame:
    """Processes bureau dataset independently so it can be merged onto train or test."""
    df_bur = df_bureau.copy()
    df_bur["IS_ACTIVE"] = (df_bur["CREDIT_ACTIVE"] == "Active").astype(int)

    bureau_agg = (
        df_bur.groupby("SK_ID_CURR")
        .agg(
            num_bureau_records=("SK_ID_CURR", "size"),
            active_count=("IS_ACTIVE", "sum"),
            mean_days_credit=("DAYS_CREDIT", "mean"),
            max_amt_credit_sum_overdue=("AMT_CREDIT_SUM_OVERDUE", "max"),
        )
        .reset_index()
    )
    return bureau_agg


class DropHighMissingColumns(BaseEstimator, TransformerMixin):
    """Drops columns exceeding a missingness threshold, respecting exclusions."""

    def __init__(self, threshold=65.0, exclude=None):
        self.threshold = threshold
        self.exclude = exclude if exclude is not None else ["OWN_CAR_AGE"]
        self.drop_cols_ = []

    def fit(self, X, y=None):
        missing_pct = (X.isnull().sum() / len(X)) * 100
        cols_to_drop = missing_pct[missing_pct > self.threshold].index.tolist()
        self.drop_cols_ = [c for c in cols_to_drop if c not in self.exclude]
        return self

    def transform(self, X):
        return X.drop(columns=self.drop_cols_, errors="ignore")


class AddMissingIndicators(BaseEstimator, TransformerMixin):
    """Creates binary missingness indicator columns for features with missingness above threshold."""

    def __init__(self, threshold=5.0, prefix="_IS_MISSING"):
        self.threshold = threshold
        self.prefix = prefix
        self.indicator_cols_ = []

    def fit(self, X, y=None):
        missing_pct = (X.isnull().sum() / len(X)) * 100
        target_cols = missing_pct[missing_pct > self.threshold].index.tolist()
        if "TARGET" in target_cols:
            target_cols.remove("TARGET")
        self.indicator_cols_ = target_cols
        return self

    def transform(self, X):
        X_out = X.copy()
        for col in self.indicator_cols_:
            if col in X_out.columns:
                X_out[f"{col}{self.prefix}"] = X_out[col].isnull().astype(int)
        return X_out


class ApplicationFeatureEngineer(BaseEstimator, TransformerMixin):
    """Engineers domain ratios, external source statistics, age buckets, and cleans anomalies."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy()

        # Handle sentinel values & AGE
        if "DAYS_BIRTH" in df.columns:
            df["AGE"] = -df["DAYS_BIRTH"] / 365.0
            df = df.drop(columns=["DAYS_BIRTH"])

        if "DAYS_EMPLOYED" in df.columns:
            df["DAYS_EMPLOYED"] = df["DAYS_EMPLOYED"].replace(365243, np.nan)

        # Domain Ratios
        if {"AMT_CREDIT", "AMT_INCOME_TOTAL"}.issubset(df.columns):
            df["CREDIT_INCOME_RATIO"] = df["AMT_CREDIT"] / df["AMT_INCOME_TOTAL"]

        if {"AMT_ANNUITY", "AMT_INCOME_TOTAL"}.issubset(df.columns):
            df["ANNUITY_INCOME_RATIO"] = df["AMT_ANNUITY"] / df["AMT_INCOME_TOTAL"]

        if {"AMT_ANNUITY", "AMT_CREDIT"}.issubset(df.columns):
            df["CREDIT_TERM"] = df["AMT_ANNUITY"] / df["AMT_CREDIT"]

        if "AGE" in df.columns and "DAYS_EMPLOYED" in df.columns:
            df["DAYS_EMPLOYED_RATIO"] = df["DAYS_EMPLOYED"] / (df["AGE"] * 365)

        if "CNT_FAM_MEMBERS" in df.columns and "AMT_INCOME_TOTAL" in df.columns:
            df["INCOME_PER_PERSON"] = df["AMT_INCOME_TOTAL"] / df["CNT_FAM_MEMBERS"]

        # External source aggregations
        ext_cols = [c for c in ["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"] if c in df.columns]
        if ext_cols:
            df["EXT_SOURCE_MEAN"] = df[ext_cols].mean(axis=1)
            df["EXT_SOURCE_STD"] = df[ext_cols].std(axis=1)

        # Age Bucket
        if "AGE" in df.columns:
            df["AGE_BUCKET"] = pd.cut(
                df["AGE"],
                bins=[20, 30, 40, 50, 60, 70, 100],
                labels=["20-30", "30-40", "40-50", "50-60", "60-70", "70-100"],
            )

        return df


class FrequencyEncoder(BaseEstimator, TransformerMixin):
    """Applies frequency encoding based on category proportions in training data."""

    def __init__(self, cols=None):
        self.cols = cols
        self.freq_maps_ = {}

    def fit(self, X, y=None):
        if self.cols is None:
            return self
        for col in self.cols:
            if col in X.columns:
                self.freq_maps_[col] = X[col].value_counts(normalize=True, dropna=False)
        return self

    def transform(self, X):
        X_out = X.copy()
        for col, freq_map in self.freq_maps_.items():
            if col in X_out.columns:
                X_out[col] = X_out[col].map(freq_map).fillna(0)
        return X_out


class HighCorrelationFilter(BaseEstimator, TransformerMixin):
    """Removes columns with absolute linear correlation higher than threshold."""

    def __init__(self, threshold: float = 0.95, method: str = "pearson"):
        self.threshold = threshold
        self.method = method
        self.to_drop_ = []

    def fit(self, X: pd.DataFrame, y=None):
        corr_matrix = X.select_dtypes(include=[np.number]).corr(method=self.method).abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        self.to_drop_ = [column for column in upper.columns if any(upper[column] >= self.threshold)]
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        return X.drop(columns=self.to_drop_, errors="ignore")

class BureauMergerAndImputer(BaseEstimator, TransformerMixin):
    """
    Processes bureau records, merges them into application data by SK_ID_CURR,
    and flags/imputes missing bureau features.
    """
    def __init__(self, df_bureau, bureau_features=None):
        self.df_bureau = df_bureau
        self.bureau_features = bureau_features or [
            "num_bureau_records",
            "active_count",
            "mean_days_credit",
            "max_amt_credit_sum_overdue",
        ]
        self.bureau_agg_ = None

    def fit(self, X, y=None):
        # Aggregate bureau data once during fit
        self.bureau_agg_ = process_bureau_data(self.df_bureau)
        return self

    def transform(self, X):
        X_out = X.copy()
        X_out = X_out.merge(self.bureau_agg_, on="SK_ID_CURR", how="left")
        
        for col in self.bureau_features:
            if col in X_out.columns:
                X_out[f"{col}_was_missing"] = X_out[col].isna().astype(int)
                X_out[col] = X_out[col].fillna(-1)
        return X_out

        # Add this method so pipeline feature tracking works seamlessly
    def get_feature_names_out(self, input_features=None):
        if input_features is None:
            return None
        
        feature_names = list(input_features)
        if self.bureau_agg_ is not None:
            # Append new columns created during merge
            new_bureau_cols = [c for c in self.bureau_agg_.columns if c != "SK_ID_CURR" and c not in feature_names]
            feature_names.extend(new_bureau_cols)
            
            # Append missing flags created during transform
            for col in self.bureau_features:
                flag_col = f"{col}_was_missing"
                if flag_col not in feature_names:
                    feature_names.append(flag_col)
                    
        return np.array(feature_names, dtype=object)