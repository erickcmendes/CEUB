# 🤖 Machine Learning · CryptoPortfolio Analytics

Diretório dedicado à fase de Machine Learning do projeto. Implementa um pipeline modular completo para treinar, avaliar e servir modelos clássicos e uma rede neural recorrente (LSTM) sobre os dados de criptomoedas extraídos nas etapas anteriores.

---

## 📁 Estrutura

```
machine_learning/
│
├── notebooks/                          ← Notebooks de desenvolvimento
│   ├── 01_classification_models.ipynb  KNN, DT, RF, LogReg + XGBoost (clf)
│   ├── 02_regression_models.ipynb      Linear Regression + XGBoost (reg)
│   └── 03_lstm_timeseries.ipynb        LSTM single-layer por ticker
│
├── src/                                ← Pacote Python (pipeline modular)
│   ├── analysis/
│   │   └── feature_importance.py
│   ├── data/
│   │   ├── loader.py                   Carregamento dos CSVs
│   │   ├── preprocessor.py             Limpeza
│   │   └── splitter.py                 Splits tabular e temporal
│   ├── evaluation/
│   │   ├── classification_metrics.py
│   │   ├── regression_metrics.py
│   │   └── model_comparator.py
│   ├── features/
│   │   ├── portfolio_features.py       Features das carteiras
│   │   └── timeseries_features.py      Sliding windows + scaler
│   ├── inference/
│   │   └── predictor.py                API de inferência
│   ├── models/
│   │   ├── base.py                     ABC: BaseModel
│   │   ├── classifiers.py              KNN, DT, RF, LogReg
│   │   ├── regressors.py               Linear Regression
│   │   ├── xgboost_model.py            XGBoost com GridSearchCV
│   │   └── lstm_model.py               LSTM (não-stacked)
│   ├── utils/
│   │   ├── config.py                   Paths e constantes globais
│   │   ├── logger.py                   Logger padronizado
│   │   └── persistence.py              Save/load (joblib + keras)
│   └── visualization/
│       ├── classification_plots.py
│       ├── regression_plots.py
│       └── lstm_plots.py
│
├── configs/                            ← Hiperparâmetros em YAML
│   ├── classifiers_config.yaml
│   ├── regressors_config.yaml
│   ├── xgboost_config.yaml
│   └── lstm_config.yaml
│
├── pipelines/                          ← Scripts de execução automatizada
│   ├── train_classifiers.py
│   ├── train_regressors.py
│   ├── train_xgboost.py
│   └── train_lstm.py
│
├── outputs/                            ← Artefatos gerados
│   ├── models/                         .joblib, .keras, .yaml (metadados)
│   ├── figures/                        .png
│   ├── reports/                        .csv comparativos
│   └── logs/                           .log de cada pipeline
│
├── tests/                              ← Smoke tests (pytest)
│   ├── test_data.py
│   └── test_models.py
│
├── Makefile                            ← Atalhos de execução
├── requirements.txt
└── README.md                           ← Este arquivo
```

---

## 🎯 Modelos Implementados

### Classificação — *"esta carteira é boa ou ruim?"*

Target: `sharpe_label` (binário; 1 = Sharpe ≥ mediana)

| Modelo | Tipo | Hiperparâmetros |
|--------|------|-----------------|
| **KNN** | Baseline | n_neighbors=5, weights='uniform' |
| **Árvore de Decisão** | Baseline | max_depth=6, criterion='gini' |
| **Random Forest** | Baseline | n_estimators=200, max_depth=10 |
| **Regressão Logística** | Baseline | C=1.0, max_iter=1000 |
| **XGBoost** | Fine-tuned | GridSearchCV em 5 dimensões (108 combinações) |

### Regressão — *"qual o retorno esperado desta carteira?"*

Target: `Retornos` (contínuo)

| Modelo | Tipo |
|--------|------|
| **Regressão Linear** | Baseline |
| **XGBoost Regressor** | Fine-tuned (GridSearchCV) |

### Séries temporais — *"qual o preço amanhã?"*

Target: preço de fechamento `Close` em USD

**Arquitetura LSTM single-layer (não-stacked):**

```
Input (90, 1)  →  LSTM(units=100)  →  Dropout(0.2)  →  Dense(1, linear)
```

| Hiperparâmetro | Valor |
|----------------|-------|
| `look_back_window` | 90 dias |
| `units` | 100 |
| `batch_size` | 32 |
| `epochs` (máx) | 200 |
| EarlyStopping `patience` | 15 |
| Loss | MSE |
| Otimizador | Adam (lr=0.001) |
| Métricas reportadas | RMSE e MAE em USD |

Um modelo é treinado para cada ticker (BTC, ETH, XRP, DASH).

---

## 🚀 Execução

### Instalação

```bash
make install
# ou
pip install -r requirements.txt
```

### Pré-requisitos

Os notebooks anteriores já devem ter gerado os CSVs em `data/`:

| Arquivo | Gerado por |
|---------|-----------|
| `data/carteiras_ml.csv` | `eda_insights.ipynb` |
| `data/historico_moedas.csv` | `eda_inicial.ipynb` |
| `data/{BTC,ETH,XRP,DASH}.csv` | `ETL_moedas.ipynb` |

### Treinar via pipelines (linha de comando)

```bash
# Pipelines individuais
make train-classifiers   # KNN, DT, RF, LogReg
make train-regressors    # Linear Regression
make train-xgboost       # XGBoost (clf + reg) com GridSearchCV
make train-lstm          # 4 LSTMs (uma por ticker)

# Tudo de uma vez
make train-all
```

Cada pipeline:
- Carrega config do YAML em `configs/`
- Treina os modelos
- Avalia no conjunto de teste
- Salva o modelo em `outputs/models/`
- Salva métricas e hiperparâmetros em `outputs/models/<nome>_meta.yaml`
- Salva log de execução em `outputs/logs/`
- Gera relatório CSV comparativo em `outputs/reports/`

### Treinar via notebooks (interativo)

Abra o Jupyter na pasta `notebooks/`:

```bash
cd notebooks/
jupyter notebook
```

Execute na ordem:
1. `01_classification_models.ipynb`
2. `02_regression_models.ipynb`
3. `03_lstm_timeseries.ipynb`

Os notebooks são autocontidos: importam o pacote `src/` e executam todo o pipeline com visualizações intercaladas.

### Testes

```bash
make test
```

---

## 📊 Outputs

Após o treinamento completo, `outputs/` conterá:

```
outputs/
├── models/
│   ├── knn_classifier.joblib                + _meta.yaml
│   ├── decision_tree_classifier.joblib      + _meta.yaml
│   ├── random_forest_classifier.joblib      + _meta.yaml
│   ├── logistic_regression.joblib           + _meta.yaml
│   ├── linear_regression.joblib             + _meta.yaml
│   ├── xgboost_clf.joblib                   + _meta.yaml
│   ├── xgboost_reg.joblib                   + _meta.yaml
│   ├── lstm_BTC.keras                       + _meta.yaml
│   ├── lstm_ETH.keras                       + _meta.yaml
│   ├── lstm_XRP.keras                       + _meta.yaml
│   └── lstm_DASH.keras                      + _meta.yaml
├── figures/
│   ├── cm_*.png                             matrizes de confusão
│   ├── roc_curves.png                       curvas ROC
│   ├── feat_imp_*.png                       importância de features
│   ├── reg_*_pred_vs_actual.png
│   ├── reg_*_residuos.png
│   ├── lstm_*_history.png
│   ├── lstm_*_predicoes.png
│   └── lstm_*_erros.png
├── reports/
│   ├── comparacao_classificadores.csv
│   ├── comparacao_regressores.csv
│   └── comparacao_lstm.csv
└── logs/
    ├── train_classifiers.log
    ├── train_regressors.log
    ├── train_xgboost.log
    └── train_lstm.log
```

---

## 🔮 Inferência

Modelos treinados podem ser carregados em qualquer notebook ou script via:

```python
from src.inference.predictor import PortfolioPredictor, PricePredictor

# Predizer qualidade e retorno de uma carteira
pred = PortfolioPredictor(classifier_name='random_forest')
pred.predict_quality([0.4, 0.3, 0.2, 0.1])      # → {'sharpe_label_pred': 1, 'prob_boa': 0.78}
pred.predict_return([0.4, 0.3, 0.2, 0.1])       # → 0.00073

# Predizer preço futuro de um ticker
from src.data.loader import load_coin
btc_pred = PricePredictor('BTC')
df = load_coin('BTC')
btc_pred.predict_next_day(df)                    # → 67432.50
btc_pred.predict_horizon(df, horizon=7)          # → array com 7 preços
```

---

## 📚 Próxima fase

Após esta etapa de treinamento, o próximo notebook a ser desenvolvido é o **`04_ai_enhanced_insights.ipynb`** (na pasta de notebooks da raiz do projeto), que vai usar os modelos treinados aqui para gerar uma camada analítica adicional:

- Recomendações de carteira ótima usando os classificadores
- Projeções de preço futuro com a LSTM
- Análise de cenários "what-if" usando o XGBoost regressor
- Comparativo com os insights da análise tradicional (`eda_insights.ipynb`)
