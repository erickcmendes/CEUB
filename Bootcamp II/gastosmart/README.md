# 💸 GastoSmart

![CI](https://github.com/erickcmendes/gastosmart/actions/workflows/ci.yml/badge.svg)

Versão: **1.1.0**

🚀 **Deploy:** [https://gastosmart.onrender.com](https://gastosmart-3nje.onrender.com)

---

## Descrição do Problema Real

Muitas pessoas têm dificuldade em controlar seus gastos mensais, o que leva ao endividamento e à falta de planejamento financeiro. A ausência de uma ferramenta simples e acessível faz com que despesas passem despercebidas no dia a dia.

## Proposta da Solução

O **GastoSmart** é uma aplicação de linha de comando (CLI) que permite registrar, listar, remover e resumir gastos pessoais de forma simples e organizada. Os dados são salvos localmente em JSON. A partir da versão 1.1.0, o resumo também exibe o **clima atual da sua cidade** via API OpenWeather.

## Público-alvo

Pessoas que desejam controlar seus gastos pessoais sem depender de aplicativos complexos ou conexão com a internet.

## Funcionalidades

- ✅ Adicionar gasto com descrição, valor, categoria e data
- ✅ Listar todos os gastos cadastrados
- ✅ Remover gasto pelo ID
- ✅ Ver resumo com total geral e total por categoria
- ✅ Exibir clima atual da cidade no resumo (via OpenWeather)
- ✅ Armazenamento local em JSON

## Tecnologias Utilizadas

- Python 3.11
- pytest (testes automatizados)
- ruff (linting / análise estática)
- GitHub Actions (CI)
- Docker (containerização)
- Render.com (deploy)
- OpenWeather API (dados climáticos)

## Instalação

```bash
git clone https://github.com/erickcmendes/gastosmart.git
cd gastosmart
pip install -r requirements.txt
```

## Execução

```bash
python src/app.py
```

### Com integração de clima (opcional)

Crie uma conta gratuita em [openweathermap.org](https://openweathermap.org) e obtenha sua API Key. Depois configure as variáveis de ambiente:

```bash
# Linux/macOS
export OPENWEATHER_API_KEY="sua_chave_aqui"
export OPENWEATHER_CIDADE="Brasilia"

# Windows
set OPENWEATHER_API_KEY=sua_chave_aqui
set OPENWEATHER_CIDADE=Brasilia
```

### Executando via Docker

```bash
docker build -t gastosmart .
docker run -it \
  -e OPENWEATHER_API_KEY=sua_chave_aqui \
  -e OPENWEATHER_CIDADE=Brasilia \
  gastosmart
```

## Rodando os Testes

```bash
pytest tests/ -v
```

## Rodando o Lint

```bash
ruff check src/ tests/
```

## Versão Atual

`1.1.0` — definida em `pyproject.toml`

## Autor

Erick Cardoso Mendes — [github.com/erickcmendes](https://github.com/erickcmendes)

## Repositório

[https://github.com/erickcmendes/gastosmart](https://github.com/erickcmendes/gastosmart)
