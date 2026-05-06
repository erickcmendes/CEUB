-- ============================================================
-- SCHEMA — CryptoPortfolio Analytics Data Warehouse
-- Star Schema | PostgreSQL 14+
-- ============================================================

-- ── DIMENSÃO TEMPO (conformada) ──────────────────────────────
-- Compartilhada entre análise de mercado e de carteiras.
-- Será usada em role-playing: sk_tempo (pregão) e sk_tempo_registro.

CREATE TABLE dim_tempo (
    sk_tempo        SERIAL PRIMARY KEY,
    data            DATE        NOT NULL UNIQUE,
    ano             SMALLINT    NOT NULL,
    trimestre       SMALLINT    NOT NULL,  -- 1 a 4
    mes             SMALLINT    NOT NULL,  -- 1 a 12
    nome_mes        VARCHAR(15) NOT NULL,
    semana_ano      SMALLINT    NOT NULL,
    dia_semana      SMALLINT    NOT NULL,  -- 0=seg ... 6=dom
    nome_dia        VARCHAR(15) NOT NULL,
    is_fim_semana   BOOLEAN     NOT NULL
);

-- ── DIMENSÃO ATIVO (desnormalizada) ──────────────────────────
-- Atributos descritivos de cada criptomoeda em linha única.

CREATE TABLE dim_ativo (
    sk_ativo        SERIAL PRIMARY KEY,
    ticker          VARCHAR(10) NOT NULL UNIQUE,
    nome            VARCHAR(50) NOT NULL,
    categoria       VARCHAR(30) NOT NULL,  -- ex: 'Layer 1', 'Payment'
    market_cap_tier VARCHAR(10) NOT NULL   -- 'Large', 'Mid', 'Small'
);

-- ── DIMENSÃO CARTEIRA (desnormalizada) ───────────────────────
-- Cada linha é uma carteira simulada.
-- Os pesos dos 4 ativos ficam como colunas escalares (desnormalizado).

CREATE TABLE dim_carteira (
    sk_carteira     SERIAL PRIMARY KEY,
    portfolio_id    INTEGER     NOT NULL UNIQUE,
    peso_btc        NUMERIC(6,4) NOT NULL,
    peso_eth        NUMERIC(6,4) NOT NULL,
    peso_xrp        NUMERIC(6,4) NOT NULL,
    peso_dash       NUMERIC(6,4) NOT NULL,
    sharpe_label    SMALLINT    NOT NULL,  -- 0=ruim, 1=boa
    quartil_sharpe  VARCHAR(15) NOT NULL   -- Q1, Q2, Q3, Q4
);

-- ── TABELA FATO ───────────────────────────────────────────────
-- Grão: um ativo em um dia de pregão associado a uma carteira.
-- sk_tempo_pregao  → dim_tempo (papel: data do pregão)   [role-playing]
-- sk_tempo_coleta  → dim_tempo (papel: data da coleta)   [role-playing]

CREATE TABLE fato_mercado (
    sk_fato             BIGSERIAL   PRIMARY KEY,

    -- Chaves estrangeiras (dimensões)
    sk_tempo_pregao     INTEGER     NOT NULL REFERENCES dim_tempo(sk_tempo),
    sk_tempo_coleta     INTEGER     NOT NULL REFERENCES dim_tempo(sk_tempo),
    sk_ativo            INTEGER     NOT NULL REFERENCES dim_ativo(sk_ativo),
    sk_carteira         INTEGER     NOT NULL REFERENCES dim_carteira(sk_carteira),

    -- Medidas brutas (preço)
    preco_abertura      NUMERIC(18,6),
    preco_maximo        NUMERIC(18,6),
    preco_minimo        NUMERIC(18,6),
    preco_fechamento    NUMERIC(18,6) NOT NULL,
    volume              NUMERIC(24,2),

    -- Medidas derivadas (calculadas no ETL)
    retorno_diario      NUMERIC(10,6),   -- variação % vs dia anterior
    volatilidade_30d    NUMERIC(10,6),   -- desvio padrão rolling 30d
    retorno_acumulado   NUMERIC(10,6)    -- retorno acumulado desde 2020-01-01
);

-- ── ÍNDICES ───────────────────────────────────────────────────
CREATE INDEX idx_fato_tempo_pregao ON fato_mercado(sk_tempo_pregao);
CREATE INDEX idx_fato_ativo        ON fato_mercado(sk_ativo);
CREATE INDEX idx_fato_carteira     ON fato_mercado(sk_carteira);
