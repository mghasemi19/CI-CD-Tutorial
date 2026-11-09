import pytest
from fastapi.testclient import TestClient

@pytest.fixture(scope="module")
def client(tmp_path_factory):
    import os
    tmp_path = tmp_path_factory.mktemp("api")
    model_dir = tmp_path / "models"
    from ml.train import train
    train(model_dir)
    os.environ["MODEL_DIR"] = str(model_dir)
    os.environ["DATABASE_URL"] = "sqlite:///" + str(tmp_path / "tests.db")
    # Import only after setting environment variables, since engine is constructed on import.
    from app.main import app
    with TestClient(app) as test_client:
        yield test_client

def test_health_and_predict(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = {"tenure_months": 12, "monthly_spend": 80, "support_tickets": 3,
               "contract_type": "monthly", "auto_pay": "no"}
    r = client.post("/predict", json=payload)
    assert r.status_code == 200, r.text
    assert 0 <= r.json()["churn_probability"] <= 1
    assert r.json()["prediction_id"] >= 1
    history = client.get("/predictions").json()
    assert len(history) >= 1

def test_validation(client):
    r = client.post("/predict", json={"tenure_months": -1})
    assert r.status_code == 422
    assert client.get("/predictions?limit=1000").status_code == 422
