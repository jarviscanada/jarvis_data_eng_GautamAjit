"""
preprocessing.py
----------------
Pipeline construction, evaluation, and unsupervised customer segmentation transformers.
"""

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.cluster import MiniBatchKMeans
import pandas as pd

def build_preprocessing_pipeline(
    num_cols: list,
    ordinal_cols: list,
    ohe_cols: list,
    freq_cols: list,
    education_order: list,
) -> ColumnTransformer:
    """Builds a scikit-learn ColumnTransformer for numerical, ordinal, and one-hot features."""
    num_transformer = Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))])

    ordinal_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "ordinal",
                OrdinalEncoder(
                    categories=[education_order],
                    handle_unknown="use_encoded_value",
                    unknown_value=-1,
                ),
            ),
        ]
    )

    ohe_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("ohe", OneHotEncoder(sparse_output=False, handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_transformer, num_cols),
            ("ord", ordinal_transformer, ordinal_cols),
            ("ohe", ohe_transformer, ohe_cols),
            ("freq", "passthrough", freq_cols),
        ],
        remainder="drop",
    )

    return preprocessor


def evaluate_missingness_predictiveness(df, missing_indicator_cols, target_col="TARGET"):
    """Evaluates the predictive power of missingness flags using Logistic Regression."""
    if not missing_indicator_cols:
        print("No missingness indicators provided.")
        return None, None

    df = df.dropna(subset=[target_col])
    X = df[missing_indicator_cols]
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = LogisticRegression(max_iter=1000, random_state=42, class_weight="balanced")
    clf.fit(X_train, y_train)

    y_pred_proba = clf.predict_proba(X_test)[:, 1]
    auroc = roc_auc_score(y_test, y_pred_proba)

    print(f"Logistic Regression ROC-AUC (Missingness Indicators Only): {auroc:.4f}")
    return auroc, clf


class ClusterSegmenter(BaseEstimator, TransformerMixin):
    """Fits MiniBatchKMeans clustering on specified scaled features and appends cluster labels."""

    def __init__(self, cluster_features: list, n_clusters: int = 2, random_state: int = 42):
        self.cluster_features = cluster_features
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.kmeans = MiniBatchKMeans(
            n_clusters=self.n_clusters,
            batch_size=4096,
            random_state=self.random_state,
            n_init=10,
            max_iter=100,
        )

    def fit(self, X, y=None):
        X_sub = X[self.cluster_features]
        X_scaled = self.scaler.fit_transform(X_sub).astype("float32")
        self.kmeans.fit(X_scaled)
        return self

    def transform(self, X):
        X_out = X.copy()
        X_sub = X_out[self.cluster_features]
        X_scaled = self.scaler.transform(X_sub).astype("float32")
        X_out["customer_segment"] = self.kmeans.predict(X_scaled)
        return X_out

class DynamicPreprocessingPipeline(BaseEstimator, TransformerMixin):
    """
    Dynamically identifies column dtypes post-feature engineering
    and routes them into the build_preprocessing_pipeline.
    """
    def __init__(self, education_categories, ordinal_cols, ohe_cols, freq_cols):
        self.education_categories = education_categories
        self.ordinal_cols = ordinal_cols
        self.ohe_cols = ohe_cols
        self.freq_cols = freq_cols
        self.preprocessor_ = None
        self.feature_names_out_ = None

    def fit(self, X, y=None):
        ignore_cols = ["SK_ID_CURR", "TARGET"] + self.ordinal_cols + self.ohe_cols + self.freq_cols
        num_cols = [
            c for c in X.select_dtypes(include=["number"]).columns
            if c not in ignore_cols
        ]
        
        self.preprocessor_ = build_preprocessing_pipeline(
            num_cols=num_cols,
            ordinal_cols=self.ordinal_cols,
            ohe_cols=self.ohe_cols,
            freq_cols=self.freq_cols,
            education_order=self.education_categories,
        )
        self.preprocessor_.fit(X, y)
        self.feature_names_out_ = self.preprocessor_.get_feature_names_out()
        return self

    def transform(self, X):
        X_arr = self.preprocessor_.transform(X)
        return pd.DataFrame(X_arr, columns=self.feature_names_out_, index=X.index)


class ClusterSegmenterWrapper(BaseEstimator, TransformerMixin):
    """
    Wrapper around ClusterSegmenter that manages ID column preservation.
    """
    def __init__(self, cluster_features, n_clusters=2):
        self.cluster_features = cluster_features
        self.n_clusters = n_clusters
        self.segmenter = ClusterSegmenter(cluster_features=cluster_features, n_clusters=n_clusters)

    def fit(self, X, y=None):
        self.segmenter.fit(X, y)
        return self

    def transform(self, X):
        # ClusterSegmenter expects a DataFrame and adds segment features
        X_out = self.segmenter.transform(X)
        
        # Drop ID columns before passing to scaling/modeling steps
        if "SK_ID_CURR" in X_out.columns:
            X_out = X_out.drop(columns=["SK_ID_CURR"])
        if "TARGET" in X_out.columns:
            X_out = X_out.drop(columns=["TARGET"])
            
        return X_out