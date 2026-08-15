import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ks_2samp
from sklearn.metrics import (
    roc_curve,
    roc_auc_score,
    precision_recall_curve,
    average_precision_score,
    f1_score,
    RocCurveDisplay,
    PrecisionRecallDisplay,
)
from sklearn.model_selection import cross_val_predict, cross_val_score


def evaluate_and_plot_models(pipeline, classifiers, X, y, cv):
    """
    Evaluates classifiers using cross-validation, reports key metrics 
    (AUROC, Gini, KS, AUPRC, Optimal F1), and returns ROC/PR plots.

    Parameters:
    -----------
    pipeline : sklearn.pipeline.Pipeline
        Base machine learning pipeline.
    classifiers : list of tuples
        List of ('Model Name', classifier_instance) tuples.
    X : array-like
        Feature dataset.
    y : array-like
        Target labels.
    cv : cross-validation generator
        e.g., StratifiedKFold.

    Returns:
    --------
    metrics_df : pd.DataFrame
        Summary table containing AUROC, Gini, KS, AUPRC, and Optimal F1 scores.
    fig_roc, fig_pr : tuple of matplotlib.figure.Figure
        The generated ROC and Precision-Recall figure objects.
    """
    metrics_records = []
    model_results = {}

    y_array = np.array(y)

    for name, clf in classifiers:
        pipeline.set_params(classifier=clf)

        # 1. Per-fold cross-validation scores for mean and std
        auroc_cv = cross_val_score(pipeline, X, y, cv=cv, scoring="roc_auc")
        ap_cv = cross_val_score(pipeline, X, y, cv=cv, scoring="average_precision")

        auroc_mean, auroc_std = auroc_cv.mean(), auroc_cv.std()
        ap_mean, ap_std = ap_cv.mean(), ap_cv.std()

        # 2. Out-of-fold predicted probabilities for positive class
        y_prob = cross_val_predict(pipeline, X, y, cv=cv, method="predict_proba")[:, 1]

        # 3. Overall Out-of-Fold AUROC & Gini Coefficient
        gini = 2 * auroc_mean - 1

        # 4. Kolmogorov-Smirnov (KS) Statistic
        # Compares probability distribution of positive vs. negative class
        prob_pos = y_prob[y_array == 1]
        prob_neg = y_prob[y_array == 0]
        ks_stat, _ = ks_2samp(prob_pos, prob_neg)

        # 5. Optimal Threshold & Max F1 Score (Youden's J Statistic: TPR - FPR)
        fpr, tpr, thresholds = roc_curve(y_array, y_prob)
        j_scores = tpr - fpr
        optimal_idx = np.argmax(j_scores)
        optimal_threshold = thresholds[optimal_idx]

        # Calculate F1 score at the optimal threshold
        y_pred_opt = (y_prob >= optimal_threshold).astype(int)
        opt_f1 = f1_score(y_array, y_pred_opt)

        # Record metrics
        metrics_records.append({
            "Model": name,
            "CV AUROC": f"{auroc_mean:.4f} (±{auroc_std:.4f})",
            "Gini": f"{gini:.4f}",
            "KS Statistic": f"{ks_stat:.4f}",
            "CV AUPRC": f"{ap_mean:.4f} (±{ap_std:.4f})",
            "Optimal Threshold": f"{optimal_threshold:.4f}",
            "F1 @ Optimal Thresh": f"{opt_f1:.4f}",
        })

        model_results[name] = {
            "y_prob": y_prob,
            "auroc_mean": auroc_mean,
            "auroc_std": auroc_std,
            "ap_mean": ap_mean,
            "ap_std": ap_std,
        }

    # Convert metrics into a structured summary DataFrame
    metrics_df = pd.DataFrame(metrics_records).set_index("Model")

    # -------------------------------------------------------------------
    # Figure 1: Receiver Operating Characteristic (ROC) Curves
    # -------------------------------------------------------------------
    fig_roc, ax_roc = plt.subplots(figsize=(8, 6))

    for name, res in model_results.items():
        label_text = f"{name} (Mean AUROC = {res['auroc_mean']:.4f} ± {res['auroc_std']:.4f})"
        RocCurveDisplay.from_predictions(
            y_array,
            res["y_prob"],
            name=label_text,
            ax=ax_roc
        )

    ax_roc.plot([0, 1], [0, 1], "k--", label="Chance Level (AUROC = 0.5000)")
    ax_roc.set_title("Out-of-Fold ROC Curves", fontsize=14, fontweight="bold")
    ax_roc.set_xlabel("False Positive Rate", fontsize=12)
    ax_roc.set_ylabel("True Positive Rate", fontsize=12)
    ax_roc.legend(loc="lower right", fontsize=10)
    ax_roc.grid(True, linestyle="--", alpha=0.6)
    fig_roc.tight_layout()

    # -------------------------------------------------------------------
    # Figure 2: Precision-Recall (PR) Curves
    # -------------------------------------------------------------------
    fig_pr, ax_pr = plt.subplots(figsize=(8, 6))
    baseline_precision = y_array.mean()

    for name, res in model_results.items():
        label_text = f"{name} (Mean PR-AUC = {res['ap_mean']:.4f} ± {res['ap_std']:.4f})"
        PrecisionRecallDisplay.from_predictions(
            y_array,
            res["y_prob"],
            name=label_text,
            ax=ax_pr
        )

    ax_pr.axhline(
        y=baseline_precision,
        color="k",
        linestyle="--",
        label=f"Baseline ({baseline_precision:.4f})"
    )
    ax_pr.set_title("Out-of-Fold Precision-Recall Curves", fontsize=14, fontweight="bold")
    ax_pr.set_xlabel("Recall", fontsize=12)
    ax_pr.set_ylabel("Precision", fontsize=12)
    ax_pr.legend(loc="lower left", fontsize=10)
    ax_pr.grid(True, linestyle="--", alpha=0.6)
    fig_pr.tight_layout()

    return metrics_df, fig_roc, fig_pr