# Fila de Tarefas

> Lista sequencial das tarefas do GastoSmart. Processe **de cima pra baixo** — só comece a próxima quando a anterior estiver totalmente concluída, revisada e mergeada.
>
> A IA marca `[x]` ao concluir, move blocos pra "Histórico" quando o PR correspondente é mergeado, e acrescenta tarefas novas no fim quando surgirem.

---

## Como processar cada item

1. **Ler** o item e o link da issue/PR.
2. **Atualizar** o status da issue no GitHub para "In progress" (se aplicável).
3. **Implementar** seguindo [`github-workflow.md`](github-workflow.md) e os checklists em [`../coding_conventions.md`](../coding_conventions.md) e [`../docs/pr-review-checklist.md`](../docs/pr-review-checklist.md).
4. **Commitar** com [Conventional Commits](../coding_conventions.md#conventional-commits).
5. **Abrir PR**, marcar reviewer, esperar CI verde e aprovação, mergear.
6. **Atualizar** este arquivo: marcar `[x]` e mover para o histórico no fim do arquivo.

---

## Fila ativa

### Atualização integral do `.ai/` pós-merges (Erick, em curso)

- [x] Corrigir `src/config.py` para ler `SUPABASE_PUB_KEY` com fallback
- [x] Corrigir `README.md` para usar `SUPABASE_PUB_KEY`
- [x] Atualizar `ai.md` com PRs reais, PDF de entrega, equipe com matrículas
- [x] Atualizar `architecture.md` com Streamlit e fluxo Web
- [x] Atualizar `config/system.md` com nova var, regras duras 11 e Streamlit
- [x] Adicionar AD-15 (Streamlit) e AD-16 (rename) em `docs/ARD.md`
- [x] Atualizar `workflows/github-workflow.md` com PRs #9, #10, #11, #13
- [x] Atualizar `workflows/task-queue.md` (este arquivo)
- [x] Atualizar `docs/glossario-tecnico.md` com Streamlit
- [x] Atualizar `coding_conventions.md` com padrão de imports relativos
- [ ] Abrir PR `chore(.ai): sincronizar contexto pos PRs #9, #10, #11, #13`
- [ ] PR aprovado e mergeado
- [ ] Renomear variável no painel do Render: `SUPABASE_KEY` → `SUPABASE_PUB_KEY`
- [ ] Smoke test do deploy após renomeação

### Entrega final (Erick)

- [ ] Validar que o PDF em `docs/PDF_ENTREGA.md` está com todos os 4 integrantes e links corretos
- [ ] Gerar PDF a partir de `docs/PDF_ENTREGA.md` (Word/Markdown → PDF)
- [ ] Enviar PDF na plataforma SalaOnline até **14/06/2026 às 23:55**
- [ ] Marcar como concluído aqui

---

## Histórico (tarefas concluídas)

### PR-01 — Infra Supabase + camada de repositório (Erick) ✅

PR [#3](https://github.com/erickcmendes/gastosmart/pull/3) mergeado.

- [x] `requirements.txt` com `supabase` e `python-dotenv`
- [x] `src/config.py` com `get_supabase_client()`
- [x] `src/repository.py` com `inserir`, `listar`, `remover_por_id`
- [x] `.env.example` com `SUPABASE_URL` e chave Supabase
- [x] `tests/test_repository.py` com mocks
- [x] `docs/supabase/schema.sql` aplicado por @joaovicente04 no painel Supabase

### Setup do `.ai/` ✅

PR [#13 / chore separado] mergeado.

- [x] Estrutura `.ai/` espelhando modelo do LegisTracker (12 arquivos)
- [x] PR aprovado e mergeado

### PR-02 — Migração da camada de serviços (Lucas) ✅

PR [#9](https://github.com/erickcmendes/gastosmart/pull/9) mergeado.

- [x] `src/services.py` com `adicionar_gasto`, `listar_gastos`, `remover_gasto`, `resumo_gastos`
- [x] `buscar_clima` movido para `src/services.py`
- [x] `src/app.py` virou fino, encaminha pra services
- [x] Lógica de JSON local removida
- [x] `tests/test_services.py` com `repository` mockado
- [x] Padrão de imports relativos com fallback adotado

### PR-03 — Testes extras + CI ajustes (João) ✅

PR [#10](https://github.com/erickcmendes/gastosmart/pull/10) mergeado.

- [x] Cenários extras adicionados em `tests/test_services.py`
- [x] CI passou a usar `ruff check --fix`
- [x] Correção de assertion de `listar_gastos`

> Nota: a issue planejada inicialmente para o João incluía também integração contra Supabase real com `skipif` — esse trabalho não foi feito nesta entrega. Registrado como caminho futuro.

### PR-04 — Deploy Render + README + PDF de entrega (Cauã) ✅

PR [#11](https://github.com/erickcmendes/gastosmart/pull/11) mergeado (Closes #6, #7).

- [x] `SUPABASE_URL` e chave Supabase configuradas no Render
- [x] Deploy validado
- [x] `docs/DEPLOY.md` criado
- [x] README atualizado com Supabase e instruções
- [x] `docs/PDF_ENTREGA.md` com nomes, matrículas e links

### PR-Streamlit — Interface Web (Erick + Lucas) ✅

PR [#13](https://github.com/erickcmendes/gastosmart/pull/13) mergeado.

- [x] `src/app_web.py` criado com 4 abas (resumo, listar, adicionar, remover)
- [x] `streamlit` adicionado em `requirements.txt`
- [x] `Dockerfile` ajustado para `streamlit run` na porta 8501
- [x] Sidebar com clima quando `OPENWEATHER_API_KEY` setada
- [x] AD-15 registrado pela IA no ARD nesta rodada de atualização

---

## Observações

- **Prazo:** 14/06/2026 23:55. Restam ~3 dias na data desta atualização.
- **Critério individual:** todos os 4 integrantes têm PR mergeado vinculado ao seu user GitHub — **cumprido**.
- **Reunião do time:** próxima sincronização para validar deploy e PDF antes da submissão.
