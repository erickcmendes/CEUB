# GastoSmart — Índice de Contexto para IA

Este arquivo é o **ponto único de entrada** para qualquer assistente de IA trabalhando neste repositório. Leia-o primeiro e depois navegue para o arquivo específico listado para o tópico que você precisa.

---

## Visão geral

**Sistema:** GastoSmart — aplicação CLI Python para registrar, listar, remover e resumir gastos pessoais, com integração opcional ao OpenWeather e persistência em PostgreSQL via Supabase.

**Stack:** Python 3.11+ · Supabase (PostgreSQL) · `supabase-py` · `python-dotenv` · `pytest` · `ruff` · GitHub Actions · Docker · Render · OpenWeather (opcional)

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
| **Glossário técnico** (Supabase, RLS, dotenv, CRUD, mocks…) | [docs/glossario-tecnico.md](docs/glossario-tecnico.md) |
| **Checklist de Code Review** (passos do revisor antes de aprovar) | [docs/pr-review-checklist.md](docs/pr-review-checklist.md) |
| **Fluxo do GitHub** (issues, PRs, branches, source of truth viva) | [workflows/github-workflow.md](workflows/github-workflow.md) |
| **Fila de tarefas** (o que trabalhar a seguir) | [workflows/task-queue.md](workflows/task-queue.md) |

---

## Source of Truth — links vivos do projeto

Esta seção é **mantida pela IA automaticamente**. Sempre que uma issue ou PR novo for criado/citado, a IA adiciona o link aqui sem pedir permissão. Veja `config/system.md` → "MANDATO DE AUTO-ATUALIZAÇÃO".

### Repositório raiz

- [erickcmendes/gastosmart](https://github.com/erickcmendes/gastosmart) — branch principal: `main`

### Issues conhecidas

- [#4 — Configurar Supabase e criar camada de repositório (Erick)](https://github.com/erickcmendes/gastosmart/issues/4) — status: em andamento, vinculada ao PR #3

### PRs conhecidos

- [#3 — feat: configuração do Supabase e camada de repositório (Erick)](https://github.com/erickcmendes/gastosmart/pull/3) — status: aberto, aguardando revisão de @lucasmalinski

> **Para a IA:** quando você abrir, mergear, fechar ou apenas mencionar uma issue/PR nova nesta conversa, **adicione a entrada nesta seção e em `workflows/github-workflow.md`**, e atualize o status das já listadas.

---

## Decisões críticas (resumo ultra-curto)

- **Persistência:** Supabase Postgres é o destino final; o JSON local em `data/gastos.json` é legado e será desativado depois do PR-2.
- **Camada de repositório obrigatória:** `src/repository.py` é a única camada que importa `supabase`. Demais camadas usam funções do repository.
- **Sem autenticação por usuário no MVP:** RLS aberto para `anon` na tabela `gastos`. Multiusuário fica fora de escopo.
- **OpenWeather é opcional:** se `OPENWEATHER_API_KEY` não estiver setada, o resumo segue funcionando sem clima.
- **CI obrigatório:** nenhum PR é mergeado com `ruff` ou `pytest` vermelhos.
- **Cada integrante abre ≥1 PR revisado e mergeado** — exigência da disciplina.

---

## Regras Duras (resumo — a versão completa está em `config/system.md`)

1. Nunca commitar `.env`. Só `.env.example`.
2. Nunca hardcodar credenciais.
3. Nunca commitar sem rodar `ruff` + `pytest` localmente.
4. Nunca aconselhar PR sem ter testado antes.
5. Nunca deixar prints de debug em `src/app.py` final.
6. Nunca chamar `supabase` fora de `src/repository.py`.
7. Nunca `git push --force` em `main`.
8. Nunca mergear PR com CI vermelho.
9. Nunca expor `SUPABASE_KEY` em logs ou mensagens.
10. `architecture.md`, `docs/ARD.md` e `docs/SRS.md` são fontes de verdade — atualize quando algo mudar.

---

## Equipe

| Integrante | GitHub | Papel principal nos PRs |
|---|---|---|
| Erick Cardoso Mendes | [@erickcmendes](https://github.com/erickcmendes) | PR-01: infra Supabase + repository |
| Lucas Patriota Malinski da Silva Pinto | [@lucasmalinski](https://github.com/lucasmalinski) | PR-02: migração da camada de serviços |
| João Vicente Burin de Souza | [@joaovicente04](https://github.com/joaovicente04) | PR-03: testes e CI de integração |
| Cauã de Godoy Araujo | [@Caua-Godoy](https://github.com/Caua-Godoy) | PR-04: deploy Render + README final |

---

## Última revisão deste índice

A IA deve atualizar este rodapé sempre que tocar este arquivo.

- **Última atualização:** 2026-06-08 (criação inicial do `.ai/`)
- **Por:** IA (Cowork / Claude) — sob orientação de @erickcmendes
