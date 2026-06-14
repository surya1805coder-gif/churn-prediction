<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/XGBoost-tuned-00A651" alt="XGBoost">
  <img src="https://img.shields.io/badge/ROC%E2%80%93AUC-0.842-success" alt="AUC">
  <img src="https://img.shields.io/badge/F1-0.627-blue" alt="F1">
  <img src="https://img.shields.io/badge/Streamlit-deployed-FF4B4B?logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/license-CC0-lightgrey" alt="License">
</p>

<h1 align="center">Customer Churn Prediction</h1>
<p align="center">
  Predicting telecom customer churn with XGBoost — deployed as a live Streamlit app.
</p>

---

## Table of Contents

- [Business Context](#business-context)
- [Tech Stack](#tech-stack)
- [Pipeline](#pipeline)
- [Results](#results)
- [Key Drivers](#key-drivers)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [License](#license)

---

## Business Context

Telecom companies lose **26.5% of customers** on average. Each churned customer means months of lost recurring revenue plus the cost of acquiring a replacement. By identifying at-risk customers *before* they leave, the business can:

- 🎯 Offer targeted retention discounts to those who need them
- 🛠️ Proactively address service issues
- 💰 Optimize marketing spend instead of blasting everyone

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

## Pipeline

```
Raw CSV (7,043 × 21)
│
├─ Data Cleaning
│  ├─ Drop customerID (non-predictive)
│  ├─ TotalCharges: blanks → median imputation
│  └─ SeniorCitizen: cast to categorical
│
├─ Feature Engineering
│  ├─ One-hot encode 16 categoricals (drop_first)
│  ├─ Churn: Yes → 1, No → 0
│  ├─ StandardScaler (fit on train, transform test)
│  └─ Stratified 80/20 train / test split
│
├─ Modeling
│  ├─ Logistic Regression (baseline)
│  ├─ Random Forest (ensemble)
│  └─ XGBoost (gradient boosted) ← **chosen for deployment**
│
├─ Tuning
│  └─ GridSearchCV: C, class_weight, max_depth,
│                    scale_pos_weight, learning_rate
│
└─ Interpretation
   └─ SHAP TreeExplainer → top churn drivers identified
```

---

## Results

| Model | Accuracy | Precision | Recall | **F1** | **AUC** |
|---|---|---|---|---|---|
| Logistic Regression (tuned) | 0.739 | 0.505 | 0.781 | 0.613 | 0.841 |
| Random Forest (tuned) | 0.767 | 0.545 | 0.738 | 0.627 | 0.839 |
| **XGBoost (tuned) ★** | **0.751** | **0.520** | **0.789** | **0.627** | **0.842** |

**Why XGBoost wins.** It catches **79% of churners** (recall) while keeping 52% precision. That means when the model flags a customer as high-risk, there's a 52% chance they'll actually churn — a 2× improvement over the 26.5% baseline rate. The **ROC-AUC of 0.842** confirms strong rank-ordering from low-risk to high-risk customers.

---

## Key Drivers

What the model learned from SHAP analysis:

| Factor | Impact |
|---|---|
| **Contract type** 🏆 | Month-to-month churn at 42.7% vs 2.8% for two-year |
| **Tenure** | Most churn happens in the first 10 months |
| **Internet service** | Fiber optic customers churn ~2× more than DSL |
| **Payment method** | Electronic check users are highest-risk |
| **Monthly charges** | Every $10 increase correlates with higher churn |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Explore the full pipeline in a notebook
jupyter notebook Churn_Prediction.ipynb

# 3. Train and export deployment artifacts
python save_artifacts.py

# 4. Launch the Streamlit app
streamlit run app.py
```

Then open **http://localhost:8501** — enter customer details in the sidebar and click **Predict Churn** for a live risk assessment.

---

## Project Structure

```
churn-prediction/
├── Churn_Prediction.ipynb   # Full ML pipeline (33 cells)
├── app.py                    # Streamlit web application
├── save_artifacts.py         # Train and export model artifacts
├── requirements.txt
├── .gitignore
├── data/                     # Raw and processed CSVs
├── models/                   # Serialized model, scaler, preprocessor
├── assets/                   # Evaluation plots and figures
└── README.md
```

---

## Deployment

Deploy to [Streamlit Community Cloud](https://share.streamlit.io) in one click:

1. Push this repo to GitHub (already done ✅)
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app** → select `churn-prediction` → branch `master` → file `app.py`
4. Click **Deploy**

Your app will be live at `https://<your-app>.streamlit.app` within minutes. Model artifacts are included in the repo — no extra setup needed.

---

## License

This project uses the [IBM Telco Customer Churn Dataset](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) available under the CC0 public domain license.
