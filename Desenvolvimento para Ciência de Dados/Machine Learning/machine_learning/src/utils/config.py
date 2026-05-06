"""
Configurações globais do projeto.

Centraliza paths, seeds e parâmetros padrão usados em todo o pipeline.
"""
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT_DIR     = Path(__file__).resolve().parents[2]
ML_DIR       = ROOT_DIR / "machine_learning"
DATA_DIR     = ROOT_DIR / "data"
CONFIG_DIR   = ML_DIR / "configs"
OUTPUTS_DIR  = ML_DIR / "outputs"

MODELS_DIR   = OUTPUTS_DIR / "models"
FIGURES_DIR  = OUTPUTS_DIR / "figures"
REPORTS_DIR  = OUTPUTS_DIR / "reports"
LOGS_DIR     = OUTPUTS_DIR / "logs"

# ── Datasets ─────────────────────────────────────────────────────────────────
CARTEIRAS_ML_CSV   = DATA_DIR / "carteiras_ml.csv"
HISTORICO_CSV      = DATA_DIR / "historico_moedas.csv"
COIN_CSVS = {
    "BTC":  DATA_DIR / "BTC.csv",
    "ETH":  DATA_DIR / "ETH.csv",
    "XRP":  DATA_DIR / "XRP.csv",
    "DASH": DATA_DIR / "DASH.csv",
}

# ── Reprodutibilidade ────────────────────────────────────────────────────────
RANDOM_SEED = 42

# ── Splits ───────────────────────────────────────────────────────────────────
TEST_SIZE     = 0.20
VAL_SIZE      = 0.10  # usado dentro do treino quando há validação separada

# ── LSTM ─────────────────────────────────────────────────────────────────────
LOOK_BACK_WINDOW = 90       # janela de entrada (em dias)
LSTM_BATCH_SIZE  = 32
LSTM_MAX_EPOCHS  = 200
LSTM_UNITS       = 100
LSTM_PATIENCE    = 15       # paciência do EarlyStopping
