"""Deterministic synthetic-data training. Run: python -m ml.train"""
import json
import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from ml.features import FEATURES, NUMERIC_FEATURES, CATEGORICAL_FEATURES


def make_dataset(n=3500, seed=42):
    rng = np.random.default_rng(seed)
    tenure = rng.integers(1, 73, size=n)
    spend = np.round(rng.uniform(15, 160, size=n), 2)
    tickets = rng.poisson(1.6, size=n)
    contract = rng.choice(["monthly", "annual"], size=n, p=[0.65, 0.35])
    autopay = rng.choice(["yes", "no"], size=n, p=[0.6, 0.4])
    # Hidden synthetic signal only: not an empirical business model.
    logit = (-0.9 - 0.032 * tenure + 0.011 * spend + 0.44 * tickets
             + 1.1 * (contract == "monthly") + 0.65 * (autopay == "no"))
    prob = 1 / (1 + np.exp(-logit))
    churn = rng.binomial(1, prob)
    return pd.DataFrame({"tenure_months": tenure, "monthly_spend": spend,
                         "support_tickets": tickets, "contract_type": contract,
                         "auto_pay": autopay, "churn": churn})


def train(output_dir=None):
    directory = Path(output_dir or os.getenv("MODEL_DIR", "artifacts"))
    directory.mkdir(parents=True, exist_ok=True)
    df = make_dataset()
    X_train, X_test, y_train, y_test = train_test_split(
        df[FEATURES], df["churn"], test_size=0.25, random_state=42,
        stratify=df["churn"])
    preprocessing = ColumnTransformer([
        ("numbers", StandardScaler(), NUMERIC_FEATURES),
        ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])
    model = Pipeline([("preprocess", preprocessing),
                      ("classifier", LogisticRegression(max_iter=1000, random_state=42))])
    model.fit(X_train, y_train)
    probabilities = model.predict_proba(X_test)[:, 1]
    metrics = {"accuracy": round(float(accuracy_score(y_test, probabilities >= 0.5)), 4),
               "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
               "test_examples": int(len(y_test)), "train_examples": int(len(X_train)),
               "data_source": "synthetic", "decision_threshold": 0.5}
    joblib.dump(model, directory / "model.joblib")
    (directory / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print("Saved model and metrics to", directory, metrics)
    return metrics


if __name__ == "__main__":
    train()
