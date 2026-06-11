# GastoSmart

![CI](https://github.com/erickcmendes/gastosmart/actions/workflows/ci.yml/badge.svg)

Versão: **1.1.0**

Deploy: [https://gastosmart-3nje.onrender.com](https://gastosmart-3nje.onrender.com)

## Visão geral

O **GastoSmart** é uma aplicação de linha de comando para registrar, listar, remover e resumir gastos pessoais. A persistência oficial já está migrada para o **Supabase** e o resumo pode exibir o clima atual da cidade usando a API OpenWeather.

Este repositório é a base de trabalho da entrega final de Bootcamp II e já conta com a separação entre CLI, serviços e repositório para facilitar testes e PRs paralelos.

## Problema

Muitas pessoas têm dificuldade em controlar gastos mensais, o que pode levar ao endividamento e à falta de planejamento financeiro. Uma ferramenta simples e acessível ajuda a tornar despesas do dia a dia mais visíveis.

## Funcionalidades atuais

- Adicionar gasto com descrição, valor, categoria e data.
- Listar gastos cadastrados.
- Remover gasto pelo ID.
- Ver resumo com total geral e total por categoria.
- Exibir clima atual da cidade no resumo, quando a OpenWeather API estiver configurada.
- Persistir gastos no Supabase.

## Tecnologias

- Python 3.11+
- pytest
- ruff
- GitHub Actions
- Docker
- Supabase
- OpenWeather API

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

Use o arquivo `.env.example` como referência. O projeto carrega `.env` automaticamente quando `python-dotenv` estiver disponível.

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
- `SUPABASE_PUB_KEY`: chave `anon`/`publishable` do projeto Supabase.
- `OPENWEATHER_API_KEY`: chave opcional para integração com OpenWeather.
- `OPENWEATHER_CIDADE`: cidade usada no resumo de clima. Padrão: `Brasilia`.
- `GASTOSMART_DATA_FILE`: legado da etapa anterior; mantido apenas por compatibilidade.

## Execução

```bash
python src/app.py
```

Se preferir trabalhar com o ambiente da virtualenv do projeto:

```bash
.\.venv\Scripts\python.exe src/app.py
```

## Testes e lint

```bash
python -m pytest tests/ -q
python -m ruff check src/ tests/
```

## Docker

```bash
docker build -t gastosmart .
docker run -it --rm gastosmart
```

Com variáveis de ambiente:

```bash
docker run -it --rm \
  -e OPENWEATHER_API_KEY=sua_chave_aqui \
  -e OPENWEATHER_CIDADE=Brasilia \
  gastosmart
```

## Documentação do projeto

- [Guia de contribuição](CONTRIBUTING.md)
- [Arquitetura atual](docs/ARCHITECTURE.md)
- [Guia de desenvolvimento](docs/DEVELOPMENT.md)
- [Preparação para a entrega final](docs/PREPARACAO_ENTREGA_FINAL.md)

## Entrega final

Para a entrega final, a equipe deverá manter testes, CI e deploy funcionando, trabalhar via Pull Requests revisados e migrar a persistência para um banco de dados em nuvem. Esses requisitos estão documentados em [docs/PREPARACAO_ENTREGA_FINAL.md](docs/PREPARACAO_ENTREGA_FINAL.md).

## Autores

Erick Cardoso Mendes - [github.com/erickcmendes](https://github.com/erickcmendes)

Lucas Patriota Malinsk da Silva Pinto - [github.com/lucasmalinsk](https://github.com/lucasmalinski)

João Vicente Burin Souza - [github.com/joaovicente04](https://github.com/joaovicente04)

Cauã de Godoy Araujo - [github.com/Caua-Godoy](https://github.com/Caua-Godoy)
