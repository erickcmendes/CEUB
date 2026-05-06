# Instruções — Data Warehouse no PostgreSQL
### CryptoPortfolio Analytics · pasta `sql/`

---

## Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Estrutura da pasta](#2-estrutura-da-pasta)
3. [Criando o banco de dados](#3-criando-o-banco-de-dados)
4. [Entendendo o modelo dimensional](#4-entendendo-o-modelo-dimensional)
5. [Executando o schema](#5-executando-o-schema)
6. [Executando a carga de dados](#6-executando-a-carga-de-dados)
7. [Criando as views analíticas](#7-criando-as-views-analíticas)
8. [Validando a instalação](#8-validando-a-instalação)
9. [Referência rápida de comandos](#9-referência-rápida-de-comandos)

---

## 1. Pré-requisitos

Antes de executar qualquer arquivo desta pasta, garanta que seu ambiente atende aos seguintes requisitos:

**Software necessário:**

| Software | Versão mínima | Como verificar |
|----------|---------------|----------------|
| PostgreSQL | 14 | `psql --version` |
| Python | 3.11 | `python --version` |
| psycopg2-binary | 2.9 | `pip show psycopg2-binary` |
| pandas | 2.1 | `pip show pandas` |

**Arquivos CSV necessários** (gerados pelos notebooks anteriores):

| Arquivo | Gerado por | Obrigatório |
|---------|-----------|-------------|
| `data/historico_moedas.csv` | `eda_inicial.ipynb` | ✅ |
| `data/carteiras_ml.csv` | `eda_insights.ipynb` | ✅ |

> ⚠️ Execute os notebooks **na ordem correta** antes de rodar qualquer script desta pasta. Consulte o `README.md` na raiz do projeto para a ordem de execução completa.

---

## 2. Estrutura da pasta

```
sql/
├── instrucoes_datawarehouse.md   ← este arquivo
├── schema.sql                    ← DDL: cria tabelas, índices e constraints
├── etl_dw.py                     ← ETL: popula o banco a partir dos CSVs
└── views.sql                     ← Cria as 2 views analíticas obrigatórias
```

**Ordem de execução obrigatória:**

```
schema.sql  →  etl_dw.py  →  views.sql
```

Nunca execute `etl_dw.py` antes de `schema.sql` — as tabelas precisam existir antes da carga.  
Nunca execute `views.sql` antes de `etl_dw.py` — as views dependem de dados já inseridos para validação.

---

## 3. Criando o banco de dados

### 3.1 Conectar no PostgreSQL

Abra o terminal e acesse o cliente `psql` com o superusuário:

```bash
psql -U postgres
```

Se o PostgreSQL estiver em uma porta ou host diferente do padrão:

```bash
psql -U postgres -h localhost -p 5432
```

### 3.2 Criar o banco e conectar

Dentro do prompt `postgres=#`, execute:

```sql
CREATE DATABASE cryptoportfolio
    ENCODING 'UTF8'
    LC_COLLATE 'pt_BR.UTF-8'
    LC_CTYPE   'pt_BR.UTF-8'
    TEMPLATE template0;
```

> Se o seu sistema não tiver o locale `pt_BR.UTF-8` configurado, use a alternativa sem locale explícito:
> ```sql
> CREATE DATABASE cryptoportfolio ENCODING 'UTF8';
> ```

Conecte ao banco recém-criado:

```sql
\c cryptoportfolio
```

O prompt mudará para `cryptoportfolio=#`. A partir daqui todos os comandos operam neste banco.

---

## 4. Entendendo o modelo dimensional

O projeto implementa um **Star Schema** — arquitetura clássica de Data Warehouse onde uma tabela central de fatos é cercada por dimensões desnormalizadas.

### 4.1 Diagrama do Star Schema

```
                     ┌─────────────────────┐
                     │     dim_tempo        │
                     │─────────────────────│
                     │ sk_tempo  (PK)       │
                     │ data                 │
                     │ ano                  │
                     │ trimestre            │
                     │ mes / nome_mes       │
                     │ semana_ano           │
                     │ dia_semana / nome_dia│
                     │ is_fim_semana        │
                     └──────────┬──────────┘
                                │
                 ┌──────────────┴──────────────┐
                 │ sk_tempo_pregao              │ sk_tempo_coleta
                 │                              │
┌────────────────┴──────────────────────────────┴──────────────┐
│                        fato_mercado                           │
│──────────────────────────────────────────────────────────────│
│ sk_fato            (PK BIGSERIAL)                             │
│ sk_tempo_pregao    (FK → dim_tempo)   papel: data do pregão  │
│ sk_tempo_coleta    (FK → dim_tempo)   papel: data da coleta  │
│ sk_ativo           (FK → dim_ativo)                           │
│ sk_carteira        (FK → dim_carteira)                        │
│ preco_abertura / preco_maximo / preco_minimo / preco_fechamento│
│ volume                                                        │
│ retorno_diario                                                │
│ volatilidade_30d                                              │
│ retorno_acumulado                                             │
└──────────────┬────────────────────────────────┬──────────────┘
               │                                │
   ┌───────────┴───────────┐      ┌─────────────┴──────────────┐
   │      dim_ativo         │      │       dim_carteira          │
   │───────────────────────│      │────────────────────────────│
   │ sk_ativo    (PK)       │      │ sk_carteira    (PK)         │
   │ ticker                 │      │ portfolio_id               │
   │ nome                   │      │ peso_btc                   │
   │ categoria              │      │ peso_eth                   │
   │ market_cap_tier        │      │ peso_xrp                   │
   └───────────────────────┘      │ peso_dash                  │
                                  │ sharpe_label               │
                                  │ quartil_sharpe             │
                                  └────────────────────────────┘
```

### 4.2 Grão da tabela fato

> **Grão:** um registro de preço de **um ativo** em **um dia de pregão**, associado a **uma carteira de referência**.

O grão define o nível de detalhe mais granular da tabela fato. Toda pergunta analítica deve ser respondível a partir dele ou de agregações sobre ele.

### 4.3 Técnicas dimensionais aplicadas

| Técnica | Onde | Como foi implementada |
|---------|------|----------------------|
| **Star Schema** | Estrutura geral | 1 fato central + 3 dimensões ao redor, sem joins entre dimensões |
| **Dimensão desnormalizada** | `dim_ativo`, `dim_carteira` | Todos os atributos em linha única, sem subdimensões |
| **Dimensão conformada** | `dim_tempo` | Mesma tabela referenciada por dois papéis distintos na fato |
| **Dimensão role-playing** | `dim_tempo` via `sk_tempo_pregao` e `sk_tempo_coleta` | A mesma tabela física é usada com dois aliases de FK para representar datas com semânticas diferentes |

#### Por que role-playing com `dim_tempo`?

A tabela fato precisa registrar **duas datas distintas**:

- `sk_tempo_pregao` → quando o preço ocorreu no mercado
- `sk_tempo_coleta` → quando o ETL rodou e coletou o dado

Criar uma segunda tabela `dim_tempo_coleta` seria redundante e quebraria o princípio de dimensões conformadas. A solução correta é ter **duas chaves estrangeiras** apontando para a **mesma** `dim_tempo`, cada uma com seu papel semântico.

No SQL isso se manifesta em queries que fazem **dois JOINs** com a mesma tabela usando aliases:

```sql
SELECT
    tp.data  AS data_pregao,
    tc.data  AS data_coleta,
    ...
FROM fato_mercado f
JOIN dim_tempo tp ON f.sk_tempo_pregao = tp.sk_tempo   -- alias tp
JOIN dim_tempo tc ON f.sk_tempo_coleta = tc.sk_tempo   -- alias tc
```

### 4.4 Surrogate keys vs. natural keys

Todas as dimensões usam **surrogate keys** (`SERIAL` / `BIGSERIAL`) como chave primária, nunca os identificadores naturais (ticker, data, portfolio_id). Isso:

- Protege o DW de mudanças nas fontes de dados
- Permite rastrear histórico com Slowly Changing Dimensions no futuro
- Garante integridade mesmo se a fonte mudar encoding ou formato

---

## 5. Executando o schema

### 5.1 O que `schema.sql` faz

O arquivo cria, nesta ordem:

1. `dim_tempo` — dimensão de tempo com atributos de calendário
2. `dim_ativo` — dimensão dos 4 ativos (BTC, ETH, XRP, DASH)
3. `dim_carteira` — dimensão das 10.000 carteiras simuladas
4. `fato_mercado` — tabela fato com FKs para as 3 dimensões
5. Índices nas colunas de FK da fato para performance analítica

### 5.2 Executar

Na raiz do projeto, com o banco já criado:

```bash
psql -U postgres -d cryptoportfolio -f sql/schema.sql
```

Saída esperada:

```
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
```

### 5.3 Verificar as tabelas criadas

```bash
psql -U postgres -d cryptoportfolio -c "\dt"
```

Saída esperada:

```
          List of relations
 Schema |     Name      | Type  |  Owner
--------+---------------+-------+----------
 public | dim_ativo     | table | postgres
 public | dim_carteira  | table | postgres
 public | dim_tempo     | table | postgres
 public | fato_mercado  | table | postgres
```

### 5.4 Inspecionar a estrutura de uma tabela

```bash
psql -U postgres -d cryptoportfolio -c "\d fato_mercado"
```

---

## 6. Executando a carga de dados

### 6.1 Configurar a conexão

Antes de rodar `etl_dw.py`, edite as credenciais no início do arquivo:

```python
conn = psycopg2.connect(
    dbname="cryptoportfolio",
    user="postgres",
    password="exemplo123",   # ← alterar!
    host="localhost",
    port=5432
)
```

> Se estiver usando variáveis de ambiente:
> ```python
> import os
> conn = psycopg2.connect(
>     dbname=os.environ["PG_DB"],
>     user=os.environ["PG_USER"],
>     password=os.environ["PG_PASS"],
>     host=os.environ.get("PG_HOST", "localhost"),
>     port=int(os.environ.get("PG_PORT", 5432))
> )
> ```

### 6.2 Executar o ETL

```bash
python sql/etl_dw.py
```

Saída esperada:

```
dim_tempo: OK
dim_ativo: OK
dim_carteira: OK
fato_mercado: XXXX linhas inseridas (não pode ser 0)
```

O número de linhas em `fato_mercado` deve ser aproximadamente `nº de dias úteis × 4 ativos` (~6.000).

### 6.3 O que o ETL faz internamente

```
1. Popula dim_tempo com todos os dias de 2020-01-01 a 2025-12-31
2. Insere os 4 ativos fixos em dim_ativo
3. Lê carteiras_ml.csv → insere cada carteira em dim_carteira
4. Lê historico_moedas.csv → calcula retorno acumulado e volatilidade 30d
5. Para cada linha de histórico:
   a. Busca sk_tempo no mapa de dim_tempo (por data)
   b. Busca sk_ativo no mapa de dim_ativo (por ticker/moeda)
   c. Usa sk_carteira de referência (portfolio_id = 0)
   d. Insere na fato_mercado
```

> **Sobre `sk_carteira` na fato:** os dados de preço histórico não pertencem a uma carteira específica — eles são o histórico de mercado. O `portfolio_id = 0` é usado como **carteira sentinela de referência**. Análises que cruzam carteiras com preços devem usar as views, que fazem essa ponte corretamente.

---

## 7. Criando as views analíticas

### 7.1 O que `views.sql` cria

| View | Descrição | Caso de uso |
|------|-----------|-------------|
| `vw_desempenho_mensal_ativo` | Retorno médio, volatilidade, preço máx/mín agrupados por mês e ativo | Análise de sazonalidade, comparação de ciclos de mercado |
| `vw_ranking_carteiras_trimestre` | Ranking de carteiras por Sharpe realizado em cada trimestre, com composição detalhada | Identificar que tipo de carteira performa melhor em cada período |

### 7.2 Executar

```bash
psql -U postgres -d cryptoportfolio -f sql/views.sql
```

Saída esperada:

```
CREATE VIEW
CREATE VIEW
```

### 7.3 Testar as views

```bash
psql -U postgres -d cryptoportfolio
```

```sql
-- Testar view 1: retorno mensal do BTC em 2021
SELECT ano, mes, nome_mes, retorno_medio_diario, volatilidade_mensal
FROM vw_desempenho_mensal_ativo
WHERE ticker = 'BTC' AND ano = 2021
ORDER BY mes;

-- Testar view 2: top 5 carteiras do 1º trimestre de 2022
SELECT portfolio_id, pct_btc, pct_eth, pct_xrp, pct_dash,
       retorno_medio, risco_realizado, rank_sharpe_realizado
FROM vw_ranking_carteiras_trimestre
WHERE ano = 2022 AND trimestre = 1
ORDER BY rank_sharpe_realizado
LIMIT 5;
```

---

## 8. Validando a instalação

Execute este bloco completo no `psql` para confirmar que tudo está correto:

```sql
-- 1. Contagem de registros por tabela
SELECT 'dim_tempo'    AS tabela, COUNT(*) AS registros FROM dim_tempo
UNION ALL
SELECT 'dim_ativo',              COUNT(*) FROM dim_ativo
UNION ALL
SELECT 'dim_carteira',           COUNT(*) FROM dim_carteira
UNION ALL
SELECT 'fato_mercado',           COUNT(*) FROM fato_mercado;
```

Resultado esperado:

```
   tabela    | registros
-------------+-----------
 dim_tempo   |      2192   (dias de 2020-01-01 a 2025-12-31)
 dim_ativo   |         4
 dim_carteira|     10000
 fato_mercado|     ~6000   (dias úteis × 4 ativos)
```

```sql
-- 2. Verificar integridade referencial (deve retornar 0)
SELECT COUNT(*) AS fk_quebradas
FROM fato_mercado f
WHERE NOT EXISTS (SELECT 1 FROM dim_tempo    WHERE sk_tempo    = f.sk_tempo_pregao)
   OR NOT EXISTS (SELECT 1 FROM dim_ativo    WHERE sk_ativo    = f.sk_ativo)
   OR NOT EXISTS (SELECT 1 FROM dim_carteira WHERE sk_carteira = f.sk_carteira);
```

```sql
-- 3. Verificar role-playing: as duas FKs de tempo existem?
SELECT
    COUNT(DISTINCT sk_tempo_pregao) AS datas_pregao_distintas,
    COUNT(DISTINCT sk_tempo_coleta) AS datas_coleta_distintas
FROM fato_mercado;
```

```sql
-- 4. Verificar cobertura de ativos
SELECT a.ticker, COUNT(*) AS registros
FROM fato_mercado f
JOIN dim_ativo a ON f.sk_ativo = a.sk_ativo
GROUP BY a.ticker
ORDER BY a.ticker;
```

---

## 9. Referência rápida de comandos

### Conexão e navegação no psql

```bash
# Conectar ao banco
psql -U postgres -d cryptoportfolio

# Listar tabelas
\dt

# Descrever estrutura de uma tabela
\d nome_da_tabela

# Listar views
\dv

# Sair do psql
\q
```

### Execução de scripts

```bash
# Executar script SQL
psql -U postgres -d cryptoportfolio -f sql/nome_do_arquivo.sql

# Executar com saída verbosa (ver cada comando executado)
psql -U postgres -d cryptoportfolio -e -f sql/schema.sql

# Executar ETL Python
python sql/etl_dw.py
```

### Reset completo (recomeçar do zero)

```bash
psql -U postgres -c "DROP DATABASE IF EXISTS cryptoportfolio;"
psql -U postgres -c "CREATE DATABASE cryptoportfolio ENCODING 'UTF8';"
psql -U postgres -d cryptoportfolio -f sql/schema.sql
python sql/etl_dw.py
psql -U postgres -d cryptoportfolio -f sql/views.sql
```

> ⚠️ O comando `DROP DATABASE` apaga **todos os dados** permanentemente. Use apenas para resetar o ambiente de desenvolvimento.

---

*Documento gerado para o Projeto Final de Desenvolvimento para Ciência de Dados II — CEUB 2026/1*
