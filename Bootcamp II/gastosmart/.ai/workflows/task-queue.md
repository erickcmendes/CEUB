# Fila de Tarefas

> Lista sequencial das próximas tarefas técnicas do GastoSmart. Processe **de cima pra baixo** — só comece a próxima quando a anterior estiver totalmente concluída, revisada e mergeada.
>
> A IA atualiza esta fila quando uma tarefa é concluída (marca `[x]`) e quando novas tarefas surgem (acrescenta no fim). Quando todas as tarefas relevantes para a entrega final estiverem feitas, a IA escreve um marco `--- Entrega final concluída ---` aqui.

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

### PR-01 — Infra Supabase + camada de repositório (Erick)

- [x] Adicionar `supabase` e `python-dotenv` ao `requirements.txt`
- [x] Criar `src/config.py` com `get_supabase_client()`
- [x] Criar `src/repository.py` com `inserir`, `listar`, `remover_por_id`
- [x] Atualizar `.env.example` com `SUPABASE_URL` e `SUPABASE_KEY`
- [x] Criar `tests/test_repository.py` com mocks
- [x] Criar `docs/supabase/schema.sql` e `docs/supabase/CONFIGURACAO.md`
- [x] Aplicar `schema.sql` no Supabase (responsável: Vicente / João Vicente)
- [ ] PR aprovado e mergeado em `main` ← [#3](https://github.com/erickcmendes/gastosmart/pull/3)
- [ ] **Atualizar este arquivo + `github-workflow.md` + `ai.md`** após o merge

### Setup do `.ai/` (Erick, chore paralelo)

- [x] Criar estrutura `.ai/` espelhando modelo do LegisTracker
- [ ] Abrir PR `chore: adicionar pasta .ai com contexto para IA` (decisão pendente: PR único ou commit direto via chore — usar PR pra cumprir a barema)
- [ ] PR aprovado e mergeado

### PR-02 — Migração da camada de serviços (Lucas) — bloqueado por PR-01

- [x] Criar `src/services.py` com `adicionar_gasto`, `listar_gastos`, `remover_gasto`, `resumo_gastos`
- [x] Mover `buscar_clima` para `src/services.py`
- [x] Atualizar `src/app.py` para importar de `services`
- [x] Remover lógica de JSON local de `src/app.py`
- [x] Criar `tests/test_services.py` com `repository` mockado
- [ ] PR aprovado e mergeado

### PR-03 — Testes + CI de integração (João) — pode iniciar em paralelo ao PR-02

- [ ] Atualizar `tests/test_app.py` para a nova arquitetura
- [ ] Criar `tests/test_integration_supabase.py` com `pytest.mark.skipif`
- [ ] Adicionar job opcional `integration` em `.github/workflows/ci.yml`
- [ ] Documentar como rodar localmente em `docs/`
- [ ] PR aprovado e mergeado

### PR-04 — Deploy + README final (Cauã)

- [ ] Configurar `SUPABASE_URL` e `SUPABASE_KEY` no Render
- [ ] Disparar deploy manual após PRs 1-3 mergeados
- [ ] Validar app implantado fazendo um insert e conferindo no painel do Supabase
- [ ] Criar `docs/DEPLOY.md` com passo a passo
- [ ] Atualizar README.md: tecnologias (Supabase), instruções com `.env`, link de deploy
- [ ] Criar `docs/PDF_ENTREGA.md` com nomes, matrículas, links
- [ ] PR aprovado e mergeado

### Entrega final (Erick)

- [ ] Gerar PDF a partir de `docs/PDF_ENTREGA.md`
- [ ] Enviar PDF na plataforma SalaOnline até 14/06/2026 às 23:55
- [ ] Marcar como concluído aqui

---

## Histórico (tarefas concluídas)

> A IA move itens da fila ativa para cá quando o PR correspondente é mergeado.

*Vazio até o primeiro PR ser mergeado.*

---

## Observações

- **Bloqueios:** PR-02 depende do PR-01 mergeado. PR-04 depende dos PRs 1, 2 e 3.
- **Paralelismo:** PR-02 (Lucas) e PR-03 (João) podem rodar simultaneamente depois do PR-01.
- **Prazo:** 14/06/2026 23:55. Trabalhar com folga — combinar deadline interno 12/06 para todos os PRs mergeados, deixando 2 dias para validação final e PDF.
- **Reunião do time:** 08/06/2026 à noite — criar issues restantes (#5 a #9 prováveis), distribuir e definir cronograma fino.
