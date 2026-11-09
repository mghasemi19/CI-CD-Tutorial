from typing import Literal
from pydantic import BaseModel, Field

class CustomerInput(BaseModel):
    tenure_months: int = Field(ge=0, le=120)
    monthly_spend: float = Field(ge=0, le=10000)
    support_tickets: int = Field(ge=0, le=100)
    contract_type: Literal["monthly", "annual"]
    auto_pay: Literal["yes", "no"]

class PredictionOutput(BaseModel):
    prediction_id: int
    churn_probability: float
    predicted_churn: bool
    model_version: str
