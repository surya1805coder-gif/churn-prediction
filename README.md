<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/XGBoost-tuned-00A651" alt="XGBoost">
  <img src="https://img.shields.io/badge/ROC%E2%80%93AUC-0.842-success" alt="AUC">
  <img src="https://img.shields.io/badge/F1-0.627-0077B6" alt="F1">
  <img src="https://img.shields.io/badge/Streamlit-%E2%86%92%20live-FF4B4B?logo=streamlit" alt="Live App">
  <img src="https://img.shields.io/badge/license-CC0-lightgrey" alt="License">
</p>

<h1 align="center">Customer Churn Prediction</h1>
<p align="center">
  <a href="https://churn-prediction-dtb6znoxdw9diydx4gwbfu.streamlit.app/"><strong>Live Demo &rarr;</strong></a>
  &nbsp;|&nbsp;
  Predict which telecom customers are about to leave &mdash; before they do.
</p>

---

## Overview

Telecom providers lose 26.5% of customers annually. This project builds a gradient-boosted classifier (XGBoost) that flags high-risk subscribers with **79% recall** and **0.842 ROC-AUC**, then serves predictions through an interactive Streamlit interface.

The model was trained on the IBM Telco Customer Churn dataset (7,043 records, 19 features) and is deployable with zero configuration beyond `pip install`.

---

## Results

| Model | Accuracy | Precision | Recall | F1 | AUC |
|---|---|---|---|---|---|
| Logistic Regression (tuned) | 0.739 | 0.505 | 0.781 | 0.613 | 0.841 |
| Random Forest (tuned) | 0.767 | 0.545 | 0.738 | 0.627 | 0.839 |
| **XGBoost (tuned)** | **0.751** | **0.520** | **0.789** | **0.627** | **0.842** |

XGBoost was selected as the production model. At a 52% precision threshold, two of every three flagged customers are true churners &mdash; a 2&times; lift over the base rate.

---

## Top Churn Drivers

| Factor | Detail |
|---|---|
| **Contract type** | Month-to-month churns at 42.7% vs 2.8% for two-year |
| **Tenure** | 80% of churn occurs within the first 10 months |
| **Internet service** | Fiber optic customers churn at roughly twice the rate of DSL |
| **Payment method** | Electronic check users are the highest-risk segment |
| **Monthly charges** | Every $10 increase raises churn probability measurably |

These drivers were identified via SHAP TreeExplainer analysis on the trained model.

---

## Tech Stack

| Component | Tools |
|---|---|
| Language | Python 3.13 |
| Data | pandas, numpy |
| Modeling | XGBoost, scikit-learn |
| Tuning | GridSearchCV (5-fold, F1-optimized) |
| Interpretation | SHAP |
| Frontend | Streamlit |
| Serialization | joblib |

---

## Local Development

```bash
pip install -r requirements.txt
python save_artifacts.py
streamlit run app.py
```

The full pipeline is also available as a Jupyter notebook (`Churn_Prediction.ipynb`) for step-by-step exploration.

---

## Project Structure

```
├── app.py                  # Streamlit application
├── save_artifacts.py       # Model training and artifact export
├── Churn_Prediction.ipynb  # Full ML pipeline
├── requirements.txt
├── data/                   # Raw and processed datasets
├── models/                 # Serialized model and preprocessor
└── assets/                 # Evaluation plots
```

---

## License

This project uses the [IBM Telco Customer Churn Dataset](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) available under CC0.
