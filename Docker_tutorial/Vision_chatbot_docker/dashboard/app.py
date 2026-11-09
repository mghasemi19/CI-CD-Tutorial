import os
import requests
import streamlit as st
import pandas as pd

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
st.set_page_config(page_title="Churn Prediction Dashboard", page_icon="📈", layout="wide")
st.title("Customer Churn ML Dashboard")
st.caption("Education-only demo trained on SYNTHETIC data. Scores are not validated business predictions.")

try:
    info = requests.get(f"{API_URL}/model/info", timeout=5)
    info.raise_for_status()
    metrics = info.json()["metrics"]
    c1,c2,c3 = st.columns(3)
    c1.metric("Test accuracy", f"{metrics['accuracy']:.1%}")
    c2.metric("Test ROC-AUC", f"{metrics['roc_auc']:.3f}")
    c3.metric("Test samples", metrics["test_examples"])
except requests.RequestException:
    st.warning("API unavailable. Is Docker Compose running?")

with st.form("customer"):
    tenure_months = st.slider("Tenure (months)", 0, 120, 12)
    monthly_spend = st.number_input("Monthly spend ($)", min_value=0.0, max_value=10000.0, value=65.0)
    support_tickets = st.number_input("Support tickets", min_value=0, max_value=100, value=2)
    contract_type = st.selectbox("Contract", ["monthly", "annual"])
    auto_pay = st.selectbox("Auto-pay", ["yes", "no"])
    submitted = st.form_submit_button("Predict churn")
if submitted:
    payload = {"tenure_months": tenure_months, "monthly_spend": monthly_spend,
               "support_tickets": support_tickets, "contract_type": contract_type,
               "auto_pay": auto_pay}
    try:
        response = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        st.metric("Predicted churn probability", f"{result['churn_probability']:.1%}")
        st.info(f"Prediction #{result['prediction_id']} stored in database")
    except requests.RequestException as exc:
        st.error(f"Prediction failed: {exc}")

st.subheader("Recent predictions")
try:
    r = requests.get(f"{API_URL}/predictions", params={"limit": 30}, timeout=5)
    r.raise_for_status()
    data = r.json()
    if data:
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No predictions recorded yet.")
except requests.RequestException:
    st.info("Prediction history will appear when the API is available.")
