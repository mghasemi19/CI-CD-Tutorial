import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, DateTime, Float, Integer, Boolean, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./predictions.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class PredictionRecord(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    tenure_months: Mapped[int] = mapped_column(Integer)
    monthly_spend: Mapped[float] = mapped_column(Float)
    support_tickets: Mapped[int] = mapped_column(Integer)
    contract_type: Mapped[str] = mapped_column(String(20))
    auto_pay: Mapped[str] = mapped_column(String(10))
    churn_probability: Mapped[float] = mapped_column(Float)
    predicted_churn: Mapped[bool] = mapped_column(Boolean)


def get_db():
    with SessionLocal() as db:
        yield db
