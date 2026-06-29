# Convenções de Código

> Compatível com `pyproject.toml` (ruff `line-length=100`, regras `E, F, W, I`) e `.github/workflows/ci.yml`.

---

## Python

### Versão e ferramentas

- **Python:** 3.11+ (alvo do CI e do Docker)
- **Linter/Formatter:** [`ruff`](https://docs.astral.sh/ruff/) (regras `E, F, W, I` ativas)
- **Testes:** [`pytest`](https://docs.pytest.org/)
- **Mocks:** `unittest.mock.MagicMock` (sem `pytest-mock` por ora)
- **Variáveis de ambiente:** [`python-dotenv`](https://pypi.org/project/python-dotenv/) carregando `.env` em `src/config.py`
- **Cliente Supabase:** [`supabase-py`](https://github.com/supabase/supabase-py)

### Estilo

- **Linha:** máximo 100 colunas (não 79).
- **Strings:** aspas duplas (`"..."`) por padrão. Use simples só dentro de f-strings ou para evitar escape.
- **Type hints:** **fortemente recomendados** em funções públicas e em parâmetros de funções de negócio. Para closures internas e helpers de teste, opcional.
- **Docstrings:** triplas aspas duplas (`"""..."""`), curtas e em **português**. Documentar parâmetros e retorno apenas quando não for óbvio pela assinatura.
- **Imports:** organizados pelo ruff (`I` rule). Ordem: stdlib → terceiros → locais. Sem `from x import *`.
- **Constantes:** `UPPER_SNAKE_CASE` no topo do módulo (ex.: `CATEGORIAS`, `TABELA`).
- **Funções/variáveis:** `snake_case` em português quando expostas ao usuário (`adicionar_gasto`, `categoria`) ou ao domínio. Helpers internos podem usar inglês.
- **Classes:** `PascalCase` (sem classes obrigatórias no MVP, mas a regra vale).
- **Booleanos:** prefira `is_x` ou `tem_x` (`is_secret`, `tem_credencial`).
- **Privado:** prefixo `_` (`_client_mock` em testes).

### Estrutura de módulo padrão

```python
"""
Descrição curta do módulo em uma linha.

Detalhe opcional em parágrafo separado.
"""

# stdlib
import os
from datetime import date

# terceiros
from supabase import Client, create_client

# locais — padrão "relativo com fallback" do projeto
try:
    from .config import get_supabase_client
except ImportError:  # pragma: no cover - fallback for direct script imports in tests
    from config import get_supabase_client

# Constantes
TABELA = "gastos"


# Funções públicas
def funcao_publica(...):
    ...
```

### Padrão de imports relativos com fallback (obrigatório em `src/`)

Todos os módulos em `src/` que importam outros módulos da mesma pasta usam **import relativo com fallback para absoluto**:

```python
try:
    from . import services
except ImportError:
    import services
```

**Por que:** o pacote é executado de duas formas no projeto:
- como módulo: `python -m src.app` ou via Streamlit (`streamlit run src/app_web.py`) → import relativo funciona
- como script avulso pelos testes: `tests/test_X.py` injeta `src/` no `sys.path` antes de `import X` → import absoluto funciona

O fallback cobre os dois cenários sem precisar configurar `conftest.py`. Replicar em todo módulo novo em `src/`.

Veja registros em [`architecture.md`](architecture.md) e em [`docs/glossario-tecnico.md`](docs/glossario-tecnico.md).

### Tratamento de erros

- **Validações de domínio:** levantam `ValueError` com mensagem em **português** clara (ex.: `raise ValueError("A descrição não pode ser vazia.")`).
- **Erros de I/O e rede:** capturados na fronteira (camada de repositório ou serviço de clima), nunca propagados para a CLI sem tratamento.
- **Nunca capturar `Exception` genérico** sem re-raise. Use exceções específicas (`urllib.error.URLError`, `json.JSONDecodeError`, etc.).
- **Sem `try/except: pass`.** Se houver razão legítima, justifique em comentário.

### Logging e prints

- **CLI:** `print()` é aceitável apenas em `src/app.py` para diálogo com o usuário.
- **Demais camadas:** não imprimem nada. Retornam dados ou levantam exceção.
- **Debug:** `print("DEBUG ...")` é PROIBIDO em código commitado (Regra Dura #6 em `config/system.md`). Use `breakpoint()` localmente e remova antes do commit.
- **Quando precisar de log estruturado** (futuro): adotar `logging` do stdlib com configuração em `src/config.py`.

### Padrões obrigatórios da camada de repositório

- Todas as funções aceitam `client=None` opcional para injeção de mock em testes.
- Quando `client=None`, chamam `get_supabase_client()` internamente.
- Retornam tipos primitivos do Python (`dict`, `list[dict]`, `bool`), nunca objetos do `supabase-py`.
- Nome da tabela em constante de módulo (`TABELA = "gastos"`).
- **Nada de SQL cru.** Use sempre a API fluente do `supabase-py`.

### Padrões obrigatórios da camada de serviços (a partir do PR-2)

- **Não importa `supabase`.** Apenas o `repository`.
- Valida entradas antes de chamar o repository.
- Erros de domínio são `ValueError` com mensagens em português.
- Retorna dicionários simples (`dict`) — nada de objetos do banco.

### Padrões de teste

- **Localização:** todos em `tests/`.
- **Nome:** `test_<modulo>.py` para o módulo correspondente; `test_<modulo>_<aspecto>.py` se for muito grande.
- **Funções:** `test_<comportamento>_<resultado_esperado>` em português (ex.: `test_remover_por_id_retorna_false_quando_nao_encontra`).
- **Sem rede em testes unitários.** Tudo com mock.
- **Testes de integração** com Supabase usam `pytest.mark.skipif(not os.getenv("SUPABASE_URL"), ...)` para serem pulados quando faltam credenciais.
- **Path injection:** o padrão atual é `sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))` no topo de cada arquivo de teste para permitir `import app`, `import repository` etc. Manter consistente.
- **Cobertura mínima esperada por módulo de negócio:**
  - Caminho feliz (1+ teste)
  - Casos de validação (1 por regra de negócio)
  - Borda (vazio, valor zero, ID inexistente)
- **Mock do `supabase-py`** segue o padrão de `tests/test_repository.py` (`_client_mock` helper) — replicar quando criar testes para outras camadas.

### Conventional Commits

Mensagem de commit no formato:

```
<tipo>(<escopo opcional>): descrição curta no imperativo
```

Tipos aceitos:

- `feat:` nova funcionalidade
- `fix:` correção de bug
- `chore:` mudanças que não afetam código de produção (configs, deps, docs internos)
- `docs:` mudanças exclusivamente em documentação para humanos
- `test:` adicionar ou ajustar testes
- `refactor:` mudança de código sem alterar comportamento externo
- `style:` formatação (ruff, espaços) — sem mudança de lógica
- `ci:` mudanças em `.github/workflows/`
- `build:` mudanças em `Dockerfile`, `requirements.txt`, `pyproject.toml`

Exemplos válidos:

```
feat: configuracao do supabase e camada de repositorio
fix(services): corrigir validacao de valor zero em adicionar_gasto
chore: atualizar .ai/ com novo PR #5 mergeado
ci: rodar integracao com supabase apenas em main
```

Quando o commit fecha uma issue, adicione no corpo: `Closes #N`.

### Branches

| Prefixo | Uso |
|---|---|
| `feature/` | novas funcionalidades |
| `fix/` | correções de bug |
| `chore/` | manutenção (deps, configs, `.ai/`) |
| `docs/` | mudanças só em documentação humana |
| `ci/` | mudanças no pipeline |

Nome em **kebab-case**, descritivo, curto. Ex.: `feature/supabase-config-e-repository`, `fix/categoria-invalida-mensagem`, `chore/atualizar-ai-pr5`.

---

## Git

- **Branch principal:** `main`. Nunca commitar direto.
- **Sempre via PR**, mesmo para mudanças pequenas. Cada integrante precisa de PR aprovado para cumprir a barema do bootcamp.
- **PRs pequenos.** Se passar de ~400 linhas de diff (excluindo testes e docs), considere dividir.
- **Squash and merge** é a estratégia padrão de merge — histórico linear e limpo na main.
- **Antes do commit:**
  - `python -m ruff check src/ tests/`
  - `python -m pytest tests/ -q`
  - (se tocou Supabase) smoke test via REPL
- **Nunca `git push --force` em `main`.** Em branches de feature, use `--force-with-lease` se for absolutamente necessário e avise o time.

---

## Segurança

- **Nunca commitar credenciais reais.** Use `.env` local (no `.gitignore`) e `secrets` do GitHub Actions / Render.
- **`.env.example` é o único arquivo de env versionado**, e contém placeholders (vazios ou `sua_chave_aqui`).
- **Nada de SQL cru por interpolação de string.** O `supabase-py` já protege; apenas reforço.
- **Nunca imprima nem logue a `SUPABASE_PUB_KEY` ou qualquer token.** Inclusive em mensagens de erro.
- **OpenWeather API key** é exposta como argumento de função em URL; mesmo sendo "menor", trate como credencial e mantenha apenas em env.
- **Dependências:** `pip install` somente de pacotes pinados em `requirements.txt`. Antes de adicionar uma dep nova, justifique no PR (no corpo).

---

## Documentação dentro do código

- **README.md** é para humanos e fica na raiz.
- **`docs/` para humanos** (já existe).
- **`.ai/` para IA** (este diretório).
- Não duplique conteúdo entre `.ai/` e `docs/`. Quando ambos forem necessários, mantenha o `.ai/` como fonte primária e o `docs/` como tradução resumida.

---

## Dependências

`requirements.txt` é a fonte. Manter pinadas com `>=` em majors estáveis:

```
pytest>=8.0.0
ruff>=0.4.0
supabase>=2.0.0
python-dotenv>=1.0.0
```

Quando adicionar uma dep, atualize também a tabela "Stack" em `ai.md` e em `architecture.md` (variáveis de ambiente, se aplicável).

---

## Checklist rápido antes de commitar

- [ ] `python -m ruff check src/ tests/` passa
- [ ] `python -m pytest tests/ -q` passa
- [ ] (se tocou banco) smoke test rodou OK
- [ ] Sem `print("DEBUG")`, `breakpoint()`, `pdb`, `TODO temporário`
- [ ] Sem `.env` ou credenciais no diff
- [ ] `.env.example` atualizado se alguma variável nova foi adicionada
- [ ] `.ai/` atualizado se o commit muda arquitetura, requisitos ou padrões
- [ ] Mensagem de commit em Conventional Commits
- [ ] Issue vinculada via `Closes #N` no corpo do PR
