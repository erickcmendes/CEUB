# Issue para criar agora — PR-01 do Erick

Cole o conteúdo abaixo em `https://github.com/erickcmendes/gastosmart/issues/new`.

---

**Título:** Configurar Supabase e criar camada de repositório de gastos

**Labels:** `infra`, `backend`

**Assignees:** @erickcmendes

**Corpo:**

```markdown
## Contexto

Primeira PR da entrega final do Bootcamp II. Prepara a base para que as demais
PRs do time possam migrar a aplicação do JSON local para o Supabase.

Projeto Supabase já provisionado:
- URL: https://jqetggonptxjqjpapjps.supabase.co
- Schema da tabela `gastos`: ver `docs/supabase/schema.sql`

## Tarefas

- [ ] Adicionar `supabase` e `python-dotenv` ao `requirements.txt`
- [ ] Criar `src/config.py` com `get_supabase_client()` lendo `SUPABASE_URL` e `SUPABASE_KEY`
- [ ] Criar `src/repository.py` com `inserir`, `listar`, `remover_por_id` da tabela `gastos`
- [ ] Atualizar `.env.example` com as variáveis novas
- [ ] Testes unitários com mock do client Supabase em `tests/test_repository.py`
- [ ] Documentar setup em `docs/supabase/CONFIGURACAO.md`

## Critério de aceite

- `pytest tests/ -q` passa local e na CI
- `ruff check src/ tests/` passa
- `python -c "from src.config import get_supabase_client; print(get_supabase_client().table('gastos').select('*').execute())"` funciona com `.env` válido
- Nenhum segredo commitado (`.env` no `.gitignore`)

## Branch

`feature/supabase-config-e-repository`
```

---

Depois que essa issue for criada, anote o número (provavelmente `#1`) e ajuste a
mensagem do seu commit/PR para incluir `Closes #1`.
