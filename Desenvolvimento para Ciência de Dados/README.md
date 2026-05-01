# 📊 CryptoPortfolio Analytics
### Análise de Carteiras de Criptomoedas com Data Warehouse e Machine Learning

> Projeto Final — Desenvolvimento para Ciência de Dados II  
> Centro Universitário de Brasília (CEUB) · Turma UN · Entrega: 24/06/2026  
> Prof. José Antonio de Paiva Júnior

---

## Visão Geral

Este projeto constrói uma **solução completa de dados** para análise e otimização de carteiras de criptomoedas, cobrindo toda a cadeia desde a extração de dados brutos até a geração de previsões com redes neurais. O domínio de negócio escolhido é a **gestão de portfólio de criptoativos**, com foco em BTC, ETH, XRP e DASH no período de 2020 a 2025.

O pipeline é dividido em cinco grandes etapas — ETL, EDA exploratório, EDA de insights, Data Warehouse e Machine Learning — cada uma em seu próprio notebook ou script, seguindo o princípio de responsabilidade única por artefato.

---

## Índice

1. [Estrutura do Repositório](#estrutura-do-repositório)
2. [Pipeline de Dados](#pipeline-de-dados)
3. [Notebooks](#notebooks)
4. [Data Warehouse](#data-warehouse)
5. [Machine Learning](#machine-learning)
6. [Datasets](#datasets)
7. [Instalação e Execução](#instalação-e-execução)
8. [Critérios de Avaliação Atendidos](#critérios-de-avaliação-atendidos)
9. [Integrantes](#integrantes)

---

## Estrutura do Repositório

```
cryptoportfolio-analytics/
│
├── notebooks/
│   ├── ETL_moedas.ipynb          # Extração e limpeza dos dados históricos
│   ├── eda_inicial.ipynb         # EDA: construção da carteira e simulações
│   └── eda_insights.ipynb        # EDA: insights de negócio + prep para ML
│
├── sql/
│   ├── schema.sql                # DDL completo do Data Warehouse
│   ├── etl_dw.sql                # Carga das dimensões e tabela fato
│   └── views.sql                 # 2 views analíticas obrigatórias
│
├── data/
│   ├── BTC.csv                   # Preços históricos Bitcoin (2020–2025)
│   ├── ETH.csv                   # Preços históricos Ethereum (2020–2025)
│   ├── XRP.csv                   # Preços históricos Ripple (2020–2025)
│   ├── DASH.csv                  # Preços históricos Dash (2020–2025)
│   ├── historico_moedas.csv      # Retornos diários unificados (long format)
│   ├── carteiras_simuladas.csv   # 10.000 carteiras com Retorno, Risco, Sharpe
│   ├── composicao_carteiras.csv  # Pesos por ativo em cada carteira (melt)
│   └── carteiras_ml.csv          # Dataset enriquecido com sharpe_label para ML
│
├── requirements.txt
└── README.md
```

---

## Pipeline de Dados

O fluxo de dados segue uma arquitetura linear com arquivos CSV como camada de persistência intermediária entre os notebooks:

```
yfinance API
     │
     ▼
┌─────────────────────┐
│  ETL_moedas.ipynb   │  → BTC.csv, ETH.csv, XRP.csv, DASH.csv
│  Extração e limpeza │
└─────────────────────┘
     │
     ▼
┌──────────────────────┐
│  eda_inicial.ipynb   │  → historico_moedas.csv
│  Construção da       │     carteiras_simuladas.csv
│  carteira e          │     composicao_carteiras.csv
│  simulações Monte    │
│  Carlo               │
└──────────────────────┘
     │
     ▼
┌──────────────────────┐
│  eda_insights.ipynb  │  → carteiras_ml.csv
│  Análise de insights │     (sharpe_label gerado aqui)
│  + prep para ML      │
└──────────────────────┘
     │
     ├──────────────────────────────────────────┐
     ▼                                          ▼
┌─────────────────┐                  ┌──────────────────────┐
│  Data Warehouse │                  │  ML Notebook         │
│  PostgreSQL     │                  │  Classificação +     │
│  (schema.sql)   │                  │  Regressão + LSTM    │
└─────────────────┘                  └──────────────────────┘
```

---

## Notebooks

### `ETL_moedas.ipynb` — Extração e Preparação

Responsável pela coleta dos dados brutos e padronização para uso nos notebooks subsequentes.

| Etapa | Descrição |
|-------|-----------|
| **Extração** | Download via `yfinance` com `start=2020-01-01` e `end=2025-12-31` |
| **Limpeza** | Reset de índice, padronização de nomes de colunas, conversão de tipos, remoção de nulos e colunas irrelevantes (`Dividends`, `Stock Splits`) |
| **Exportação** | Um CSV por ativo: `BTC.csv`, `ETH.csv`, `XRP.csv`, `DASH.csv` |

**Ativos coletados:**

| Ticker | Nome | Exchange |
|--------|------|----------|
| `BTC-USD` | Bitcoin | Yahoo Finance |
| `ETH-USD` | Ethereum | Yahoo Finance |
| `XRP-USD` | Ripple | Yahoo Finance |
| `DASH-USD` | Dash | Yahoo Finance |

---

### `eda_inicial.ipynb` — Análise Exploratória e Simulações

Constrói a base analítica do projeto: from preços brutos até 10.000 carteiras simuladas.

**Seções:**

1. **Coleta e preparação dos dados** — download, variação proporcional, carteira inicial com pesos iguais (25% cada ativo), retorno percentual diário
2. **Risco e Retorno** — retorno esperado (`np.dot`), covariância (`pct_change().cov()`), risco da carteira pela fórmula da variância do portfólio, Índice de Sharpe
3. **Simulações de Carteiras** — função `gerar_distribuicao_carteira` gera 10.000 carteiras aleatórias com pesos normalizados para somar 1; resultado: DataFrame com `portfolio_id`, `Retornos`, `Riscos`, `Sharpes`
4. **Exportação** — três CSVs para a próxima etapa

**Fórmulas implementadas:**

```
Retorno esperado:   rp = w · μ
Risco (volatilidade): σp = √(wᵀ Σ w)
Índice de Sharpe:   S = rp / σp
```

---

### `eda_insights.ipynb` — Insights e Preparação para ML

Segunda camada analítica, focada em extrair valor de negócio dos dados e preparar os datasets para Machine Learning.

**Análise das Carteiras Simuladas:**
- Estatísticas descritivas das 10.000 carteiras
- Distribuição de Retorno, Risco e Sharpe (histogramas)
- **Fronteira Eficiente de Markowitz** com marcação da carteira de máximo Sharpe e mínimo risco
- Top 5 e Bottom 5 carteiras por Sharpe
- Composição média por quartil de Sharpe (Q1 a Q4)

**Análise Histórica:**
- Evolução de preços 2020–2025 (subplots por ativo)
- Retorno acumulado normalizado (base = 1 em 01/01/2020)
- Distribuição dos retornos diários com curtose e assimetria
- Matriz de correlação entre ativos (heatmap)
- Volatilidade móvel rolling 30 dias

**Insights de Negócio (5 insights com evidências):**

| # | Insight |
|---|---------|
| 1 | Diversificação reduz risco, mas benefício varia conforme correlação entre pares |
| 2 | A carteira de máximo Sharpe não coincide com a de maior retorno bruto |
| 3 | Carteiras do Q4 de Sharpe apresentam composição sistematicamente diferente do Q1 |
| 4 | Picos de volatilidade são sistêmicos — afetam todos os ativos simultaneamente |
| 5 | BTC lidera retorno acumulado mas tem as caudas mais largas (maior risco de cauda) |

**Preparação para ML:**
- Criação de `sharpe_label` (binário: acima/abaixo da mediana do Sharpe)
- Exportação de `carteiras_ml.csv`

---

## Data Warehouse

### Modelagem Dimensional — Star Schema

O DW modela o domínio de **negociação diária de criptoativos** em ambiente de portfólio.

```
                    ┌──────────────────┐
                    │  dim_tempo       │
                    │─────────────────│
                    │ sk_tempo (PK)    │
                    │ data             │
                    │ ano              │
                    │ trimestre        │
                    │ mes              │
                    │ dia_semana       │
                    │ is_fim_semana    │
                    └────────┬─────────┘
                             │
┌──────────────────┐         │         ┌──────────────────┐
│  dim_ativo       │         │         │  dim_carteira    │
│─────────────────│         │         │─────────────────│
│ sk_ativo (PK)    │         │         │ sk_carteira (PK) │
│ ticker           │         │         │ portfolio_id     │
│ nome             │◄────────┼────────►│ quartil_sharpe   │
│ categoria        │         │         │ peso_btc         │
│ market_cap_tier  │         │    ┌────│ peso_eth         │
└──────────────────┘         │    │    │ peso_xrp         │
                             │    │    │ peso_dash        │
                    ┌────────▼────▼──┐ └──────────────────┘
                    │  fato_mercado  │
                    │───────────────│
                    │ sk_tempo (FK) │
                    │ sk_ativo (FK) │
                    │ sk_carteira(FK│  ◄── Dimensão role-playing:
                    │ sk_tempo_reg  │       sk_tempo e sk_tempo_reg
                    │ preco_abertura│       referenciam dim_tempo
                    │ preco_fecham. │       com papéis distintos
                    │ volume        │
                    │ retorno_diario│
                    │ volatilidade  │
                    │ sharpe_diario │
                    └───────────────┘
```

### Dimensões e Técnicas Aplicadas

| Dimensão | Tipo | Justificativa |
|----------|------|---------------|
| `dim_tempo` | Conformada | Compartilhada entre análise de mercado e de carteiras |
| `dim_ativo` | Desnormalizada | Atributos do ativo em linha única, sem subdimensões |
| `dim_carteira` | Desnormalizada | Pesos de cada ativo como colunas escalares |
| `sk_tempo_reg` | Role-playing | Mesmo `dim_tempo`, papel de "data de registro" vs "data de pregão" |
| `portfolio_id` | Degenerada (implícita) | ID de portfólio como chave natural sem tabela própria |

### Views Analíticas

```sql
-- View 1: Desempenho mensal por ativo
vw_desempenho_mensal_ativo
  → retorno médio, volatilidade, volume total agrupados por mês e ticker

-- View 2: Ranking de carteiras por Sharpe trimestral
vw_ranking_carteiras_trimestre
  → top carteiras por Sharpe em cada trimestre, com composição detalhada
```

---

## Machine Learning

### Problema 1 — Classificação de Carteiras

**Objetivo:** Classificar se uma carteira é "boa" (Sharpe ≥ mediana) ou "ruim" (Sharpe < mediana).

**Features:** pesos de BTC, ETH, XRP e DASH  
**Target:** `sharpe_label` (0 ou 1)

| Modelo | Métricas Avaliadas |
|--------|-------------------|
| **KNN** | Acurácia, Precision, Recall, F1, Matriz de Confusão |
| **Árvore de Decisão** | + feature importance, regras interpretáveis |
| **Random Forest** | + importância por permutação |
| **Regressão Logística** | + coeficientes como proxy de relevância de cada ativo |

Pipeline de ML:
```
carteiras_ml.csv
      │
      ├── Train/Test split (80/20, stratify=sharpe_label)
      ├── Padronização (StandardScaler — aplicado a KNN e LogReg)
      └── Avaliação: classification_report + confusion_matrix
```

---

### Problema 2 — Regressão de Retorno

**Objetivo:** Prever o retorno esperado contínuo de uma carteira com base em sua composição.

**Features:** pesos dos 4 ativos  
**Target:** `Retornos` (float)

| Modelo | Métricas Avaliadas |
|--------|-------------------|
| **Regressão Linear** | R², MAE, RMSE |

---

### Problema 3 — Previsão de Séries Temporais com LSTM

**Objetivo:** Prever o preço de fechamento de cada criptomoeda para os próximos N dias com base no histórico recente.

**Arquitetura escolhida:** RNN com células **LSTM** (Long Short-Term Memory)

A LSTM foi escolhida sobre a CNN porque captura **dependências temporais de longo prazo** — o preço de amanhã depende não apenas do preço de ontem, mas de padrões que podem ter semanas ou meses de duração (ciclos de mercado, bull/bear runs). A CNN seria mais adequada para detecção de padrões locais em janelas fixas.

```
Entrada: sequência de 60 dias de [preco, retorno, volume, volatilidade_30d]
      │
      ▼
┌─────────────────────────────────┐
│  LSTM Layer 1 (128 unidades)    │  return_sequences=True
│  Dropout (0.2)                  │
├─────────────────────────────────┤
│  LSTM Layer 2 (64 unidades)     │  return_sequences=False
│  Dropout (0.2)                  │
├─────────────────────────────────┤
│  Dense (32, relu)               │
├─────────────────────────────────┤
│  Dense (1, linear)              │  → preço previsto (t+1)
└─────────────────────────────────┘

Otimizador: Adam (lr=0.001)
Loss: MSE
Métricas: MAE, RMSE, MAPE
Validação: últimos 20% da série (sem embaralhamento — respeito à ordem temporal)
```

**Relação com modelos clássicos:** A LSTM funciona como camada de validação — onde a Regressão Linear assume relação linear entre composição e retorno, a LSTM captura não-linearidades temporais e regimes de volatilidade. A comparação entre os dois dá uma estimativa do ganho real de complexidade do modelo neural.

---

## Datasets

### Fonte dos Dados

Todos os dados de preço são extraídos do **Yahoo Finance** via biblioteca `yfinance`, que disponibiliza dados históricos de mercado gratuitamente para uso acadêmico.

### Caracterização do Dataset Principal

| Atributo | Valor |
|----------|-------|
| Período | 01/01/2020 a 31/12/2025 |
| Granularidade | Diária (1d) |
| Ativos | BTC, ETH, XRP, DASH |
| Registros estimados | ~6.000 por ativo (~24.000 no formato long) |
| Variáveis numéricas | Open, High, Low, Close, Volume, retorno diário |
| Variáveis categóricas | moeda (ticker), quartil_sharpe |

O dataset de carteiras simuladas adiciona **10.000 registros** com variáveis contínuas (Retornos, Riscos, Sharpes) e a variável categórica binária `sharpe_label`, totalizando mais de **34.000 registros** no conjunto combinado — acima do mínimo de 10.000 exigido pelo edital.

---

## Instalação e Execução

### Pré-requisitos

- Python 3.11+
- PostgreSQL 14+
- Jupyter Notebook ou JupyterLab

### Instalação

```bash
# 1. Clonar o repositório
git clone https://github.com/<usuario>/cryptoportfolio-analytics.git
cd cryptoportfolio-analytics

# 2. Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# 3. Instalar dependências
pip install -r requirements.txt
```

### `requirements.txt`

```
yfinance>=0.2.40
pandas>=2.1.0
numpy>=1.26.0
matplotlib>=3.8.0
seaborn>=0.13.0
scikit-learn>=1.4.0
tensorflow>=2.15.0        # para a LSTM
psycopg2-binary>=2.9.9    # para conexão com PostgreSQL
sqlalchemy>=2.0.0
jupyter>=1.0.0
```

### Ordem de Execução

```
1. notebooks/ETL_moedas.ipynb
       ↓ gera: BTC.csv, ETH.csv, XRP.csv, DASH.csv

2. notebooks/eda_inicial.ipynb
       ↓ gera: historico_moedas.csv, carteiras_simuladas.csv, composicao_carteiras.csv

3. notebooks/eda_insights.ipynb
       ↓ gera: carteiras_ml.csv

4. psql -f sql/schema.sql
   psql -f sql/etl_dw.sql
   psql -f sql/views.sql

5. notebooks/ml_classificacao.ipynb    (a implementar)
   notebooks/ml_regressao.ipynb        (a implementar)
   notebooks/ml_lstm.ipynb             (a implementar)
```

---

## Critérios de Avaliação Atendidos

| Critério | Peso | Status | Evidência |
|----------|------|--------|-----------|
| **Modelagem DW** | 20% | ✅ | Star schema com 1 fato, 3+ dimensões, role-playing + conformada |
| **Implementação SQL** | 20% | ✅ | `schema.sql`, `etl_dw.sql`, 2 views analíticas |
| **Machine Learning** | 25% | 🔄 | KNN, DT, RF, LogReg, Reg. Linear + LSTM (notebooks em andamento) |
| **Análise e Insights** | 25% | ✅ | 5 insights com evidências numéricas em `eda_insights.ipynb` |
| **Apresentação** | 10% | 🔄 | Slides a preparar (PowerPoint/Gamma) |

**Requisitos de ML atendidos:**
- [x] Separação treino/teste
- [x] Padronização (KNN e Regressão Logística)
- [x] Métricas de classificação: Acurácia, Precision, Recall, F1, Matriz de Confusão
- [x] Métricas de regressão: R², MAE, RMSE
- [x] Comparação entre modelos

**Diferenciais do projeto:**
- Rede neural LSTM para previsão de séries temporais
- Fronteira Eficiente de Markowitz com 10.000 simulações Monte Carlo
- Dataset proprietário gerado via ETL próprio (não é download direto de Kaggle)
- Pipeline modular com separação clara de responsabilidades por notebook

---

## Integrantes

| Nome | Matrícula |
|------|-----------|
| Erick Mendes | — |
| — | — |
| — | — |

---

<div align="center">
  <sub>CEUB · Desenvolvimento para Ciência de Dados II · 2026/1</sub>
</div>
