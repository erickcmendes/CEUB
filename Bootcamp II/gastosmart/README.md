# 💸 GastoSmart

![CI](https://github.com/erickcmendes/gastosmart/actions/workflows/ci.yml/badge.svg)

Versão: **1.0.0**

## Descrição do Problema Real

Muitas pessoas têm dificuldade em controlar seus gastos mensais, o que leva ao endividamento e à falta de planejamento financeiro. A ausência de uma ferramenta simples e acessível faz com que despesas passem despercebidas no dia a dia.

## Proposta da Solução

O **GastoSmart** é uma aplicação de linha de comando (CLI) que permite registrar, listar, remover e resumir gastos pessoais de forma simples, rápida e organizada. Os dados são salvos localmente em um arquivo JSON.

## Público-alvo

Pessoas que desejam controlar seus gastos pessoais sem depender de aplicativos complexos ou conexão com a internet.

## Funcionalidades

- ✅ Adicionar gasto com descrição, valor, categoria e data
- ✅ Listar todos os gastos cadastrados
- ✅ Remover gasto pelo ID
- ✅ Ver resumo com total geral e total por categoria
- ✅ Armazenamento local em JSON

## Tecnologias Utilizadas

- Python 3.11
- pytest (testes automatizados)
- ruff (linting / análise estática)
- GitHub Actions (CI)

## Instalação

```bash
# Clone o repositório
git clone https://github.com/SEU_USUARIO/gastosmart.git
cd gastosmart

# Instale as dependências
pip install -r requirements.txt
```

## Execução

```bash
python src/app.py
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

`1.0.0` — definida em `pyproject.toml`

## Autor

Seu Nome — [github.com/SEU_USUARIO](https://github.com/SEU_USUARIO)

## Repositório

[https://github.com/SEU_USUARIO/gastosmart](https://github.com/SEU_USUARIO/gastosmart)
