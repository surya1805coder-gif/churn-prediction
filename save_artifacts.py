"""
save_artifacts.py
=================
Replicates the exact preprocessing pipeline from Churn_Prediction.ipynb,
trains the best model (XGBoost) on the full dataset, and saves all
artifacts needed for the Streamlit deployment.

Saved to models/:
  - model.pkl          : Trained XGBoost classifier
  - scaler.pkl         : Fitted StandardScaler
  - preprocessor.pkl   : Metadata dict for aligning new data
"""

import pandas as pd
import numpy as np
import joblib
import warnings
import xgboost as xgb
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

DATA_PATH = "data/WA_Fn-UseC_-Telco-Customer-Churn.csv"
MODELS_DIR = "models/"

# ── 1. Load & Clean ──────────────────────────────────────────────────────
df = pd.read_csv(DATA_PATH)
df.drop(columns=["customerID"], inplace=True)

df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
totalcharges_median = df["TotalCharges"].median()
df["TotalCharges"] = df["TotalCharges"].fillna(totalcharges_median)

df["SeniorCitizen"] = df["SeniorCitizen"].astype(object)

# ── 2. Encode Target ─────────────────────────────────────────────────────
df["Churn"] = df["Churn"].map({"Yes": 1, "No": 0})

# ── 3. One-Hot Encode ────────────────────────────────────────────────────
cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
if "Churn" in cat_cols:
    cat_cols.remove("Churn")

df_encoded = pd.get_dummies(df, columns=cat_cols, drop_first=True)
for col in df_encoded.select_dtypes("bool").columns:
    df_encoded[col] = df_encoded[col].astype(int)

feature_columns = [c for c in df_encoded.columns if c != "Churn"]

# ── 4. Scale — fit on full dataset ───────────────────────────────────────
X = df_encoded[feature_columns]
y = df_encoded["Churn"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ── 5. Train Best Model (XGBoost, tuned params from notebook) ──────────
# Parameters discovered by GridSearchCV in the notebook:
#   learning_rate=0.1, max_depth=4, scale_pos_weight=2.77, subsample=1.0
scale_pos_weight = (y == 0).sum() / (y == 1).sum()

model = xgb.XGBClassifier(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=4,
    subsample=1.0,
    scale_pos_weight=scale_pos_weight,
    random_state=42,
    eval_metric="logloss",
)
model.fit(X_scaled, y)

# ── 6. Save Artifacts ────────────────────────────────────────────────────
preprocessor = {
    "feature_columns": feature_columns,
    "cat_cols": cat_cols,
    "totalcharges_median": totalcharges_median,
    "scale_pos_weight": scale_pos_weight,
}

joblib.dump(model, MODELS_DIR + "model.pkl")
joblib.dump(scaler, MODELS_DIR + "scaler.pkl")
joblib.dump(preprocessor, MODELS_DIR + "preprocessor.pkl")

print("Artifacts saved to models/:")
print("  - model.pkl         (trained XGBoost)")
print("  - scaler.pkl       (fitted StandardScaler)")
print("  - preprocessor.pkl (metadata for inference)")
print(f"\nFeature columns ({len(feature_columns)}): {feature_columns}")
print(f"TotalCharges median: {totalcharges_median}")
print(f"Aliased categories: {cat_cols}")
print(f"scale_pos_weight: {scale_pos_weight:.2f}")
