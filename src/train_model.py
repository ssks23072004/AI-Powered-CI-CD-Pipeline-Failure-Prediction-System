import os
import json
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score, precision_score,
    recall_score, f1_score, classification_report
)

import joblib

# -----------------------------
# PATHS
# -----------------------------
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH   = os.path.join(BASE_DIR, "data", "processed", "dataset.csv")
MODEL_PATH  = os.path.join(BASE_DIR, "models", "model.pkl")
RESULT_PATH = os.path.join(BASE_DIR, "models", "results.json")

# -----------------------------
# LOAD DATASET
# -----------------------------
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f"\n\n❌ Dataset not found at: {DATA_PATH}"
        f"\n   Run: python data/generate_dataset.py\n"
    )

df = pd.read_csv(DATA_PATH)

print(f"✅ Loaded dataset: {len(df)} records")
print(f"Label distribution:\n{df['label'].value_counts().to_string()}\n")

# -----------------------------
# FEATURE ENGINEERING (CLEAN)
# -----------------------------
df["has_high_error"]      = (df["error_count"] >= 3).astype(int)
df["has_many_warnings"]   = (df["warning_count"] >= 5).astype(int)
df["error_warning_ratio"] = df["error_count"] / (df["warning_count"] + 1)
df["pipeline_complexity"] = df["dependency_downloads"] * df["install_steps"]

# -----------------------------
# FEATURES (NO NOISE)
# -----------------------------
FEATURE_COLUMNS = [
    "error_count",
    "warning_count",
    "dependency_downloads",
    "install_steps",
    "has_git_clone",
    "has_high_error",
    "has_many_warnings",
    "error_warning_ratio",
    "pipeline_complexity"
]

X = df[FEATURE_COLUMNS]
y = df["label"]

# -----------------------------
# TRAIN / TEST SPLIT
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# -----------------------------
# MODELS
# -----------------------------
models = {
    "Random Forest": RandomForestClassifier(
        n_estimators=350,
        max_depth=14,
        min_samples_split=6,
        min_samples_leaf=2,
        max_features="sqrt",
        class_weight="balanced",
        bootstrap=True,
        random_state=42
    ),

    "Logistic Regression": LogisticRegression(
        max_iter=500
    ),

    "Decision Tree": DecisionTreeClassifier(
        max_depth=6,
        min_samples_split=10,
        min_samples_leaf=4,
        random_state=42
    ),

    "Gradient Boosting": GradientBoostingClassifier(
        random_state=42
    ),
}

best_model    = None
best_accuracy = 0
best_name     = ""
best_preds    = None
all_metrics   = {}

print("🔍 Model Comparison:\n")

# -----------------------------
# TRAIN + EVALUATE
# -----------------------------
for name, model in models.items():

    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    acc  = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds, zero_division=0)
    rec  = recall_score(y_test, preds, zero_division=0)
    f1   = f1_score(y_test, preds, zero_division=0)

    all_metrics[name] = {
        "accuracy":  round(acc * 100, 2),
        "precision": round(prec * 100, 2),
        "recall":    round(rec * 100, 2),
        "f1_score":  round(f1 * 100, 2),
    }

    marker = " ← BEST" if acc > best_accuracy else ""

    print(
        f"{name:<22} "
        f"Acc: {acc:.4f}  "
        f"Prec: {prec:.4f}  "
        f"Rec: {rec:.4f}  "
        f"F1: {f1:.4f}"
        f"{marker}"
    )

    if acc > best_accuracy:
        best_accuracy = acc
        best_model    = model
        best_name     = name
        best_preds    = preds

# -----------------------------
# SAVE MODEL
# -----------------------------
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
joblib.dump(best_model, MODEL_PATH)

# -----------------------------
# SAVE RESULTS
# -----------------------------
results = {
    "best_model":    best_name,
    "best_accuracy": round(best_accuracy * 100, 2),
    "models":        all_metrics,
    "dataset_size":  len(df),
    "failure_rate":  round(float(y.mean()) * 100, 2),
}

with open(RESULT_PATH, "w") as f:
    json.dump(results, f, indent=2)

# -----------------------------
# FINAL OUTPUT
# -----------------------------
print(f"\n✅ Best model : {best_name}")
print(f"   Accuracy   : {best_accuracy:.4f}")
print(f"   Saved to   : {MODEL_PATH}")
print(f"   Metrics    : {RESULT_PATH}")

print(f"\n📊 Classification Report ({best_name}):\n")
print(classification_report(y_test, best_preds))