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
from datetime import datetime

# ── Page Config ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Churn Predictor",
    page_icon="\U0001f4ca",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State ───────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []


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
    df.drop(columns=["customerID"], errors="ignore", inplace=True)

    if pd.isna(df["TotalCharges"].iloc[0]) or df["TotalCharges"].iloc[0] == 0:
        df["TotalCharges"] = df["tenure"] * df["MonthlyCharges"]
    df["TotalCharges"] = df["TotalCharges"].fillna(totalcharges_median)
    df["SeniorCitizen"] = df["SeniorCitizen"].astype(object)

    df_encoded = pd.get_dummies(df, drop_first=True)
    for col in feature_columns:
        if col not in df_encoded.columns:
            df_encoded[col] = 0
    df_encoded = df_encoded.reindex(columns=feature_columns, fill_value=0)

    X_scaled = scaler.transform(df_encoded.astype(float))
    return X_scaled


# ── Risk Breakdown ──────────────────────────────────────────────────────
def get_active_risk_factors(inputs: dict) -> list:
    factors = []
    if inputs["Contract"] == "Month-to-month":
        factors.append(("Contract Type", "Month-to-month (42.7% churn rate)"))
    if inputs["tenure"] < 10:
        factors.append(("Tenure", f"{inputs['tenure']} months (< 10, highest risk period)"))
    if inputs["InternetService"] == "Fiber optic":
        factors.append(("Internet Service", "Fiber optic (2x churn vs DSL)"))
    if inputs["PaymentMethod"] == "Electronic check":
        factors.append(("Payment Method", "Electronic check (highest-risk payment)"))
    if inputs["MonthlyCharges"] >= 80:
        factors.append(("Monthly Charges", f"${inputs['MonthlyCharges']:.0f}/mo (high)"))
    if inputs["SeniorCitizen"] == 1:
        factors.append(("Senior Citizen", "Senior citizens churn at higher rates"))
    if inputs["Partner"] == "No":
        factors.append(("Partner", "No partner (less household stability)"))
    if inputs["Dependents"] == "No":
        factors.append(("Dependents", "No dependents (less household stability)"))
    if inputs["PaperlessBilling"] == "Yes":
        factors.append(("Paperless Billing", "Paperless billing users churn more"))
    return factors


# ── UI: Header ──────────────────────────────────────────────────────────
st.title("\U0001f4ca Customer Churn Predictor")
st.markdown(
    "Enter customer details in the sidebar and click **Predict Churn** "
    "to assess their cancellation risk."
)

# ── UI: Sidebar Inputs ──────────────────────────────────────────────────
st.sidebar.header("Customer Information")
st.sidebar.markdown("---")

st.sidebar.subheader("Demographics")
gender = st.sidebar.selectbox("Gender", ["Male", "Female"])
senior_citizen = st.sidebar.selectbox("Senior Citizen", ["No", "Yes"])
partner = st.sidebar.selectbox("Has Partner", ["No", "Yes"])
dependents = st.sidebar.selectbox("Has Dependents", ["No", "Yes"])

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
    min_value=0.0, max_value=10000.0, value=0.0, step=10.0,
)

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

            # ── Save to session history ─────────────────────────────
            entry = {
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Tenure": tenure,
                "Contract": contract,
                "Internet": internet_service,
                "Monthly": f"${monthly_charges:.0f}",
                "Payment": payment_method,
                "Probability": f"{proba:.1%}",
                "Prediction": "Churn \u26a0\ufe0f" if prediction else "Stay \u2705",
            }
            st.session_state.history.append(entry)

            # ── Result columns ──────────────────────────────────────
            col1, col2 = st.columns([1, 2])

            with col1:
                if prediction == 1:
                    st.error("### \u26a0\ufe0f High Risk of Churn")
                else:
                    st.success("### \u2705 Low Risk of Churn")

                st.metric("Churn Probability", f"{proba:.1%}")
                st.metric("Confidence", f"{max(proba, 1 - proba):.1%}")

                # Risk gauge
                pct = int(round(proba * 100))
                color = "red" if pct >= 50 else "orange" if pct >= 30 else "green"
                st.markdown(
                    f'<div style="height:20px;width:100%;background:#eee;border-radius:10px;">'
                    f'<div style="height:20px;width:{pct}%;background:{color};border-radius:10px;'
                    f'text-align:center;color:white;font-size:12px;line-height:20px;">'
                    f"{pct}%</div></div>",
                    unsafe_allow_html=True,
                )

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

            # ── Per-prediction risk factor breakdown ────────────────
            st.markdown("---")
            st.markdown("#### \U0001f50d Risk Factors for This Customer")

            active = get_active_risk_factors(raw_input)
            if active:
                for label, detail in active:
                    st.markdown(f"- **{label}:** {detail}")
            else:
                st.markdown("*None of the top risk factors apply to this profile.*")

            st.caption(
                "Based on SHAP analysis from the trained model. "
                "Features shown are the strongest global predictors of churn."
            )

        except Exception as e:
            st.error(f"Prediction failed: {e}")
            st.info(
                "Try re-running `save_artifacts.py` to ensure model files "
                "are up to date."
            )

# ── Prediction History ──────────────────────────────────────────────────
if st.session_state.history:
    st.markdown("---")
    st.markdown("### \U0001f4cb Session History")

    hist_df = pd.DataFrame(st.session_state.history)
    st.dataframe(hist_df, use_container_width=True, hide_index=True)

    csv = hist_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="\U0001f4e5 Download as CSV",
        data=csv,
        file_name=f"churn_predictions_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

# ── Footer ──────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Model:** XGBoost (tuned)  \n"
    "**F1 Score:** 0.627  \n"
    "**ROC-AUC:** 0.842  \n"
    "**Dataset:** IBM Telco Churn"
)
