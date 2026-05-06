-- ============================================================
-- VIEWS ANALÍTICAS — CryptoPortfolio DW
-- ============================================================

-- ── View 1: Desempenho mensal por ativo ─────────────────────
-- Agrega retorno médio, volatilidade e volume por mês e ticker.
-- Útil para comparar sazonalidade e ciclos de mercado.

CREATE OR REPLACE VIEW vw_desempenho_mensal_ativo AS
SELECT
    t.ano,
    t.mes,
    t.nome_mes,
    a.ticker,
    a.nome                              AS nome_ativo,
    ROUND(AVG(f.retorno_diario)::NUMERIC, 6)    AS retorno_medio_diario,
    ROUND(STDDEV(f.retorno_diario)::NUMERIC, 6) AS volatilidade_mensal,
    ROUND(MAX(f.preco_fechamento)::NUMERIC, 2)  AS preco_maximo,
    ROUND(MIN(f.preco_fechamento)::NUMERIC, 2)  AS preco_minimo,
    COUNT(*)                            AS dias_negociados
FROM fato_mercado f
JOIN dim_tempo  t ON f.sk_tempo_pregao = t.sk_tempo
JOIN dim_ativo  a ON f.sk_ativo        = a.sk_ativo
GROUP BY t.ano, t.mes, t.nome_mes, a.ticker, a.nome
ORDER BY t.ano, t.mes, a.ticker;


-- ── View 2: Ranking de carteiras por Sharpe por trimestre ───
-- Mostra as top 10 carteiras de cada trimestre,
-- com composição completa e classificação do sharpe_label.

CREATE OR REPLACE VIEW vw_ranking_carteiras_trimestre AS
SELECT
    t.ano,
    t.trimestre,
    c.portfolio_id,
    c.sharpe_label,
    c.quartil_sharpe,
    ROUND(c.peso_btc  * 100, 2) AS pct_btc,
    ROUND(c.peso_eth  * 100, 2) AS pct_eth,
    ROUND(c.peso_xrp  * 100, 2) AS pct_xrp,
    ROUND(c.peso_dash * 100, 2) AS pct_dash,
    ROUND(AVG(f.retorno_diario)::NUMERIC,   6) AS retorno_medio,
    ROUND(STDDEV(f.retorno_diario)::NUMERIC, 6) AS risco_realizado,
    RANK() OVER (
        PARTITION BY t.ano, t.trimestre
        ORDER BY AVG(f.retorno_diario) / NULLIF(STDDEV(f.retorno_diario), 0) DESC
    ) AS rank_sharpe_realizado
FROM fato_mercado f
JOIN dim_tempo    t ON f.sk_tempo_pregao = t.sk_tempo
JOIN dim_carteira c ON f.sk_carteira     = c.sk_carteira
GROUP BY t.ano, t.trimestre, c.portfolio_id, c.sharpe_label,
         c.quartil_sharpe, c.peso_btc, c.peso_eth, c.peso_xrp, c.peso_dash
ORDER BY t.ano, t.trimestre, rank_sharpe_realizado;
