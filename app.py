"""
app.py — Customer Churn Prediction (Streamlit)
================================================
Loads saved model artifacts and serves a live prediction UI.
Run with:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os

# ── Page Config ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Churn Predictor",
    page_icon="\U0001f4ca",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load Artifacts ──────────────────────────────────────────────────────
@st.cache_resource
def load_artifacts():
    model_path = "models/model.pkl"
    scaler_path = "models/scaler.pkl"
    preprocessor_path = "models/preprocessor.pkl"

    missing = [p for p in [model_path, scaler_path, preprocessor_path] if not os.path.exists(p)]
    if missing:
        st.error(
            f"Missing file(s): {', '.join(missing)}. "
            "Run `python save_artifacts.py` first to generate them."
        )
        st.stop()

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    preprocessor = joblib.load(preprocessor_path)
    return model, scaler, preprocessor


model, scaler, preprocessor = load_artifacts()
feature_columns = preprocessor["feature_columns"]
totalcharges_median = preprocessor["totalcharges_median"]


# ── Preprocessing Function ───────────────────────────────────────────────
def preprocess_input(raw_input: dict) -> pd.DataFrame:
    df = pd.DataFrame([raw_input])

    # Drop customerID if present
    df.drop(columns=["customerID"], errors="ignore", inplace=True)

    # TotalCharges: estimate from tenure * MonthlyCharges if empty/zero
    if pd.isna(df["TotalCharges"].iloc[0]) or df["TotalCharges"].iloc[0] == 0:
        df["TotalCharges"] = df["tenure"] * df["MonthlyCharges"]
    df["TotalCharges"] = df["TotalCharges"].fillna(totalcharges_median)

    # SeniorCitizen: 0/1 -> object so get_dummies encodes it
    df["SeniorCitizen"] = df["SeniorCitizen"].astype(object)

    # One-hot encode, then align columns to match training set
    df_encoded = pd.get_dummies(df, drop_first=True)
    for col in feature_columns:
        if col not in df_encoded.columns:
            df_encoded[col] = 0
    df_encoded = df_encoded.reindex(columns=feature_columns, fill_value=0)

    X_scaled = scaler.transform(df_encoded.astype(float))
    return X_scaled


# ── UI: Header ──────────────────────────────────────────────────────────
st.title("\U0001f4ca Customer Churn Predictor")
st.markdown(
    "Enter customer details in the sidebar and click **Predict Churn** "
    "to assess their cancellation risk."
)

# ── UI: Sidebar Inputs ──────────────────────────────────────────────────
st.sidebar.header("Customer Information")
st.sidebar.markdown("---")

# Demographics
st.sidebar.subheader("Demographics")
gender = st.sidebar.selectbox("Gender", ["Male", "Female"])
senior_citizen = st.sidebar.selectbox("Senior Citizen", ["No", "Yes"])
partner = st.sidebar.selectbox("Has Partner", ["No", "Yes"])
dependents = st.sidebar.selectbox("Has Dependents", ["No", "Yes"])

# Account & Tenure
st.sidebar.subheader("Account & Tenure")
tenure = st.sidebar.slider("Tenure (months)", 0, 72, 12)
contract = st.sidebar.selectbox("Contract", ["Month-to-month", "One year", "Two year"])
paperless_billing = st.sidebar.selectbox("Paperless Billing", ["No", "Yes"])
payment_method = st.sidebar.selectbox(
    "Payment Method",
    ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"],
)
monthly_charges = st.sidebar.slider("Monthly Charges ($)", 18.0, 120.0, 70.0, step=1.0)
total_charges_input = st.sidebar.number_input(
    "Total Charges ($) \u2014 leave 0 to auto-calculate",
    min_value=0.0,
    max_value=10000.0,
    value=0.0,
    step=10.0,
)

# Services
st.sidebar.subheader("Services")
phone_service = st.sidebar.selectbox("Phone Service", ["No", "Yes"])
multiple_lines = st.sidebar.selectbox("Multiple Lines", ["No", "Yes", "No phone service"])
internet_service = st.sidebar.selectbox("Internet Service", ["DSL", "Fiber optic", "No"])

internet_on = internet_service != "No"
online_security = st.sidebar.selectbox(
    "Online Security",
    ["No", "Yes", "No internet service"] if internet_on else ["No internet service"],
)
online_backup = st.sidebar.selectbox(
    "Online Backup",
    ["No", "Yes", "No internet service"] if internet_on else ["No internet service"],
)
device_protection = st.sidebar.selectbox(
    "Device Protection",
    ["No", "Yes", "No internet service"] if internet_on else ["No internet service"],
)
tech_support = st.sidebar.selectbox(
    "Tech Support",
    ["No", "Yes", "No internet service"] if internet_on else ["No internet service"],
)
streaming_tv = st.sidebar.selectbox(
    "Streaming TV",
    ["No", "Yes", "No internet service"] if internet_on else ["No internet service"],
)
streaming_movies = st.sidebar.selectbox(
    "Streaming Movies",
    ["No", "Yes", "No internet service"] if internet_on else ["No internet service"],
)

# ── Prediction ──────────────────────────────────────────────────────────
predict_btn = st.sidebar.button(
    "\U0001f50d Predict Churn", type="primary", use_container_width=True
)

if predict_btn:
    raw_input = {
        "gender": gender,
        "SeniorCitizen": 1 if senior_citizen == "Yes" else 0,
        "Partner": partner,
        "Dependents": dependents,
        "tenure": tenure,
        "PhoneService": phone_service,
        "MultipleLines": multiple_lines,
        "InternetService": internet_service,
        "OnlineSecurity": online_security,
        "OnlineBackup": online_backup,
        "DeviceProtection": device_protection,
        "TechSupport": tech_support,
        "StreamingTV": streaming_tv,
        "StreamingMovies": streaming_movies,
        "Contract": contract,
        "PaperlessBilling": paperless_billing,
        "PaymentMethod": payment_method,
        "MonthlyCharges": monthly_charges,
        "TotalCharges": total_charges_input,
    }

    with st.spinner("Computing prediction..."):
        try:
            X_input = preprocess_input(raw_input)
            proba = model.predict_proba(X_input)[0, 1]
            prediction = int(proba >= 0.5)

            col1, col2 = st.columns([1, 2])

            with col1:
                if prediction == 1:
                    st.error("### \u26a0\ufe0f High Risk of Churn")
                else:
                    st.success("### \u2705 Low Risk of Churn")

                st.metric("Churn Probability", f"{proba:.1%}")
                st.metric("Confidence", f"{max(proba, 1 - proba):.1%}")

            with col2:
                st.markdown("#### Customer Profile")
                st.json(
                    {
                        "Contract": contract,
                        "Tenure": f"{tenure} months",
                        "Monthly Charges": f"${monthly_charges:.2f}",
                        "Internet Service": internet_service,
                        "Payment Method": payment_method,
                        "Has Partner": partner,
                        "Has Dependents": dependents,
                    }
                )

            st.markdown("---")
            st.markdown("#### \U0001f511 Key Factors in This Prediction")
            st.markdown(
                """
Based on global SHAP analysis from the trained model, the top features
that most strongly influence churn risk are:

1. **Contract Type** \u2014 Month-to-month contracts have significantly higher
   churn risk (42.7%) vs two-year contracts (2.8%).
2. **Tenure** \u2014 Customers with less than 10 months of tenure are at
   the highest risk of churning.
3. **Internet Service** \u2014 Fiber optic customers churn at higher rates
   compared to DSL customers, likely due to service quality or pricing.

> *For a personalized explanation with feature-level SHAP values,
> consider deploying a SHAP explainer endpoint alongside the model.*
"""
            )

        except Exception as e:
            st.error(f"Prediction failed: {e}")
            st.info(
                "Try re-running `save_artifacts.py` to ensure model files "
                "are up to date."
            )

# ── Footer ──────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Model:** XGBoost (tuned)  \n"
    "**F1 Score:** 0.627  \n"
    "**ROC-AUC:** 0.842  \n"
    "**Dataset:** IBM Telco Churn"
)
