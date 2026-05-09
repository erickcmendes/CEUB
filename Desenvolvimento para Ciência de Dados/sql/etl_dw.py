"""
ETL: popula o Data Warehouse a partir dos CSVs gerados pelos notebooks.

Este script:
1. Lê credenciais de variáveis de ambiente (com fallback para defaults seguros)
2. Resolve os caminhos dos CSVs relativos ao próprio arquivo (sem hardcoded)
3. Popula dim_tempo, dim_ativo, dim_carteira e fato_mercado
l
Pré-requisitos:
    - schema.sql já executado no banco
    - CSVs presentes em <raiz_projeto>/data/
    - Variáveis de ambiente PG_DB, PG_USER, PG_PASS, PG_HOST, PG_PORT
      (ou edite os defaults abaixo)

Uso:
    python sql/etl_dw.py
"""
import os
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2

# ── 0. Paths relativos ao próprio arquivo ────────────────────────────────────
# etl_dw.py está em <projeto>/sql/etl_dw.py
SQL_DIR  = Path(__file__).resolve().parent
ROOT_DIR = SQL_DIR.parent
DATA_DIR = ROOT_DIR / "data"

CARTEIRAS_ML_CSV = DATA_DIR / "carteiras_ml.csv"
HISTORICO_CSV    = DATA_DIR / "historico_moedas.csv"

# Verificações iniciais (falha cedo, com mensagem clara)
for csv in (CARTEIRAS_ML_CSV, HISTORICO_CSV):
    if not csv.exists():
        raise FileNotFoundError(
            f"Arquivo {csv} não encontrado.\n"
            f"Execute os notebooks da pasta 'Carteira de Criptomoedas/' "
            f"antes de rodar este ETL."
        )

# ── 1. Conexão (variáveis de ambiente com fallback) ──────────────────────────
conn = psycopg2.connect(
    dbname  = os.environ.get("PG_DB",   "Projeto Final"),
    user    = os.environ.get("PG_USER", "postgres"),
    password= os.environ.get("PG_PASS", "ceub123456"),
    host    = os.environ.get("PG_HOST", "localhost"),
    port    = int(os.environ.get("PG_PORT", 5432)),
)
cur = conn.cursor()

# ── 2. dim_tempo ─────────────────────────────────────────────────────────────
datas = pd.date_range("2020-01-01", "2025-12-31", freq="D")
nomes_mes = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
             "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
nomes_dia = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]

for d in datas:
    cur.execute("""
        INSERT INTO dim_tempo
            (data, ano, trimestre, mes, nome_mes, semana_ano, dia_semana, nome_dia, is_fim_semana)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (data) DO NOTHING
    """, (
        d.date(),
        d.year,
        d.quarter,
        d.month,
        nomes_mes[d.month - 1],
        d.isocalendar()[1],
        d.weekday(),
        nomes_dia[d.weekday()],
        d.weekday() >= 5
    ))

conn.commit()
print("dim_tempo: OK")

# ── 3. dim_ativo ─────────────────────────────────────────────────────────────
ativos = [
    ("BTC",  "Bitcoin",  "Layer 1", "Large"),
    ("ETH",  "Ethereum", "Layer 1", "Large"),
    ("XRP",  "Ripple",   "Payment", "Large"),
    ("DASH", "Dash",     "Payment", "Mid"),
]
for ticker, nome, categoria, tier in ativos:
    cur.execute("""
        INSERT INTO dim_ativo (ticker, nome, categoria, market_cap_tier)
        VALUES (%s,%s,%s,%s)
        ON CONFLICT (ticker) DO NOTHING
    """, (ticker, nome, categoria, tier))

conn.commit()
print("dim_ativo: OK")

# ── 4. dim_carteira ──────────────────────────────────────────────────────────
df_ml = pd.read_csv(CARTEIRAS_ML_CSV)

# detectar colunas de peso (padrão gerado pelo notebook)
colunas_peso = [c for c in df_ml.columns if "comp" in c.lower()]
mapa = {colunas_peso[i]: ["peso_btc","peso_eth","peso_xrp","peso_dash"][i]
        for i in range(4)}
df_ml = df_ml.rename(columns=mapa)

for _, row in df_ml.iterrows():
    cur.execute("""
        INSERT INTO dim_carteira
            (portfolio_id, peso_btc, peso_eth, peso_xrp, peso_dash,
             sharpe_label, quartil_sharpe)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (portfolio_id) DO NOTHING
    """, (
        int(row["portfolio_id"]),
        float(row["peso_btc"]),
        float(row["peso_eth"]),
        float(row["peso_xrp"]),
        float(row["peso_dash"]),
        int(row["sharpe_label"]),
        str(row["quartil_sharpe"])
    ))

conn.commit()
print("dim_carteira: OK")

# ── 5. fato_mercado ──────────────────────────────────────────────────────────
# Mapas de lookup (SK das dimensões)
cur.execute("SELECT sk_tempo, data FROM dim_tempo")
map_tempo = {str(r[1]): r[0] for r in cur.fetchall()}

cur.execute("SELECT sk_ativo, ticker FROM dim_ativo")
map_ativo = {r[1]: r[0] for r in cur.fetchall()}

cur.execute("SELECT sk_carteira, portfolio_id FROM dim_carteira")
map_carteira = {r[1]: r[0] for r in cur.fetchall()}

# portfolio_id=0 funciona como carteira de referência para os fatos de preço
# (cada linha de preço não pertence a uma carteira específica)
SK_CARTEIRA_REF = map_carteira[0]

# Data de coleta = hoje (ou primeira data disponível, se "hoje" estiver fora de 2020-2025)
DATA_COLETA = str(date.today())
SK_COLETA   = map_tempo.get(DATA_COLETA, map_tempo[min(map_tempo.keys())])

df_hist = pd.read_csv(HISTORICO_CSV, parse_dates=["date"])

# Calcular retorno acumulado e volatilidade 30d por moeda
df_hist = df_hist.sort_values(["moeda", "date"])
df_hist["retorno_acumulado"] = df_hist.groupby("moeda")["retorno"].transform(
    lambda x: (1 + x).cumprod() - 1
)
df_hist["volatilidade_30d"] = df_hist.groupby("moeda")["retorno"].transform(
    lambda x: x.rolling(30).std()
)

inseridos = 0
for _, row in df_hist.iterrows():
    data_str = str(row["date"].date())

    # Limpando a string para garantir que " btc", "btc" ou "BTC" fiquem iguais ao banco
    moeda_limpa = str(row["moeda"]).split("-")[0].strip().upper()

    sk_tempo = map_tempo.get(data_str)
    sk_ativo = map_ativo.get(moeda_limpa)

    if not sk_tempo or not sk_ativo:
        print(f"[Pulado] Data: {data_str} (SK: {sk_tempo}) | "
              f"Moeda CSV: '{row['moeda']}' -> '{moeda_limpa}' (SK: {sk_ativo})")
        continue

    cur.execute("""
        INSERT INTO fato_mercado
            (sk_tempo_pregao, sk_tempo_coleta, sk_ativo, sk_carteira,
             preco_fechamento, retorno_diario, volatilidade_30d, retorno_acumulado)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        sk_tempo,
        SK_COLETA,
        sk_ativo,
        SK_CARTEIRA_REF,
        float(row.get("preco", row.get("Close", 0))),
        float(row["retorno"])           if pd.notna(row["retorno"])           else None,
        float(row["volatilidade_30d"])  if pd.notna(row["volatilidade_30d"])  else None,
        float(row["retorno_acumulado"]) if pd.notna(row["retorno_acumulado"]) else None,
    ))
    inseridos += 1

conn.commit()
print(f"fato_mercado: {inseridos} linhas inseridas")

cur.close()
conn.close()
