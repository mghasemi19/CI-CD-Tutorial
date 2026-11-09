"""Serving API. Use a trusted, versioned model artifact; never load untrusted joblib files."""
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
import joblib
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import Base, PredictionRecord, engine, get_db
from app.schemas import CustomerInput, PredictionOutput

MODEL_DIR = Path(os.getenv("MODEL_DIR", "artifacts"))
MODEL_VERSION = os.getenv("MODEL_VERSION", "synthetic-v1")

@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = MODEL_DIR / "model.joblib"
    if not model_path.exists():
        raise RuntimeError(f"Missing model: {model_path}. Run python -m ml.train")
    app.state.model = joblib.load(model_path)
    app.state.metrics = json.loads((MODEL_DIR / "metrics.json").read_text())
    Base.metadata.create_all(bind=engine)  # Tutorial convenience; use Alembic migrations in production.
    yield

app = FastAPI(title="Churn ML API", version="1.0.0", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": hasattr(app.state, "model")}

@app.get("/model/info")
def model_info():
    if not hasattr(app.state, "metrics"):
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"version": MODEL_VERSION, "metrics": app.state.metrics}

@app.post("/predict", response_model=PredictionOutput)
def predict(customer: CustomerInput, db: Session = Depends(get_db)):
    if not hasattr(app.state, "model"):
        raise HTTPException(status_code=503, detail="Model not loaded")
    data = pd.DataFrame([customer.model_dump()])
    probability = float(app.state.model.predict_proba(data)[0][1])
    record = PredictionRecord(**customer.model_dump(), churn_probability=probability,
                              predicted_churn=probability >= 0.5)
    db.add(record)
    db.commit()
    db.refresh(record)
    return PredictionOutput(prediction_id=record.id, churn_probability=round(probability, 4),
                            predicted_churn=record.predicted_churn, model_version=MODEL_VERSION)

@app.get("/predictions")
def get_predictions(limit: int = 20, db: Session = Depends(get_db)):
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    rows = db.scalars(select(PredictionRecord).order_by(PredictionRecord.id.desc()).limit(limit)).all()
    return [{"id": r.id, "created_at": r.created_at.isoformat(),
             "tenure_months": r.tenure_months, "monthly_spend": r.monthly_spend,
             "support_tickets": r.support_tickets, "contract_type": r.contract_type,
             "auto_pay": r.auto_pay, "churn_probability": r.churn_probability,
             "predicted_churn": r.predicted_churn} for r in rows]
