# Guia de desenvolvimento

Este guia ajuda a equipe a configurar o projeto e manter um fluxo colaborativo saudável.

## Ambiente

Recomendação:

- Python 3.11 ou superior.
- Ambiente virtual local.
- Dependências instaladas via `requirements.txt`.

Setup:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

Ativação no PowerShell:

```bash
.\.venv\Scripts\Activate.ps1
```

## Configuração local

Copie `.env.example` como referência e configure as variáveis no terminal quando precisar.

O arquivo `.env` não deve ser commitado.

Variáveis principais:

- `OPENWEATHER_API_KEY`
- `OPENWEATHER_CIDADE`
- `GASTOSMART_DATA_FILE`

## Comandos úteis

Rodar o app:

```bash
python src/app.py
```

Rodar testes:

```bash
python -m pytest tests/ -q
```

Rodar lint:

```bash
python -m ruff check src/ tests/
```

Rodar com Docker:

```bash
docker build -t gastosmart .
docker run -it --rm gastosmart
```

## Fluxo de branches

Use uma branch por tarefa:

```bash
git checkout -b feature/minha-tarefa
```

Sugestões de prefixo:

- `feature/` para funcionalidades;
- `fix/` para correções;
- `docs/` para documentação;
- `chore/` para manutenção.

## Pull Requests

Cada PR deve:

- resolver uma tarefa clara;
- ter escopo pequeno;
- passar no CI;
- ser revisado por outro integrante;
- incluir teste quando alterar comportamento.

Para a entrega final, cada integrante precisa abrir pelo menos 1 PR relevante e ter esse PR revisado por outra pessoa.

## Antes de pedir review

Rode:

```bash
python -m pytest tests/ -q
python -m ruff check src/ tests/
```

Confira também:

- nenhum `.env` foi commitado;
- nenhum arquivo `data/*.json` foi commitado;
- a documentação foi atualizada quando necessário.

