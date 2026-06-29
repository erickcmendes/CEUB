# GastoSmart

![CI](https://github.com/erickcmendes/gastosmart/actions/workflows/ci.yml/badge.svg)

Versão: **1.2**

Deploy: [https://gastosmart-3nje.onrender.com](https://gastosmart-3nje.onrender.com)

## Visão geral

O **GastoSmart** é uma aplicação Python para registrar, listar, remover e resumir gastos pessoais. O projeto oferece duas interfaces sobre o mesmo núcleo de regras de negócio:

- **CLI interativa** (`src/app.py`) para uso local via terminal.
- **Aplicação web em Streamlit** (`src/app_web.py`) — é o que está publicado no Render.

A persistência oficial é em **Supabase (PostgreSQL)**. O resumo financeiro pode exibir o clima atual da cidade usando a API OpenWeather quando configurada.

Este repositório é o resultado da entrega final da disciplina **Bootcamp II - CEUB**.

## Problema

Muitas pessoas têm dificuldade em controlar gastos mensais, o que pode levar ao endividamento e à falta de planejamento financeiro. Uma ferramenta simples e acessível ajuda a tornar despesas do dia a dia mais visíveis.

## Funcionalidades

- Adicionar gasto com descrição, valor, categoria e data.
- Listar gastos cadastrados.
- Remover gasto pelo ID.
- Ver resumo com total geral e total por categoria.
- Exibir clima atual da cidade no resumo, quando a OpenWeather API estiver configurada.
- Persistir gastos no Supabase (PostgreSQL em nuvem).
- Acessar as funcionalidades via CLI ou via aplicação web.

## Tecnologias

- Python 3.11+
- Streamlit (interface web)
- Supabase (PostgreSQL)
- supabase-py
- python-dotenv
- pytest
- ruff
- GitHub Actions
- Docker
- Render (hospedagem)
- OpenWeather API (opcional)

## Setup local

```bash
git clone https://github.com/erickcmendes/gastosmart.git
cd gastosmart
python -m venv .venv
```

Ative o ambiente virtual:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate
```

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

## Variáveis de ambiente

Use o arquivo `.env.example` como referência. O projeto carrega `.env` automaticamente via `python-dotenv`.

```bash
# Windows PowerShell
$env:SUPABASE_URL="sua_url_aqui"
$env:SUPABASE_PUB_KEY="sua_chave_aqui"
$env:OPENWEATHER_API_KEY="sua_chave_aqui"
$env:OPENWEATHER_CIDADE="Brasilia"

# Linux/macOS
export SUPABASE_URL="sua_url_aqui"
export SUPABASE_PUB_KEY="sua_chave_aqui"
export OPENWEATHER_API_KEY="sua_chave_aqui"
export OPENWEATHER_CIDADE="Brasilia"
```

Variáveis disponíveis:

- `SUPABASE_URL`: URL do projeto Supabase.
- `SUPABASE_PUB_KEY`: chave anon/publishable do projeto Supabase.
- `OPENWEATHER_API_KEY`: chave opcional para integração com OpenWeather.
- `OPENWEATHER_CIDADE`: cidade usada no resumo de clima. Padrão: `Brasilia`.

## Execução

**Interface web (Streamlit):**

```bash
streamlit run src/app_web.py
```

Abre em `http://localhost:8501`.

**Interface CLI:**

```bash
python src/app.py
```

## Testes e lint

```bash
python -m pytest tests/ -q
python -m ruff check src/ tests/
```

## Docker

```bash
docker build -t gastosmart .
docker run -it --rm -p 8501:8501 --env-file .env gastosmart
```

A imagem expõe a porta 8501 (Streamlit). O serviço fica acessível em `http://localhost:8501` após o `docker run`.

## Documentação do projeto

- [Guia de contribuição](CONTRIBUTING.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Guia de desenvolvimento](docs/DEVELOPMENT.md)
- [Deploy no Render](docs/DEPLOY.md)
- [Resumo da entrega final](docs/PREPARACAO_ENTREGA_FINAL.md)
- [Contexto para IA copiloto (`.ai/`)](.ai/ai.md)

## Autores

| Nome | Matrícula | GitHub |
|---|---|---|
| Cauã de Godoy Araujo | 22507326 | [@Caua-Godoy](https://github.com/Caua-Godoy) |
| Erick Cardoso Mendes | 22509170 | [@erickcmendes](https://github.com/erickcmendes) |
| Lucas Patriota Malinski da Silva Pinto | 22452112 | [@lucasmalinski](https://github.com/lucasmalinski) |
| João Vicente Burin Souza | 22501001 | [@joaovicente04](https://github.com/joaovicente04) |
