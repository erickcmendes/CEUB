"""
Smoke tests para os wrappers de modelos.
Verificam apenas que os modelos podem ser instanciados, treinados e usados em predição.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.timeseries_features import create_sequences
from src.models.classifiers import get_classifier
from src.models.regressors import LinearRegressor


def test_classifier_factory():
    for name in ["knn", "decision_tree", "random_forest", "logistic_regression"]:
        clf = get_classifier(name)
        assert clf is not None


def test_classifier_fit_predict():
    np.random.seed(0)
    X = np.random.randn(100, 4)
    y = (X.sum(axis=1) > 0).astype(int)

    clf = get_classifier("random_forest", n_estimators=10)
    clf.fit(X, y)
    pred = clf.predict(X)
    assert pred.shape == (100,)
    assert set(np.unique(pred)).issubset({0, 1})


def test_linear_regressor_fit_predict():
    np.random.seed(0)
    X = np.random.randn(50, 3)
    y = X @ np.array([1.0, 2.0, 3.0]) + 0.1

    reg = LinearRegressor()
    reg.fit(X, y)
    pred = reg.predict(X)
    assert pred.shape == (50,)
    # Coeficientes devem aproximar [1, 2, 3]
    assert np.allclose(reg.coefficients, [1, 2, 3], atol=0.5)


def test_create_sequences():
    series = np.arange(100, dtype=float)
    X, y = create_sequences(series, look_back=10)
    assert X.shape == (90, 10, 1)
    assert y.shape == (90,)
    # Cada y[i] deve ser series[10+i]
    assert y[0] == 10
    assert y[-1] == 99
