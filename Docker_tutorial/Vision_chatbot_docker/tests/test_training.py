import numpy as np
from ml.train import make_dataset, train

def test_dataset_is_reproducible():
    assert make_dataset(20).equals(make_dataset(20))

def test_training_artifacts(tmp_path):
    m = train(tmp_path)
    assert 0 <= m["roc_auc"] <= 1
    assert (tmp_path / "model.joblib").exists()
    assert (tmp_path / "metrics.json").exists()
