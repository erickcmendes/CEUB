.PHONY: install train-classifiers train-regressors train-xgboost train-lstm train-all test clean help

# Comandos disponíveis ─────────────────────────────────────────────────────────
help:
	@echo "Comandos disponíveis:"
	@echo "  make install           Instala todas as dependências"
	@echo "  make train-classifiers Treina KNN, DT, RF, LogReg"
	@echo "  make train-regressors  Treina Regressão Linear"
	@echo "  make train-xgboost     Treina XGBoost com GridSearchCV"
	@echo "  make train-lstm        Treina uma LSTM por ticker (BTC, ETH, XRP, DASH)"
	@echo "  make train-all         Executa todos os pipelines acima em sequência"
	@echo "  make test              Roda smoke tests"
	@echo "  make clean             Limpa outputs/"

# Instalação ───────────────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt

# Pipelines individuais ────────────────────────────────────────────────────────
train-classifiers:
	python -m pipelines.train_classifiers

train-regressors:
	python -m pipelines.train_regressors

train-xgboost:
	python -m pipelines.train_xgboost

train-lstm:
	python -m pipelines.train_lstm

# Executar tudo ────────────────────────────────────────────────────────────────
train-all: train-classifiers train-regressors train-xgboost train-lstm
	@echo "✅ Todos os modelos foram treinados."

# Tests ────────────────────────────────────────────────────────────────────────
test:
	pytest tests/ -v

# Limpeza ──────────────────────────────────────────────────────────────────────
clean:
	rm -rf outputs/models/*.joblib outputs/models/*.keras outputs/models/*.yaml
	rm -rf outputs/figures/*.png
	rm -rf outputs/reports/*.csv
	rm -rf outputs/logs/*.log
	@echo "🧹 Outputs limpos."
