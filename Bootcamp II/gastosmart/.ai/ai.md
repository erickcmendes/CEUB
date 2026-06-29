# GastoSmart — Índice de Contexto para IA

Este arquivo é o **ponto único de entrada** para qualquer assistente de IA trabalhando neste repositório. Leia-o primeiro e depois navegue para o arquivo específico listado para o tópico que você precisa.

---

## Visão geral

**Sistema:** GastoSmart — aplicação Python para registrar, listar, remover e resumir gastos pessoais. Duas interfaces coexistem:

- **CLI interativa** (`src/app.py`) — uso local via terminal.
- **Web app Streamlit** (`src/app_web.py`) — uso via navegador, é o que está implantado no Render.

Ambas compartilham a mesma camada de serviços (`src/services.py`) e repositório (`src/repository.py`), com persistência em PostgreSQL via Supabase e integração opcional ao OpenWeather.

**Stack:** Python 3.11+ · Streamlit · Supabase (PostgreSQL) · `supabase-py` · `python-dotenv` · `pytest` · `ruff` · GitHub Actions · Docker · Render · OpenWeather (opcional)

**Repositório (Source of Truth):** https://github.com/erickcmendes/gastosmart

**Deploy:** https://gastosmart-3nje.onrender.com

**Contexto acadêmico:** entrega final da disciplina **Bootcamp II — Turma C 0226, Campus Virtual (CEUB)**. Equipe de 4 integrantes (ver "Equipe" no fim).

---

## Mapa de navegação — para cada tópico, leia o arquivo certo

| Tópico | Arquivo local |
|---|---|
| **Papel da IA, comportamento e Regras Duras** | [config/system.md](config/system.md) |
| **Arquitetura do sistema**, componentes, fluxo de dados, modelo de dados | [architecture.md](architecture.md) |
| **Decisões de arquitetura** (ADRs com motivação e consequências) | [docs/ARD.md](docs/ARD.md) |
| **Requisitos funcionais e não-funcionais** | [docs/SRS.md](docs/SRS.md) |
| **Design da CLI** (menus, telas, mensagens, iconografia) | [docs/design-doc.md](docs/design-doc.md) |
| **Padrões visuais da CLI** (emojis, separadores, formatação) | [ui_guidelines.md](ui_guidelines.md) |
| **Padrões de código** (Python, Git, segurança, testes) | [coding_conventions.md](coding_conventions.md) |
| **Glossário de negócio** (gasto, categoria, resumo…) | [docs/glossario-negocio.md](docs/glossario-negocio.md) |
| **Glossário técnico** (Supabase, Streamlit, RLS, dotenv, CRUD, mocks…) | [docs/glossario-tecnico.md](docs/glossario-tecnico.md) |
| **Checklist de Code Review** (passos do revisor antes de aprovar) | [docs/pr-review-checklist.md](docs/pr-review-checklist.md) |
| **Fluxo do GitHub** (issues, PRs, branches, source of truth viva) | [workflows/github-workflow.md](workflows/github-workflow.md) |
| **Fila de tarefas** (o que trabalhar a seguir) | [workflows/task-queue.md](workflows/task-queue.md) |

---

## Source of Truth — links vivos do projeto

Esta seção é **mantida pela IA automaticamente**. Sempre que uma issue ou PR novo for criado/citado, a IA adiciona o link aqui sem pedir permissão. Veja `config/system.md` → "MANDATO DE AUTO-ATUALIZAÇÃO".

### Repositório raiz

- [erickcmendes/gastosmart](https://github.com/erickcmendes/gastosmart) — branch principal: `main`

### PRs mergeados (entrega final)

- [#3 — feat: configuração do Supabase e camada de repositório](https://github.com/erickcmendes/gastosmart/pull/3) — @erickcmendes — mergeado
- [#9 — PR-02: migrar serviços para Supabase](https://github.com/erickcmendes/gastosmart/pull/9) — @lucasmalinski — mergeado
- [#10 — testes extras de services + ruff --fix](https://github.com/erickcmendes/gastosmart/pull/10) — @joaovicente04 — mergeado
- [#11 — deploy Render, arquitetura 3 camadas e PDF de entrega](https://github.com/erickcmendes/gastosmart/pull/11) — @Caua-Godoy — mergeado (Closes #6, #7)
- [#13 — feat: Streamlit web app](https://github.com/erickcmendes/gastosmart/pull/13) — @erickcmendes (impl. com @lucasmalinski) — mergeado

### Issues conhecidas

- [#4 — Configurar Supabase e criar camada de repositório](https://github.com/erickcmendes/gastosmart/issues/4) — fechada via PR #3

> **Para a IA:** quando você abrir, mergear, fechar ou apenas mencionar uma issue/PR nova nesta conversa, **adicione a entrada nesta seção e em `workflows/github-workflow.md`**, e atualize o status das já listadas.

---

## Decisões críticas (resumo ultra-curto)

- **Persistência:** Supabase Postgres é o destino oficial. O JSON local em `data/gastos.json` é legado descontinuado.
- **Duas interfaces, mesmo core:** CLI (`src/app.py`) e Web (`src/app_web.py` via Streamlit) compartilham `services` e `repository`.
- **Streamlit foi a solução adotada para destravar o deploy do Render** (Docker rodando `streamlit run src/app_web.py`). Ver AD-15 em [`docs/ARD.md`](docs/ARD.md).
- **Camada de repositório obrigatória:** `src/repository.py` é a única camada que importa `supabase`. Demais camadas usam funções do repository.
- **Imports relativos com fallback:** todos os módulos de `src/` usam `try: from . import X / except ImportError: import X` para suportar tanto execução como pacote quanto como script avulso (testes). Convenção registrada em `coding_conventions.md`.
- **Sem autenticação por usuário no MVP:** RLS aberto para `anon` na tabela `gastos`. Multiusuário fica fora de escopo.
- **OpenWeather é opcional:** sem `OPENWEATHER_API_KEY`, o resumo/sidebar seguem funcionando sem clima.
- **Variável da chave Supabase:** **`SUPABASE_PUB_KEY`** (decisão consolidada). `SUPABASE_KEY` ainda é aceita pelo `config.py` por compatibilidade, mas o `.env.example`, README e deploy usam `SUPABASE_PUB_KEY`. Ver AD-16.
- **CI obrigatório:** nenhum PR é mergeado com `ruff` ou `pytest` vermelhos.
- **Cada integrante abriu ≥1 PR revisado e mergeado** — exigência da disciplina **cumprida**.

---

## Regras Duras (resumo — a versão completa está em `config/system.md`)

1. Nunca commitar `.env`. Só `.env.example`.
2. Nunca hardcodar credenciais.
3. Nunca commitar sem rodar `ruff` + `pytest` localmente.
4. Nunca aconselhar PR sem ter testado antes.
5. Nunca deixar prints de debug em `src/app.py` ou `src/app_web.py` finais.
6. Nunca chamar `supabase` fora de `src/repository.py`.
7. Nunca `git push --force` em `main`.
8. Nunca mergear PR com CI vermelho.
9. Nunca expor a chave Supabase em logs, mensagens ou prints.
10. `architecture.md`, `docs/ARD.md` e `docs/SRS.md` são fontes de verdade — atualize quando algo mudar.

---

## Entrega final — status

**Concluída.** Todos os requisitos foram atendidos:

- 6 PRs mergeados na `main` (cada integrante com ao menos 1 PR no nome).
- Deploy em https://gastosmart-3nje.onrender.com servindo o Streamlit conectado ao Supabase.
- CI verde no último commit da `main`.
- PDF de entrega submetido na SalaOnline.

---

## Equipe

| Integrante | Matrícula | GitHub | PR(s) entregues |
|---|---|---|---|
| Cauã de Godoy Araujo | 22507326 | [@Caua-Godoy](https://github.com/Caua-Godoy) | PR-04 (#11) |
| Erick Cardoso Mendes | 22509170 | [@erickcmendes](https://github.com/erickcmendes) | PR-01 (#3), PR-Streamlit (#13) |
| Lucas Patriota Malinski da Silva Pinto | 22452112 | [@lucasmalinski](https://github.com/lucasmalinski) | PR-02 (#9) + impl. Streamlit em #13 |
| João Vicente Burin Souza | 22501001 | [@joaovicente04](https://github.com/joaovicente04) | PR-03 (#10) |

---

## Última revisão deste índice

A IA deve atualizar este rodapé sempre que tocar este arquivo.

- **Última atualização:** 2026-06-11 (sincronização pós-PRs #9, #10, #11, #13 e padronização `SUPABASE_PUB_KEY`)
- **Por:** IA (Cowork / Claude) — sob orientação de @erickcmendes, atendendo pedido de @lucasmalinski para atualizar contexto integral
