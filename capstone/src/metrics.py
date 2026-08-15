"""
metrics.py - Reusable utility functions for model evaluation, 
population stability analysis, and SHAP explainability.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold
import seaborn as sns
import shap
from sklearn.preprocessing import StandardScaler
from sklearn.base import clone
from sklearn.metrics import roc_curve, average_precision_score, roc_auc_score, precision_recall_curve, f1_score
from sklearn.model_selection import StratifiedKFold

def compute_psi(expected, actual, bins=10):
    """
    Compute Population Stability Index (PSI) between two distributions safely.
    
    Parameters
    ----------
    expected : array-like or pd.Series
        Baseline distribution (e.g., training feature data).
    actual : array-like or pd.Series
        Comparison distribution (e.g., test feature data).
    bins : int, default=10
        Number of quantile bins to evaluate.
        
    Returns
    -------
    float
        Calculated PSI value.
    """
    exp_clean = pd.Series(expected).dropna()
    act_clean = pd.Series(actual).dropna()
    
    # Generate quantiles and force unique boundaries to handle duplicate values/ties
    breakpoints = np.quantile(exp_clean, np.linspace(0, 1, bins + 1))
    breakpoints = np.unique(breakpoints)
    
    # Fallback to simple min/max binning if non-unique quantiles fail
    if len(breakpoints) <= 2:
        breakpoints = np.linspace(exp_clean.min(), exp_clean.max(), bins + 1)
        
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf
    
    exp_counts = np.histogram(exp_clean, breakpoints)[0]
    act_counts = np.histogram(act_clean, breakpoints)[0]
    
    exp_pct = np.clip(exp_counts / exp_counts.sum(), 0.001, None)
    act_pct = np.clip(act_counts / act_counts.sum(), 0.001, None)
    
    return float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))


def calculate_psi_dataframe(df_train, df_test):
    """
    Computes PSI for all matching columns across train and test sets.
    """
    psi_results = []
    for col in df_train.columns:
        psi_val = compute_psi(df_train[col], df_test[col])
        status = 'Stable' if psi_val < 0.1 else ('Moderate Shift' if psi_val < 0.25 else 'REVIEW NEEDED')
        psi_results.append({'Feature': col, 'PSI': round(psi_val, 4), 'Status': status})
    
    return pd.DataFrame(psi_results)


def compute_holdout_metrics(y_true, y_proba, cv_auroc_mean):
    """
    Calculates AUROC, Gini, KS statistic, and AUPRC metrics.
    """
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    ks = max(tpr - fpr)
    auprc = np.abs(average_precision_score(y_true, y_proba))

    # 2. Precision-Recall Curve & Max F1 Calculation
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    
    # Calculate F1 score for all threshold steps (avoid division by zero)
    f1_scores = np.divide(
        2 * precisions * recalls,
        precisions + recalls,
        out=np.zeros_like(precisions),
        where=(precisions + recalls) != 0
    )
    
    # Find max F1 score and its corresponding threshold
    opt_idx = np.argmax(f1_scores)
    max_f1 = f1_scores[opt_idx]
    # precision_recall_curve returns len(thresholds) = len(precision) - 1
    optimal_threshold = thresholds[opt_idx] if opt_idx < len(thresholds) else 1.0
    
    # Option to calculate direct test AUROC or retain CV mean
    holdout_auroc = cv_auroc_mean
    gini = 2 * holdout_auroc - 1

    metrics_df = pd.DataFrame([{
    'Metric': 'Mean AUROC', 'Value': f'{holdout_auroc:.4f}', 'Interpretation': f'Model discriminates well' if holdout_auroc > 0.7 else 'Weak',
    }, {
    'Metric': 'Gini', 'Value': f'{gini:.4f}', 'Interpretation': f'Good' if gini > 0.3 else 'Weak',
    }, {
    'Metric': 'KS', 'Value': f'{ks:.4f}', 'Interpretation': f'Good separation' if ks > 0.3 else 'Moderate',
    }, {
    'Metric': 'AUPRC', 'Value': f'{auprc:.4f}', 'Interpretation': f'Above baseline ({y_true.mean():.4f})',
    }, {
    'Metric': 'F1', 'Value': f'{max_f1:.4f}', 'Interpretation': f'Optimal threshold: {optimal_threshold:.4f}',
    }])
    return metrics_df

def calculate_ks(y_true, y_pred_proba):
    """Calculates the Kolmogorov-Smirnov (KS) statistic."""
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    return np.max(tpr - fpr)


def evaluate_val_folds_plot(
    full_pipeline, X_train_raw, y_train, n_splits=5, random_state=42, f1_threshold=0.5
):
    """Evaluates an end-to-end sklearn Pipeline across Stratified K-Folds using raw DataFrames,

    calculates AUROC, AUC-PR, Gini, KS Metric, and F1 Score per fold, prints summary metrics,
    and plots fold performance across all metrics.
    """
    # 1. Initialize the stratified splitter
    skf = StratifiedKFold(
        n_splits=n_splits, shuffle=True, random_state=random_state
    )

    # 2. Storage for tracking fold performance
    metrics_history = {
        "AUROC": [],
        "AUC-PR": [],
        "Gini": [],
        "KS Metric": [],
        "F1 Score": [],
    }

    # Ensure inputs are pandas DataFrames/Series for proper iloc slicing
    if not isinstance(X_train_raw, pd.DataFrame):
        X_train_raw = pd.DataFrame(X_train_raw)
    if not isinstance(y_train, (pd.Series, np.ndarray)):
        y_train = pd.Series(y_train)

    # 3. Loop through the stratified splits
    for fold, (train_idx, val_idx) in enumerate(
        skf.split(X_train_raw, y_train), 1
    ):
        X_tr = X_train_raw.iloc[train_idx]
        X_val = X_train_raw.iloc[val_idx]

        y_tr = (
            y_train.iloc[train_idx]
            if isinstance(y_train, pd.Series)
            else y_train[train_idx]
        )
        y_val = (
            y_train.iloc[val_idx]
            if isinstance(y_train, pd.Series)
            else y_train[val_idx]
        )

        # Clone and fit
        fold_pipeline = clone(full_pipeline)
        fold_pipeline.fit(X_tr, y_tr)

        # Predict probabilities
        y_pred_proba = fold_pipeline.predict_proba(X_val)[:, 1]

        # --- Calculate Metrics ---
        # 1. AUROC
        auroc = roc_auc_score(y_val, y_pred_proba)

        # 2. AUC-PR (using trapezoidal integration over precision-recall curve)
        precision, recall, _ = precision_recall_curve(y_val, y_pred_proba)
        auc_pr = np.trapz(precision, recall)

        # 3. Gini Score (2 * AUROC - 1)
        gini = 2 * auroc - 1

        # 4. KS Metric (Max distance between TPR and FPR)
        ks = calculate_ks(y_val, y_pred_proba)

        # 5. F1 Score (evaluated at specified probability threshold)
        y_pred_class = (y_pred_proba >= f1_threshold).astype(int)
        f1 = f1_score(y_val, y_pred_class)

        # Store metrics
        metrics_history["AUROC"].append(auroc)
        metrics_history["AUC-PR"].append(auc_pr)
        metrics_history["Gini"].append(gini)
        metrics_history["KS Metric"].append(ks)
        metrics_history["F1 Score"].append(f1)

        print(
            f"Fold {fold} | AUROC: {auroc:.4f} | AUC-PR: {auc_pr:.4f} | "
            f"Gini: {gini:.4f} | KS: {ks:.4f} | F1: {f1:.4f}"
        )

    # 4. Print aggregate summary
    print("\n" + "=" * 50)
    print("CV SUMMARY PERFORMANCE")
    print("=" * 50)
    for metric_name, scores in metrics_history.items():
        print(
            f"Mean {metric_name:10s}: {np.mean(scores):.4f} (+/- {np.std(scores):.4f})"
        )

    # 5. Plotting multi-metric comparison chart
    folds = [f"Fold {i}" for i in range(1, n_splits + 1)]
    plt.figure(figsize=(10, 6))

    for metric_name, scores in metrics_history.items():
        plt.plot(folds, scores, marker="o", label=metric_name, linewidth=2)

    plt.title("Cross-Validation Metrics Across Folds", fontsize=14, fontweight="bold")
    plt.xlabel("Folds", fontsize=12)
    plt.ylabel("Score", fontsize=12)
    plt.ylim(0, 1.05)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.show()

    return metrics_history

def generate_shap_waterfalls(full_pipeline, X_train_raw, X_test_raw, model_name="Model", n_samples=1000):
    """
    Generates SHAP waterfall plots for High Risk, Borderline, and Low Risk instances
    directly from raw input DataFrames using a fitted end-to-end sklearn Pipeline.
    """
    # 1. Extract feature transformation steps (all steps except the final classifier)
    preprocessor_pipeline = Pipeline(full_pipeline.steps[:-1])
    fitted_clf = full_pipeline.steps[-1][1]

    # 2. Transform raw data into model-ready arrays
    X_train_proc = preprocessor_pipeline.transform(X_train_raw)
    X_test_proc = preprocessor_pipeline.transform(X_test_raw)

    # 3. Safely extract feature names directly from the transformed object
    if isinstance(X_train_proc, pd.DataFrame):
        features = list(X_train_proc.columns)
    elif hasattr(preprocessor_pipeline.steps[-1][1], "get_feature_names_out"):
        # Get names from the last preprocessor step (e.g. StandardScaler / ColumnTransformer)
        features = list(preprocessor_pipeline.steps[-1][1].get_feature_names_out())
    else:
        features = [f"feature_{i}" for i in range(X_train_proc.shape[1])]

    # Convert matrices to numpy arrays if they are DataFrames/Series for uniform slicing
    X_train_arr = X_train_proc.to_numpy() if isinstance(X_train_proc, (pd.DataFrame, pd.Series)) else X_train_proc
    X_test_arr = X_test_proc.to_numpy() if isinstance(X_test_proc, (pd.DataFrame, pd.Series)) else X_test_proc

    # 4. Slice test sample for SHAP calculation
    n_eval = min(n_samples, len(X_test_arr))
    X_sample = X_test_arr[:n_eval]

    # 5. Instantiate Explainer based on final classifier type
    model_name_str = type(fitted_clf).__name__

    if hasattr(fitted_clf, "tree_output") or any(
        k in model_name_str for k in ["RandomForest", "LGBM", "XGB", "DecisionTree", "ExtraTrees"]
    ):
        explainer = shap.TreeExplainer(fitted_clf)
        shap_values = explainer.shap_values(X_sample)
        sv = shap_values[1] if isinstance(shap_values, list) else shap_values
        ev = explainer.expected_value[1] if isinstance(explainer.expected_value, (list, np.ndarray)) else explainer.expected_value
    else:
        explainer = shap.LinearExplainer(fitted_clf, X_train_arr)
        shap_values = explainer.shap_values(X_sample)
        sv = shap_values
        ev = explainer.expected_value

    # 6. Get predicted probabilities on raw test slice using the full pipeline
    y_proba_sample = full_pipeline.predict_proba(X_test_raw.iloc[:n_eval])[:, 1]

    # 7. Identify risk profile index targets
    high_risk = np.argmax(y_proba_sample)
    low_risk = np.argmin(y_proba_sample)
    borderline = np.argmin(np.abs(y_proba_sample - 0.30))

    profiles = [("High Risk", high_risk), ("Borderline", borderline), ("Low Risk", low_risk)]

    # 8. Render SHAP Waterfall Plots
    for risk_label, idx in profiles:
        plt.figure()
        sample_sv = sv[idx]

        # Select positive class if 2D array returned per instance
        if hasattr(sample_sv, "ndim") and sample_sv.ndim > 1:
            sample_sv = sample_sv[:, 1]

        sample_ev = ev[1] if isinstance(ev, (list, np.ndarray)) and len(ev) > 1 else ev

        explanation = shap.Explanation(
            values=sample_sv,
            base_values=sample_ev,
            data=X_sample[idx],
            feature_names=features
        )

        shap.waterfall_plot(explanation, max_display=10, show=False)
        plt.title(f"{model_name} - {risk_label} (PD={y_proba_sample[idx]:.4f})")
        plt.tight_layout()
        plt.show()

def model_monitoring_dashboard(full_pipeline, X_train_raw, y_train, X_test_raw, f1_threshold, n_samples=1000):
    """
    Generates model monitoring visuals (SHAP Beeswarm, SHAP Bar, Top 10 Feature PSI Heatmap)
    preserving exact feature names from the preprocessing steps.
    """
    # 1. Separate preprocessor steps and model
    preprocessor_pipeline = Pipeline(full_pipeline.steps[:-1])
    model = full_pipeline.steps[-1][1]

    # Force scikit-learn steps to return pandas DataFrames where possible
    try:
        preprocessor_pipeline.set_output(transform="pandas")
    except Exception:
        pass

    # 2. Transform raw data
    X_train_proc = preprocessor_pipeline.transform(X_train_raw)
    X_test_proc = preprocessor_pipeline.transform(X_test_raw)

    # 3. Extract feature names reliably
    features = None

    # Case A: Transformed output is already a DataFrame with valid column names
    if isinstance(X_train_proc, pd.DataFrame) and not str(X_train_proc.columns[0]).startswith("feature_"):
        features = list(X_train_proc.columns)
        X_train_df = X_train_proc
        X_test_df = X_test_proc
    else:
        # Case B: Extract column names from the internal ColumnTransformer step
        for name, step in reversed(preprocessor_pipeline.steps):
            if hasattr(step, "get_feature_names_out"):
                try:
                    features = list(step.get_feature_names_out())
                    break
                except Exception:
                    continue
            elif hasattr(step, "preprocessor_") and hasattr(step.preprocessor_, "get_feature_names_out"):
                features = list(step.preprocessor_.get_feature_names_out())
                break

        # Fallback if no step provided feature names
        if features is None:
            if isinstance(X_train_raw, pd.DataFrame):
                features = list(X_train_raw.columns)
            else:
                features = [f"feature_{i}" for i in range(X_train_proc.shape[1])]

        # Re-construct DataFrames with verified feature names
        X_train_df = pd.DataFrame(X_train_proc, columns=features)
        X_test_df = pd.DataFrame(X_test_proc, columns=features)

    # 4. Compute SHAP explanations on test slice
    n_eval = min(n_samples, len(X_test_df))
    X_sample = X_test_df.iloc[:n_eval]

    model_name_str = type(model).__name__
    if hasattr(model, "tree_output") or any(
        k in model_name_str for k in ["RandomForest", "LGBM", "XGB", "DecisionTree", "ExtraTrees"]
    ):
        explainer = shap.TreeExplainer(model)
    else:
        explainer = shap.LinearExplainer(model, X_train_df)

    # Calculate SHAP values as an Explanation object
    explanation = explainer(X_sample)
    
    # Force SHAP object to use human-readable feature names
    explanation.feature_names = features

    # 5. SHAP Beeswarm Plot
    plt.figure(figsize=(10, 6))
    shap.plots.beeswarm(explanation, max_display=15, show=False)
    plt.title("SHAP Summary Beeswarm Plot", fontsize=14, pad=10)
    plt.tight_layout()
    plt.show()

    # 6. SHAP Bar Plot
    plt.figure(figsize=(10, 6))
    shap.plots.bar(explanation, max_display=15, show=False)
    plt.title("Mean |SHAP Value| Feature Importance", fontsize=14, pad=10)
    plt.tight_layout()
    plt.show()

    # 7. Extract Top 10 Features by Importance
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_[0])
    else:
        importances = np.ones(len(features))

    df_imp = pd.DataFrame({"feature": features, "importance": importances})
    df_top10 = df_imp.sort_values(by="importance", ascending=False).head(10)
    top10_features = df_top10["feature"].tolist()

    # 8. Compute Feature PSI for Top 10 Features
    df_psi = calculate_psi_dataframe(X_train_df, X_test_df).drop("Status", axis=1)

    heatmap_data = df_psi[df_psi["Feature"].isin(top10_features)].set_index("Feature")[["PSI"]]

    # 9. PSI Heatmap
    colors = ["#2ecc71", "#f1c40f", "#e74c3c"]
    cmap = sns.blend_palette(colors, as_cmap=True)

    plt.figure(figsize=(6, 6))
    sns.heatmap(
        heatmap_data,
        annot=True,
        fmt=".3f",
        cmap=cmap,
        vmin=0,
        vmax=0.5,
        linewidths=0.5,
        cbar_kws={"label": "Population Stability Index"}
    )
    plt.title("Feature PSI Alert Dashboard", fontsize=14, pad=15)
    plt.ylabel("Model Features")
    plt.tight_layout()
    plt.show()

    evaluate_val_folds_plot(full_pipeline, X_train_raw, y_train, n_splits=5, random_state=42, f1_threshold=f1_threshold)
    