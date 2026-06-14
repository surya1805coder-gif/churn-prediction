# Customer Churn Prediction

A production-grade machine learning project that predicts whether a telecom customer will cancel their subscription. Deployed as an interactive **Streamlit web app** for real-time risk scoring.

---

## The Business Problem

Telecom companies lose **26.5% of customers** on average. Each lost customer means months of lost revenue plus the cost of acquiring a replacement. By identifying at-risk customers *before* they leave, the business can:

- Offer targeted retention discounts
- Proactively address service issues
- Optimize marketing spend on customers who actually need it

**Goal:** Predict churn with enough precision and recall to run a cost-effective retention campaign.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.13 |
| **Data Processing** | pandas, numpy, scikit-learn |
| **Modeling** | XGBoost, Logistic Regression, Random Forest |
| **Hyperparameter Tuning** | GridSearchCV (5-fold CV, F1-optimized) |
| **Interpretation** | SHAP (TreeExplainer) |
| **Web App** | Streamlit |
| **Serialization** | joblib |

---

## Pipeline Summary

```
Raw CSV (7,043 x 21)
│
├─ Data Cleaning
│  ├─ Drop customerID (non-predictive)
│  ├─ TotalCharges: blanks → median imputation
│  └─ SeniorCitizen: cast to categorical
│
├─ Feature Engineering
│  ├─ One-hot encode 16 categoricals (drop_first)
│  ├─ Churn: Yes→1, No→0
│  ├─ StandardScaler (fit on train, transform test)
│  └─ Stratified 80/20 train/test split
│
├─ Modeling
│  ├─ Logistic Regression (baseline)
│  ├─ Random Forest (ensemble)
│  └─ XGBoost (gradient boosted) ← Best
│
├─ Tuning
│  └─ GridSearchCV: C, class_weight, max_depth,
│                   scale_pos_weight, learning_rate
│
└─ Interpretation
   └─ SHAP TreeExplainer → top churn drivers identified
```

---

## Key Results

| Model | Accuracy | Precision | Recall | **F1** | **AUC** |
|---|---|---|---|---|---|
| Logistic Regression (tuned) | 0.739 | 0.505 | 0.781 | **0.613** | **0.841** |
| Random Forest (tuned) | 0.767 | 0.545 | 0.738 | **0.627** | 0.839 |
| **XGBoost (tuned) ★** | 0.751 | 0.520 | **0.789** | **0.627** | **0.842** |

**XGBoost is the deployed model.** It catches **79% of churners** (Recall) while maintaining 52% precision — meaning when it flags a customer as high-risk, there's a 52% chance they'll actually churn (vs 26.5% baseline). The **ROC-AUC of 0.842** confirms strong rank-ordering ability.

---

## Top Churn Drivers (SHAP)

1. **Contract type** — Month-to-month churn at 42.7% vs 2.8% for two-year
2. **Tenure** — Most churn happens in the first 10 months
3. **Internet service** — Fiber optic customers churn ~2× more than DSL
4. **Payment method** — Electronic check users are highest-risk
5. **Monthly charges** — Every $10 increase correlates with higher churn

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Re-run the full pipeline

```bash
jupyter notebook Churn_Prediction.ipynb
```

### 3. Train deployment artifacts

```bash
python save_artifacts.py
```

### 4. Launch the Streamlit app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. Enter customer details in the sidebar and click **Predict Churn** to see the live prediction.

---

## Project Structure

```
├── Churn_Prediction.ipynb   # Full ML pipeline (33 cells)
├── app.py                    # Streamlit web application
├── save_artifacts.py         # Trains + exports model artifacts
├── requirements.txt
├── README.md
├── .gitignore
├── data/                     # Raw + processed CSVs
├── models/                   # Serialized model, scaler, preprocessor
└── assets/                   # EDA + evaluation PNGs
```

---

## Deployment (Streamlit Community Cloud)

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app** → select this repo → branch `main` → file `app.py`.
4. Under **Advanced settings**, ensure `requirements.txt` is detected (it auto-selects).
5. Click **Deploy**.

The app will be live at `https://<your-app>.streamlit.app` within a few minutes.
No additional configuration needed — the `models/` directory is tracked by git
so the `.pkl` artifacts are included in the deployment.

---

## License

This project uses the [IBM Telco Customer Churn Dataset](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) available under the CC0 public domain license.
