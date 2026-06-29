# Guia de desenvolvimento

Guia rápido para configurar o ambiente local e manter um fluxo de trabalho saudável.

## Ambiente

- Python 3.11 ou superior
- Ambiente virtual local (`.venv`)
- Dependências em `requirements.txt`

Setup:

```bash
python -m venv .venv
```

Ativação:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate
```

Instalação das dependências:

```bash
python -m pip install -r requirements.txt
```

## Configuração local

Copie `.env.example` para `.env` na raiz e preencha as variáveis. O `python-dotenv` carrega `.env` automaticamente.

Variáveis:

- `SUPABASE_URL` — URL do projeto Supabase (obrigatória)
- `SUPABASE_PUB_KEY` — chave publishable/anon do Supabase (obrigatória)
- `OPENWEATHER_API_KEY` — chave opcional do OpenWeather
- `OPENWEATHER_CIDADE` — cidade usada no resumo do clima (padrão: `Brasilia`)

O arquivo `.env` **nunca** deve ser commitado.

## Comandos úteis

Rodar a aplicação web (Streamlit):

```bash
streamlit run src/app_web.py
```

Abre em `http://localhost:8501`.

Rodar a aplicação CLI:

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

Rodar via Docker:

```bash
docker build -t gastosmart .
docker run -it --rm -p 8501:8501 --env-file .env gastosmart
```

## Fluxo de branches

Use uma branch por tarefa:

```bash
git checkout -b feature/minha-tarefa
```

Prefixos:

- `feature/` para funcionalidades
- `fix/` para correções
- `docs/` para documentação
- `chore/` para manutenção

## Pull Requests

Cada PR deve:

- resolver uma tarefa clara;
- ter escopo pequeno;
- passar no CI (ruff + pytest verdes);
- ser revisado por outro integrante;
- incluir teste quando alterar comportamento.

## Antes de pedir review

```bash
python -m pytest tests/ -q
python -m ruff check src/ tests/
```

Confira também:

- nenhum `.env` foi commitado;
- nenhum arquivo `data/*.json` foi commitado;
- a documentação foi atualizada quando necessário (incluindo `.ai/` para mudanças arquiteturais).
