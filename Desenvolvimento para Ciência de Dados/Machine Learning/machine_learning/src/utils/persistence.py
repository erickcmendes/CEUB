"""
Persistência de modelos treinados.

Suporta:
- joblib: para modelos sklearn e XGBoost
- keras: para modelos LSTM (formato .keras)
- yaml: para metadados (métricas, hiperparâmetros)
"""
from pathlib import Path
from typing import Any

import joblib
import yaml

from src.utils.config import MODELS_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def save_sklearn_model(model: Any, name: str) -> Path:
    """Salva um modelo sklearn/XGBoost via joblib."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / f"{name}.joblib"
    joblib.dump(model, path)
    logger.info(f"Modelo salvo: {path}")
    return path


def load_sklearn_model(name: str) -> Any:
    """Carrega um modelo sklearn/XGBoost via joblib."""
    path = MODELS_DIR / f"{name}.joblib"
    if not path.exists():
        raise FileNotFoundError(f"Modelo não encontrado: {path}")
    return joblib.load(path)


def save_keras_model(model: Any, name: str) -> Path:
    """Salva um modelo Keras (LSTM) no formato .keras."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / f"{name}.keras"
    model.save(path)
    logger.info(f"Modelo Keras salvo: {path}")
    return path


def load_keras_model(name: str) -> Any:
    """Carrega um modelo Keras."""
    from tensorflow.keras.models import load_model
    path = MODELS_DIR / f"{name}.keras"
    if not path.exists():
        raise FileNotFoundError(f"Modelo não encontrado: {path}")
    return load_model(path)


def save_metadata(metadata: dict, name: str) -> Path:
    """Salva metadados (métricas, hiperparâmetros) em YAML."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / f"{name}_meta.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(metadata, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    logger.info(f"Metadados salvos: {path}")
    return path


def load_metadata(name: str) -> dict:
    """Carrega metadados do YAML."""
    path = MODELS_DIR / f"{name}_meta.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Metadados não encontrados: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
