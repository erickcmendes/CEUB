# 🎬 Projeto IMDB Movies Dashboard

Dashboard analítico desenvolvido em **Power BI** como exercício prático da disciplina de **Business Intelligence II**, com foco em todo o fluxo de construção de uma solução de BI: desde o tratamento dos dados no **Power Query** até a modelagem, criação de medidas em **DAX** e desenvolvimento do dashboard final.

O projeto utiliza um dataset de filmes do IMDb para responder perguntas de negócio relacionadas a desempenho financeiro, avaliações críticas e padrões da indústria cinematográfica.

---

## 📌 Objetivo

Aplicar na prática conceitos de:

- ETL com Power Query
- Tratamento e padronização de dados
- Modelagem analítica
- Criação de colunas e medidas DAX
- Desenvolvimento de dashboards interativos
- Versionamento com Git/GitHub

---

## 🛠️ Tecnologias Utilizadas

- **Power BI Desktop**
- **Power Query (M)**
- **DAX**
- **Git**
- **GitHub**

---

## 🔄 Processo de Tratamento de Dados (ETL)

Durante o desenvolvimento, foram realizadas as seguintes transformações:

### Limpeza e organização
- Remoção de colunas irrelevantes
- Exclusão de colunas com alta taxa de valores nulos
- Remoção de registros duplicados
- Promoção e tradução de cabeçalhos

### Padronização
- Conversão correta dos tipos de dados
- Padronização de títulos em caixa alta
- Ajuste da coluna de gêneros para manter apenas o gênero principal

### Qualidade dos dados
- Remoção de registros com nota IMDb ausente
- Correção de falsos nulos
- Tratamento de valores ausentes com substituições condicionais

### Transformações analíticas
- Conversão da duração textual para minutos
- Classificação automática de filmes por duração
- Criação de colunas derivadas com DAX

---

## ❓ Perguntas de Negócio

O dashboard foi desenvolvido para responder às seguintes questões:

### 1. Filmes com maiores notas do IMDb geram maior retorno financeiro?

Busca identificar possível correlação entre avaliação crítica e desempenho comercial.

### 2. Quais gêneros apresentam maior receita bruta global?

Permite analisar quais segmentos da indústria cinematográfica possuem maior potencial de faturamento.

### 3. A indústria cinematográfica, no conjunto do dataset, operou com lucro ou prejuízo?

Análise consolidada do resultado financeiro total.

---

## 📊 Métricas Desenvolvidas

Foram criadas medidas DAX para análise estratégica:

- **Quantidade Total de Filmes**
- **Média de Nota IMDb (filmes lançados a partir de 2000)**
- **Resultado Financeiro Total**
- **Status de Crítica**
- **Tratamento de Local de Filmagem**

---

## 📈 Principais Visualizações

O dashboard inclui:

- Receita bruta por gênero
- Distribuição das notas IMDb
- Indicadores financeiros
- Comparativos entre orçamento e faturamento
- Segmentação temporal
- KPIs analíticos

---

## 👨‍💻 Autor

**Erick Mendes**

Projeto acadêmico desenvolvido para a disciplina de **Business Intelligence II**.