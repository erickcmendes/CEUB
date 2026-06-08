# Passo a passo — PR-01 (Erick)

Guia descomplicado para fechar a PR-01 (`feature/supabase-config-e-repository`) hoje ou amanhã.

Pré-requisito: o Vicente já rodou o `docs/supabase/schema.sql` no Supabase, criando a tabela `gastos`.

---

## 0. Antes de começar — limpar a sujeira de CRLF

Seu `git status` está mostrando 6 arquivos modificados que são só normalização de quebra de linha (CRLF/LF). Descarte tudo:

```powershell
cd "C:\Users\hulkd\OneDrive\Documents\Docs estudo\Ceub\Bootcamps\Bootcamp II\gastosmart"
git checkout -- .
git status   # tem que vir limpo
```

Para isso não voltar a acontecer, configure o autocrlf (uma vez só):

```powershell
git config --global core.autocrlf true
```

---

## 1. Criar a branch e ativar o ambiente

```powershell
git checkout main
git pull
git checkout -b feature/supabase-config-e-repository

# Ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Dependências (agora com supabase + dotenv)
python -m pip install -r requirements.txt
```

---

## 2. Configurar o `.env` local

Crie o `.env` na raiz a partir do `.env.example`:

```powershell
copy .env.example .env
```

Garanta que tem dentro:

```env
SUPABASE_URL=https://jqetggonptxjqjpapjps.supabase.co
SUPABASE_KEY=sb_publishable_XaI_Sb_1onqHfiFMHwwU5Q_wrcAXTxf
```

Confirme que o `.env` está ignorado:

```powershell
git check-ignore -v .env   # tem que retornar uma linha (significa que vai ser ignorado)
```

---

## 3. Validar localmente

```powershell
python -m ruff check src/ tests/
python -m pytest tests/ -q
```

Esperado: ruff sem erros e **29 testes passando** (18 antigos + 11 novos de repository).

### Smoke test manual de conexão (opcional, mas recomendado)

Confirma que sua key e URL estão funcionando:

```powershell
python -c "from src.config import get_supabase_client; c = get_supabase_client(); print(c.table('gastos').select('*').execute())"
```

Esperado: imprime um `APIResponse(...)` com `data=[]` (ou com registros se o Vicente já inseriu algo de teste).

---

## 4. Commitar

Os arquivos novos/modificados desta PR são:

```
src/config.py                       (novo)
src/repository.py                   (novo)
tests/test_repository.py            (novo)
docs/supabase/schema.sql            (novo)
docs/supabase/CONFIGURACAO.md       (novo)
docs/PLANO_ENTREGA_FINAL.md         (novo)
docs/ISSUES_GITHUB.md               (novo)
docs/PASSO_A_PASSO_PR01.md          (este arquivo)
requirements.txt                    (modificado: + supabase + dotenv)
.env.example                        (modificado: + SUPABASE_URL/KEY)
```

```powershell
git add src/config.py src/repository.py tests/test_repository.py
git add docs/supabase/ docs/PLANO_ENTREGA_FINAL.md docs/ISSUES_GITHUB.md docs/PASSO_A_PASSO_PR01.md
git add requirements.txt .env.example

git status    # confere a lista

git commit -m "feat: configuracao do supabase e camada de repositorio (#1, #2)"
```

> Se ainda não houver issues no GitHub no momento do commit, troque por `feat: configuracao do supabase e camada de repositorio` e atualize o PR depois com `Closes #1, Closes #2` no corpo.

---

## 5. Push e abrir o PR

```powershell
git push -u origin feature/supabase-config-e-repository
```

O terminal vai imprimir um link tipo `https://github.com/erickcmendes/gastosmart/pull/new/feature/supabase-config-e-repository` — abre ele.

### Conteúdo sugerido do PR

**Título:** `feat: configuração do Supabase e camada de repositório`

**Corpo:**

```markdown
## O que foi feito

- Adicionado `supabase` e `python-dotenv` ao `requirements.txt`.
- `src/config.py`: carrega `.env` e expõe `get_supabase_client()`.
- `src/repository.py`: camada de acesso ao banco com `inserir`, `listar` e `remover_por_id`.
- `tests/test_repository.py`: 11 testes unitários com mock do client (sem rede).
- `docs/supabase/schema.sql` + `docs/supabase/CONFIGURACAO.md`: schema da tabela `gastos` e guia de setup.
- `docs/PLANO_ENTREGA_FINAL.md` + `docs/ISSUES_GITHUB.md`: planejamento e issues da entrega final.
- `.env.example` atualizado com `SUPABASE_URL` e `SUPABASE_KEY`.

Closes #1
Closes #2

## Como testar

- [x] Rodei `python -m pytest tests/ -q` (29 passed)
- [x] Rodei `python -m ruff check src/ tests/` (OK)
- [x] Validei conexão real com `python -c "from src.config import get_supabase_client; ..."`

## Checklist

- [x] A mudança tem escopo pequeno e claro
- [x] Não inclui `.env`, chaves, senhas ou dados locais
- [x] Atualizei a documentação quando necessário
- [ ] Pedi revisão de outro integrante (Lucas)
```

---

## 6. Pedir revisão

No PR no GitHub:

1. Na barra lateral direita → **Reviewers** → marca o **Lucas**.
2. Avisa no grupo do time.
3. Quando a CI ficar verde e o Lucas aprovar, faça **Squash and merge**.

---

## 7. Depois do merge

- Avisa Lucas e João que podem partir para os PRs 2 e 3 — eles agora têm `config.py` e `repository.py` para importar.
- Marca a issue #1 e #2 como fechadas (acontece automático com `Closes #N`).
- Atualiza no quadro de tarefas que a sua entrega individual está cumprida.

---

## Resolução de problemas comuns

**`ModuleNotFoundError: No module named 'supabase'`**
Esqueceu de instalar dependências: `python -m pip install -r requirements.txt`.

**`RuntimeError: SUPABASE_URL e SUPABASE_KEY precisam estar definidas`**
Falta o `.env` na raiz, ou o `python-dotenv` não carregou. Confere se o `.env` está exatamente em `gastosmart/.env`.

**CI falha no GitHub Actions**
Como o CI não tem o `.env`, qualquer teste que crie um cliente real vai falhar. Por isso os testes novos usam mock. Se quebrar, ver `tests/test_repository.py` — nenhum teste deve chamar `get_supabase_client()` direto.

**Erro `Row Level Security` ao inserir**
O schema já cria políticas abertas para `anon`. Se mesmo assim der, conferir no dashboard do Supabase em **Authentication → Policies** se elas foram aplicadas na tabela `gastos`.
