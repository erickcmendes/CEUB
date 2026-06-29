# Checklist de Code Review

> Esta é a lista que **o revisor** segue antes de aprovar um PR no GastoSmart. Não é exaustiva — é o **piso**. Sempre que possível, vá além. Quem está revisando assume responsabilidade compartilhada pelo que vai pra `main`.

A IA também usa este checklist quando age como revisora (humana via `@menção` no PR ou IA via plugin).

---

## Antes de começar a revisão

- [ ] Li o **título** e a **descrição** do PR. Entendo o que ele se propõe a fazer.
- [ ] O PR está vinculado a uma issue (`Closes #N` no corpo). Se não, peço pro autor vincular.
- [ ] Tamanho do diff é razoável (idealmente < 400 linhas excluindo testes e docs). Se for maior, sugiro divisão.
- [ ] Branch segue convenção (`feature/`, `fix/`, `chore/`, etc. — ver [`coding_conventions.md`](../coding_conventions.md)).

---

## CI e qualidade

- [ ] A CI está **verde**. Se vermelha, NÃO continuar a revisão — peço pro autor consertar primeiro.
- [ ] Nenhum check obrigatório foi pulado.
- [ ] `ruff` passou.
- [ ] `pytest` passou (todos os testes, não apenas os novos).

---

## Segurança

- [ ] **Nenhum `.env`, chave, senha, token ou string de conexão** aparece no diff.
- [ ] Variáveis novas estão no `.env.example` com placeholder.
- [ ] Não há `print(SUPABASE_KEY)` ou similar.
- [ ] Não há `# nopep8`, `# noqa` injustificados que possam estar escondendo problema.
- [ ] Não há `eval()`, `exec()`, `subprocess.run(..., shell=True)` com input do usuário.
- [ ] Política de RLS no Supabase não foi enfraquecida sem justificativa em `ARD.md`.

---

## Arquitetura e padrões

- [ ] **Nenhum `import supabase`** fora de `src/repository.py`. (Regra Dura #6)
- [ ] **Nenhum `print()`** fora de `src/app.py` (a menos que justificado).
- [ ] **Nenhum `print("DEBUG ...")`, `breakpoint()`, `pdb`** no código final. (Regra Dura #6)
- [ ] Camadas respeitam as setas em [`architecture.md`](../architecture.md) → "Diagrama de dependências".
- [ ] Funções da camada de repositório aceitam `client=None` opcional (injeção pra mock).
- [ ] Erros de domínio levantam `ValueError` com mensagem em **português**.
- [ ] Sem `try/except: pass`. Exceções são tratadas ou re-lançadas com contexto.

---

## Código

- [ ] Nomes em **português** quando expostos ao usuário ou ao domínio (`adicionar_gasto`, `categoria`).
- [ ] Constantes em `UPPER_SNAKE_CASE` no topo do módulo.
- [ ] Imports organizados pelo ruff (stdlib → terceiros → locais).
- [ ] Strings com aspas duplas (`"..."`), salvo em f-strings ou pra evitar escape.
- [ ] Type hints presentes em funções públicas (recomendado, não bloqueante).
- [ ] Docstrings curtas em funções públicas (recomendado, não bloqueante).
- [ ] Sem código comentado "para depois".
- [ ] Sem `TODO temporário` sem owner ou contexto.

---

## Testes

- [ ] Mudanças de comportamento têm teste correspondente.
- [ ] Testes novos seguem o padrão de nome `test_<comportamento>_<resultado_esperado>`.
- [ ] Testes unitários **não usam rede** nem banco real. Tudo com mock.
- [ ] Testes de integração estão marcados com `pytest.mark.skipif(not os.getenv("SUPABASE_URL"), ...)`.
- [ ] Cobertura de borda mínima: caminho feliz + validações + casos vazios/inexistentes.
- [ ] Nomes de fixture e helpers começam com `_` se forem internos.

---

## Banco de dados (quando aplicável)

- [ ] Schema do Supabase está em sincronia com `docs/supabase/schema.sql`.
- [ ] Nova coluna ou tabela: schema.sql foi atualizado.
- [ ] Novas políticas RLS estão documentadas em `architecture.md` e `ARD.md`.
- [ ] Não há SQL cru por interpolação de string.
- [ ] Queries usam a API fluente do `supabase-py`.

---

## Documentação

- [ ] **`.ai/` atualizado** se o PR muda arquitetura, requisitos, padrões ou stack:
  - Decisão nova? → novo AD em [`ARD.md`](ARD.md).
  - Requisito novo? → entrada em [`SRS.md`](SRS.md).
  - Nova convenção de código? → [`coding_conventions.md`](../coding_conventions.md).
  - Mudança no fluxo da CLI? → [`design-doc.md`](design-doc.md) e [`../ui_guidelines.md`](../ui_guidelines.md).
  - Termo novo? → [`glossario-negocio.md`](glossario-negocio.md) ou [`glossario-tecnico.md`](glossario-tecnico.md).
- [ ] Links de issues/PRs novos foram adicionados em [`../ai.md`](../ai.md) e em [`../workflows/github-workflow.md`](../workflows/github-workflow.md).
- [ ] README atualizado se o PR muda como rodar localmente ou a stack.
- [ ] `requirements.txt` atualizado se há nova dependência, com justificativa no corpo do PR.

---

## Smoke test do revisor

Antes de aprovar, o revisor faz um teste rápido:

1. Faz checkout local da branch do PR:
   ```powershell
   git fetch origin
   git checkout <nome-da-branch-do-pr>
   ```
2. Atualiza dependências (se mudaram):
   ```powershell
   python -m pip install -r requirements.txt
   ```
3. Roda lint e testes:
   ```powershell
   python -m ruff check src/ tests/
   python -m pytest tests/ -q
   ```
4. Se o PR toca a CLI, executa pelo menos uma vez:
   ```powershell
   python src/app.py
   ```
   E confere que o menu carrega e uma operação básica funciona.

5. Se o PR toca o banco, faz smoke test de conexão:
   ```powershell
   python -c "from src.config import get_supabase_client; print(get_supabase_client().table('gastos').select('*').execute())"
   ```

Se qualquer um desses passos falhar → **Request changes** com o output do erro no comentário.

---

## Comentários do revisor

Estilo recomendado:

- **🔴 Bloqueante:** "Precisa mudar antes do merge." — use `Request changes`.
- **🟡 Sugestão:** "Funciona mas pode melhorar." — use `Comment`, não bloqueia merge.
- **🟢 Elogio / pergunta:** opcional, ajuda no aprendizado mútuo.

Nunca seja seco. Explique **por quê** sugerir uma mudança — o autor aprende mais e a próxima revisão fica mais rápida.

---

## Aprovação

Aprove o PR (`Approve`) somente quando:

- [ ] Todos os itens **bloqueantes** acima estão OK.
- [ ] O autor respondeu ou aplicou os pontos levantados.
- [ ] A CI continua verde após as últimas mudanças.

Após aprovar, **quem mergeia é o autor do PR** (boas práticas de versionamento). Estratégia: **Squash and merge** (ver `ARD.md` → AD-13).

---

## O que NUNCA aprovar

- PR com CI vermelha.
- PR sem testes para mudança de comportamento.
- PR com credenciais commitadas (incluindo "vou tirar antes do merge" — não, tira agora).
- PR que importa `supabase` fora do repository.
- PR que reescreve histórico de `main`.
- PR que remove testes existentes sem justificativa.

---

## Auditoria periódica

Uma vez por semana (ou antes da entrega final), o time confere:

- A `main` não recebeu commits diretos (só merges de PRs revisados).
- Todas as issues fechadas têm PR vinculado e mergeado.
- O `.ai/` reflete o estado real do código (sem citações a arquivos que não existem).
- O deploy do Render bate com o último commit da `main`.
