import pandas as pd
import numpy as np
import psycopg2
from datetime import date

conn = psycopg2.connect(
    dbname="Projeto Final",
    user="postgres",
    password="ceub123456",
    host="localhost",
    port=5432
)
cur = conn.cursor()

# ── 1. dim_tempo ──────────────────────────────────────────────
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

# ── 2. dim_ativo ─────────────────────────────────────────────
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

# ── 3. dim_carteira ───────────────────────────────────────────
df_ml = pd.read_csv(r"C:\Users\sophia.silva\Documents\CEUB\Desenvolvimento para Ciência de Dados\data\carteiras_ml.csv")

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

# ── 4. fato_mercado ───────────────────────────────────────────
# Mapas de lookup (SK das dimensões)
cur.execute("SELECT sk_tempo, data FROM dim_tempo")
map_tempo = {str(r[1]): r[0] for r in cur.fetchall()}

cur.execute("SELECT sk_ativo, ticker FROM dim_ativo")
map_ativo = {r[1]: r[0] for r in cur.fetchall()}

cur.execute("SELECT sk_carteira, portfolio_id FROM dim_carteira")
map_carteira = {r[1]: r[0] for r in cur.fetchall()}

# Usaremos a carteira de portfolio_id=0 como carteira de referência para os fatos de preço
# (cada linha de preço não pertence a uma carteira específica — usamos um portfolio sentinela)
SK_CARTEIRA_REF = map_carteira[0]

# Data de coleta = hoje (data em que o ETL rodou)
DATA_COLETA = str(date.today())
SK_COLETA = map_tempo.get(DATA_COLETA, map_tempo[min(map_tempo.keys())])

df_hist = pd.read_csv(r"C:\Users\sophia.silva\Documents\CEUB\Desenvolvimento para Ciência de Dados\data\historico_moedas.csv", parse_dates=["date"])

# Calcular retorno acumulado por moeda
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
    
    sk_tempo  = map_tempo.get(data_str)
    sk_ativo  = map_ativo.get(moeda_limpa)
    
    if not sk_tempo or not sk_ativo:
        # Este print vai te mostrar exatamente qual chave está faltando!
        print(f"[Pulado] Data: {data_str} (SK: {sk_tempo}) | Moeda CSV: '{row['moeda']}' -> '{moeda_limpa}' (SK: {sk_ativo})")
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
        float(row["retorno"])     if pd.notna(row["retorno"])         else None,
        float(row["volatilidade_30d"]) if pd.notna(row["volatilidade_30d"]) else None,
        float(row["retorno_acumulado"]) if pd.notna(row["retorno_acumulado"]) else None,
    ))
    inseridos += 1

conn.commit()
print(f"fato_mercado: {inseridos} linhas inseridas")

cur.close()
conn.close()
