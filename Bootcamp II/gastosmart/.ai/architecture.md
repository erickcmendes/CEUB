# Arquitetura

> Versão detalhada de referência. Para o resumo executivo, ver [`ai.md`](ai.md). Para decisões justificadas, ver [`docs/ARD.md`](docs/ARD.md).

---

## Visão geral

GastoSmart é uma **aplicação CLI de camadas finas**. A entrada é interativa via terminal; a saída é texto formatado; a persistência é em PostgreSQL hospedado no Supabase.

A arquitetura segue o padrão clássico **Presentation → Service → Repository**:

```
┌────────────────────┐
│   CLI (app.py)     │   menu, prompts, prints
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Serviços           │   regras de negócio, validações,
│ (services.py)      │   cálculo de resumo, formatação
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Repositório        │   CRUD na tabela `gastos`
│ (repository.py)    │   ÚNICA camada que importa supabase-py
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Supabase (Postgres)│   tabela `gastos` + RLS aberto p/ anon
└────────────────────┘
```

Integração externa opcional ao **OpenWeather** fica isolada em `src/weather.py` (a partir do PR-2). A CLI consulta o serviço de clima somente no resumo, e somente quando `OPENWEATHER_API_KEY` está setada.

---

## Serviços e hospedagem

| Camada | Onde roda | Responsabilidade |
|---|---|---|
| CLI | Localmente / container Docker / shell do Render | Interação com o usuário |
| Lógica de negócio | Mesmo processo Python da CLI | Validações, agregações, cálculo de resumo |
| Banco | Supabase (`https://jqetggonptxjqjpapjps.supabase.co`) | Persistência relacional |
| CI | GitHub Actions | `ruff` + `pytest` em PRs e push para `main` |
| Deploy | Render (https://gastosmart-3nje.onrender.com) | Hosting da aplicação |
| Integração clima (opcional) | OpenWeather API | Resumo enriquecido com clima da cidade |

---

## Estrutura do repositório (alvo, após todos os PRs da entrega final)

```
gastosmart/
├── .ai/                       ← contexto para IA (este diretório)
│   ├── ai.md                  ← entry point
│   ├── architecture.md        ← este arquivo
│   ├── coding_conventions.md
│   ├── ui_guidelines.md
│   ├── config/
│   │   └── system.md          ← papel da IA + regras duras
│   ├── docs/
│   │   ├── ARD.md             ← decisões de arquitetura
│   │   ├── SRS.md             ← requisitos
│   │   ├── design-doc.md      ← design da CLI
│   │   ├── glossario-negocio.md
│   │   ├── glossario-tecnico.md
│   │   └── pr-review-checklist.md
│   └── workflows/
│       ├── github-workflow.md
│       └── task-queue.md
├── .github/
│   ├── workflows/ci.yml       ← pipeline ruff + pytest
│   └── pull_request_template.md
├── data/                      ← legado JSON (descontinuado pós-PR-2)
│   └── .gitkeep
├── docs/                      ← documentação para humanos (não duplicar .ai/)
│   ├── ARCHITECTURE.md        ← versão para humanos
│   ├── CONTRIBUTING.md
│   ├── DEVELOPMENT.md
│   ├── PLANO_ENTREGA_FINAL.md
│   ├── ISSUES_GITHUB.md
│   ├── PASSO_A_PASSO_PR01.md
│   ├── ISSUE_ERICK_PR01.md
│   └── supabase/
│       ├── schema.sql
│       └── CONFIGURACAO.md
├── src/
│   ├── app.py                 ← entrada da CLI
│   ├── config.py              ← env + Supabase client
│   ├── repository.py          ← CRUD em `gastos`
│   ├── services.py            ← regras de negócio (PR-2)
│   └── weather.py             ← OpenWeather isolado (PR-2)
├── tests/
│   ├── test_app.py            ← smoke/legacy
│   ├── test_repository.py     ← mocks do supabase client
│   ├── test_services.py       ← mocks do repository (PR-2)
│   └── test_integration_supabase.py  ← integração opcional (PR-3)
├── .env.example
├── .gitignore
├── .dockerignore
├── CONTRIBUTING.md
├── Dockerfile
├── README.md
├── pyproject.toml
└── requirements.txt
```

---

## Modelo de dados

### Tabela `gastos` (Supabase / Postgres)

```sql
create table public.gastos (
    id          bigserial primary key,
    descricao   text         not null check (length(trim(descricao)) > 0),
    valor       numeric(10,2) not null check (valor > 0),
    categoria   text         not null check (categoria in (
        'Alimentação','Transporte','Saúde','Lazer','Educação','Moradia','Outros'
    )),
    data        date         not null default current_date,
    criado_em   timestamptz  not null default now()
);

create index idx_gastos_categoria on public.gastos (categoria);
create index idx_gastos_data      on public.gastos (data desc);
```

### Políticas RLS no MVP

```sql
alter table public.gastos enable row level security;

create policy "anon pode ler gastos"      on public.gastos for select to anon using (true);
create policy "anon pode inserir gastos"  on public.gastos for insert to anon with check (true);
create policy "anon pode atualizar gastos" on public.gastos for update to anon using (true) with check (true);
create policy "anon pode remover gastos"  on public.gastos for delete to anon using (true);
```

**Justificativa:** sem autenticação de usuário no MVP, qualquer cliente com a `publishable key` pode operar. A migração para política por `user_id` é registrada como caminho futuro em `docs/ARD.md` (seção AD-10).

---

## Fluxo de chamadas — exemplos

### Adicionar gasto

```
app.tela_adicionar()
  └─> coleta input do usuário (descricao, valor, categoria)
  └─> services.adicionar_gasto(descricao, valor, categoria)
        └─> valida (descricao não vazia, valor > 0, categoria ∈ CATEGORIAS)
        └─> repository.inserir({descricao, valor, categoria, data})
              └─> client.table("gastos").insert(...).execute()
              └─> retorna registro com id gerado
        └─> retorna registro completo
  └─> imprime confirmação com id
```

### Resumo com clima

```
app.tela_resumo()
  └─> services.resumo_gastos()
        └─> repository.listar() ─> [{...}, {...}]
        └─> agrega total e total_por_categoria
        └─> retorna dict
  └─> imprime resumo
  └─> se OPENWEATHER_API_KEY: weather.buscar_clima(cidade, key)
        └─> imprime clima ou aviso de indisponibilidade
```

---

## Variáveis de ambiente

| Variável | Onde é usada | Obrigatória? | Padrão |
|---|---|---|---|
| `SUPABASE_URL` | `src/config.py` | Sim (a partir do PR-1) | — |
| `SUPABASE_KEY` | `src/config.py` | Sim (a partir do PR-1) | — |
| `OPENWEATHER_API_KEY` | `src/weather.py` (ou `src/app.py`) | Não | `""` |
| `OPENWEATHER_CIDADE` | idem | Não | `Brasilia` |
| `GASTOSMART_DATA_FILE` | legado de `src/app.py` | Não (descontinuada após PR-2) | `data/gastos.json` |

**Todas** as variáveis devem ser declaradas em `.env.example` com placeholder. Veja a Regra Dura #3 em `config/system.md`.

---

## Pipeline CI (GitHub Actions)

Arquivo: `.github/workflows/ci.yml`.

Job único `quality`:

1. `actions/checkout@v4`
2. `actions/setup-python@v5` com Python 3.11
3. `pip install -r requirements.txt`
4. `ruff check src/ tests/`
5. `pytest tests/ -v`

A partir do PR-3, um segundo job opcional `integration` roda os testes em `tests/test_integration_supabase.py` apenas em pushes para `main` usando `secrets.SUPABASE_URL` e `secrets.SUPABASE_KEY`. PRs vindos de forks ficam de fora desse job.

---

## Deploy

- **Plataforma:** Render
- **Tipo:** Web Service rodando o `Dockerfile`
- **URL:** https://gastosmart-3nje.onrender.com
- **Trigger:** auto-deploy a cada push em `main`
- **Variáveis de ambiente no painel do Render:**
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `OPENWEATHER_API_KEY` (opcional)
  - `OPENWEATHER_CIDADE` (opcional)

---

## Pontos de extensão futuros (fora do escopo do bootcamp)

| Extensão | Onde adicionar | Observações |
|---|---|---|
| Autenticação por usuário | Camada nova `src/auth.py` + tabela `users` no Supabase + RLS por `auth.uid()` | Substitui o RLS aberto para `anon` |
| API REST (FastAPI) | Pacote novo `api/` | A CLI continua usando o `repository` direto; a API expõe o mesmo `services` |
| Frontend web | Pacote novo `web/` | Lê Supabase diretamente via cliente JS (mesma estratégia do LegisTracker) |
| Categorias custom por usuário | Tabela nova `categorias` no Supabase | Substitui a lista hardcoded em `src/services.py` |
| Importação de extrato bancário (OFX/CSV) | `src/importers/` | Camada de transformação isolada |

---

## Diagrama de dependências entre módulos

```
config.py    ──────────────────┐
   ▲                            │
   │                            ▼
repository.py ◀─── services.py ─── app.py
                       ▲           ▲
                       │           │
                  weather.py ──────┘
```

Regra de dependência: setas só podem apontar para baixo ou para a esquerda. **Nada importa `app`.** **Nada além de `repository` importa `supabase`.** Veja Regra Dura #6.
