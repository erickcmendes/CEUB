# Arquitetura

> Versão detalhada de referência. Para o resumo executivo, ver [`ai.md`](ai.md). Para decisões justificadas, ver [`docs/ARD.md`](docs/ARD.md).

---

## Visão geral

GastoSmart é uma **aplicação Python de camadas finas**, com **duas interfaces** intercambiáveis sobre o mesmo core de regras de negócio e persistência:

- **CLI interativa** (`src/app.py`) — uso local.
- **Web app Streamlit** (`src/app_web.py`) — uso via navegador, é o que está implantado no Render.

A persistência é em PostgreSQL hospedado no Supabase. A arquitetura segue **Presentation → Service → Repository**:

```
┌─────────────────────┐   ┌───────────────────────┐
│  CLI (app.py)       │   │  Web (app_web.py)     │
│  menu, prompts,     │   │  abas Streamlit,      │
│  prints             │   │  forms, charts        │
└──────────┬──────────┘   └──────────┬────────────┘
           │                          │
           └────────────┬─────────────┘
                        ▼
            ┌────────────────────┐
            │ Serviços           │ regras de negócio, validações,
            │ (services.py)      │ resumo, OpenWeather opcional
            └─────────┬──────────┘
                      │
                      ▼
            ┌────────────────────┐
            │ Repositório        │ CRUD na tabela `gastos`
            │ (repository.py)    │ ÚNICA camada que importa supabase-py
            └─────────┬──────────┘
                      │
                      ▼
            ┌────────────────────┐
            │ Supabase (Postgres)│ tabela `gastos` + RLS aberto p/ anon
            └────────────────────┘
```

Integração externa opcional ao **OpenWeather** fica em `src/services.py`. A CLI consulta o serviço de clima no resumo; o Streamlit consulta no sidebar. Em ambos, só quando `OPENWEATHER_API_KEY` está setada.

---

## Serviços e hospedagem

| Camada | Onde roda | Responsabilidade |
|---|---|---|
| CLI | Localmente | Interação com o usuário via terminal |
| Web (Streamlit) | Container Docker no Render | Interface web pública |
| Lógica de negócio | Mesmo processo Python das interfaces | Validações, agregações, cálculo de resumo |
| Banco | Supabase (`https://jqetggonptxjqjpapjps.supabase.co`) | Persistência relacional |
| CI | GitHub Actions | `ruff` + `pytest` em PRs e push para `main` |
| Deploy | Render (https://gastosmart-3nje.onrender.com) | Hosting do Streamlit |
| Integração clima (opcional) | OpenWeather API | Resumo enriquecido com clima da cidade |

---

## Estrutura do repositório (estado atual após entrega final)

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
│   │   ├── design-doc.md      ← design da CLI (e do Streamlit)
│   │   ├── glossario-negocio.md
│   │   ├── glossario-tecnico.md
│   │   └── pr-review-checklist.md
│   └── workflows/
│       ├── github-workflow.md
│       └── task-queue.md
├── .github/
│   ├── workflows/ci.yml       ← pipeline ruff + pytest
│   └── pull_request_template.md
├── data/                      ← legado JSON (descontinuado)
│   └── .gitkeep
├── docs/                      ← documentação para humanos (não duplicar .ai/)
│   ├── PDF_ENTREGA.md         ← conteúdo do PDF da entrega (Cauã)
│   ├── PLANO_ENTREGA_FINAL.md
│   ├── ISSUES_GITHUB.md
│   ├── PASSO_A_PASSO_PR01.md
│   ├── ISSUE_ERICK_PR01.md
│   └── supabase/
│       ├── schema.sql
│       └── CONFIGURACAO.md
├── src/
│   ├── app.py                 ← entrada da CLI
│   ├── app_web.py             ← entrada da Web Streamlit (deploy Render)
│   ├── config.py              ← env + Supabase client
│   ├── repository.py          ← CRUD em `gastos`
│   └── services.py            ← regras de negócio + OpenWeather
├── tests/
│   ├── test_app.py            ← delegação app → services
│   ├── test_repository.py     ← mocks do supabase client
│   └── test_services.py       ← mocks do repository + OpenWeather
├── CHANGELOG
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

**Justificativa:** sem autenticação de usuário no MVP, qualquer cliente com a `publishable key` pode operar. A migração para política por `user_id` é registrada como caminho futuro em [`docs/ARD.md`](docs/ARD.md) (AD-10).

---

## Padrão de imports (convenção do projeto)

Todos os módulos dentro de `src/` que importam outros módulos da mesma pasta usam **import relativo com fallback para absoluto**:

```python
try:
    from . import services
except ImportError:
    import services
```

Justificativa: o pacote é executado de duas formas — como módulo (`python -m src.app`) e como script avulso (testes injetam `src/` no `sys.path`). O fallback cobre os dois cenários sem precisar configurar `conftest.py`. Convenção registrada em [`coding_conventions.md`](coding_conventions.md) e em AD novo se trocado no futuro.

---

## Fluxo de chamadas — exemplos

### Adicionar gasto (CLI)

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

### Adicionar gasto (Web)

```
app_web.tab_adicionar (Streamlit form submit)
  └─> services.adicionar_gasto(descricao, valor, categoria)
        └─> mesmo fluxo da CLI
  └─> st.success(...) + st.rerun()
```

### Resumo com clima (qualquer interface)

```
services.resumo_gastos()
  └─> repository.listar() ─> [{...}, {...}]
  └─> agrega total e por_categoria
  └─> retorna dict

Se OPENWEATHER_API_KEY setada:
  services.buscar_clima(cidade, key)
    └─> CLI imprime ou Streamlit mostra st.metric no sidebar
```

---

## Variáveis de ambiente

| Variável | Onde é usada | Obrigatória? | Padrão |
|---|---|---|---|
| `SUPABASE_URL` | `src/config.py` | Sim | — |
| `SUPABASE_PUB_KEY` | `src/config.py` (com fallback para `SUPABASE_KEY` legado) | Sim | — |
| `OPENWEATHER_API_KEY` | `src/services.py` (via `app.py` e `app_web.py`) | Não | `""` |
| `OPENWEATHER_CIDADE` | idem | Não | `Brasilia` |
| `GASTOSMART_DATA_FILE` | legado (não mais usado) | Não | `data/gastos.json` |

**Todas** as variáveis devem ser declaradas em `.env.example` com placeholder. Veja a Regra Dura #3 em [`config/system.md`](config/system.md). A decisão de renomear `SUPABASE_KEY` → `SUPABASE_PUB_KEY` está em AD-16.

---

## Pipeline CI (GitHub Actions)

Arquivo: `.github/workflows/ci.yml`.

Job único `quality`:

1. `actions/checkout@v4`
2. `actions/setup-python@v5` com Python 3.11
3. `pip install -r requirements.txt`
4. `ruff check src/ tests/ --fix`
5. `pytest tests/ -v`

> Observação: o `--fix` na etapa 4 modifica arquivos no checkout do runner, mas não commita. Isso é tolerável para fazer a CI passar quando há autofix trivial, mas mascara violações em PRs (o desenvolvedor não vê o erro). Decisão registrada como ponto a revisar em AD futuro se for incomodar.

---

## Deploy

- **Plataforma:** Render
- **Tipo:** Web Service rodando o `Dockerfile`
- **Comando do container:** `streamlit run src/app_web.py --server.port 8501 --server.address 0.0.0.0`
- **URL:** https://gastosmart-3nje.onrender.com
- **Trigger:** auto-deploy a cada push em `main`
- **Variáveis de ambiente no painel do Render:**
  - `SUPABASE_URL`
  - `SUPABASE_PUB_KEY`  ← renomeada de `SUPABASE_KEY` (AD-16). Conferir no painel.
  - `OPENWEATHER_API_KEY` (opcional)
  - `OPENWEATHER_CIDADE` (opcional)

---

## Pontos de extensão futuros (fora do escopo do bootcamp)

| Extensão | Onde adicionar | Observações |
|---|---|---|
| Autenticação por usuário | Camada nova `src/auth.py` + tabela `users` no Supabase + RLS por `auth.uid()` | Substitui o RLS aberto para `anon` |
| API REST (FastAPI) | Pacote novo `api/` | A CLI/Web continuam usando o `services` direto; a API expõe o mesmo |
| Edição de gasto | Adicionar `repository.atualizar` + tela na CLI e tab no Streamlit | Hoje só add/list/remove |
| Categorias custom por usuário | Tabela nova `categorias` no Supabase | Substitui a lista hardcoded em `src/services.py` |
| Importação de extrato bancário (OFX/CSV) | `src/importers/` | Camada de transformação isolada |

---

## Diagrama de dependências entre módulos

```
              config.py
                 ▲
                 │
            repository.py
                 ▲
                 │
             services.py
                 ▲
        ┌────────┴────────┐
        │                  │
     app.py            app_web.py
```

Regra de dependência: setas só podem apontar para baixo. **Nada importa `app` nem `app_web`.** **Nada além de `repository` importa `supabase`.** Veja Regra Dura #6.
