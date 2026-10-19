# Glossário Técnico

> Termos técnicos usados no GastoSmart, explicados em português e com contexto de **como cada um se aplica ao nosso projeto**. Quando uma tecnologia ou conceito técnico novo entrar no projeto, adicione aqui. Para termos do domínio (gasto, categoria, resumo), ver [`glossario-negocio.md`](glossario-negocio.md).

---

## Banco de Dados e Backend

### BaaS (Backend as a Service)

Modelo em que um provedor oferece "backend pronto" — banco, autenticação, storage, edge functions — sem você precisar gerenciar servidor. Você consome via SDK.

**No GastoSmart:** Supabase é nosso BaaS. Substitui ter que provisionar Postgres em VM, configurar firewall, fazer backup etc.

---

### Streamlit

Framework Python que transforma scripts em aplicações web interativas sem precisar escrever HTML/CSS/JS. O dev escreve o app como um script Python linear; o Streamlit renderiza widgets (botões, forms, tabelas, gráficos) no navegador.

**No GastoSmart:** o `src/app_web.py` usa Streamlit pra expor 4 abas (Resumo, Listar, Adicionar, Remover) sobre os mesmos serviços que a CLI usa. É o que está no deploy do Render. Veja AD-15 em [`ARD.md`](ARD.md) para a história da decisão.

**Comando local:**
```bash
streamlit run src/app_web.py
```

Abre em `http://localhost:8501`.

---

### Web Service (Render)

Tipo de hospedagem que serve HTTP/HTTPS público numa porta específica do container. Diferente de "Background Worker" (que só roda sem expor porta).

**No GastoSmart:** o Render hospeda um Web Service que escuta na porta 8501 (Streamlit). Auto-deploy a cada push em `main`.

---

### Supabase

Plataforma open-source de BaaS construída em cima do **PostgreSQL**. Oferece banco relacional, autenticação, storage, realtime, edge functions e dashboard web.

**No GastoSmart:**

- Usamos apenas o **banco de dados** (PostgreSQL).
- Projeto: `https://jqetggonptxjqjpapjps.supabase.co`
- Plano: free tier (atenção: pausa após ~1 semana de inatividade).
- Acesso via biblioteca `supabase-py` no Python.
- Painel administrativo: `https://supabase.com/dashboard/project/jqetggonptxjqjpapjps`

**Por que escolhemos:** ver [`ARD.md`](ARD.md) → AD-03.

---

### PostgreSQL

Sistema de gerenciamento de banco de dados **relacional** open-source. Suporta SQL padrão, transações ACID, full-text search nativo, JSON nativo, extensões.

**No GastoSmart:** uma única tabela `gastos` (ver schema em `architecture.md`). Sem joins, sem stored procedures. Uso simples.

---

### `supabase-py`

Biblioteca Python oficial para conectar ao Supabase. Instalação: `pip install supabase`.

**API fluente:**

```python
client.table("gastos").insert({"descricao": "...", ...}).execute()
client.table("gastos").select("*").order("data", desc=True).execute()
client.table("gastos").delete().eq("id", 5).execute()
```

**Onde é usada no projeto:** apenas em `src/repository.py`. Nenhum outro módulo importa `supabase` (Regra Dura #6).

---

### RLS (Row Level Security)

Recurso do PostgreSQL (exposto também pelo Supabase) que aplica **políticas por linha**: cada SELECT/INSERT/UPDATE/DELETE pode ser permitido ou negado conforme uma condição que envolve a role do cliente e os dados.

**No GastoSmart:** habilitamos RLS na tabela `gastos` com 4 políticas abertas para a role `anon` (qualquer um com a publishable key pode operar). Isso é **temporário e documentado** (ver AD-10 em [`ARD.md`](ARD.md)). Em produção real, substituiríamos por `auth.uid() = user_id`.

---

### `anon` (role anônima do Supabase)

Role padrão usada por requisições que apresentam apenas a **publishable key** (sem autenticação de usuário). Tem permissões definidas pelas políticas RLS.

**No GastoSmart:** todas as operações da CLI rodam como `anon`. Não há fluxo de login.

---

### Publishable key vs Service role key

| Tipo | Quando usar | Onde fica |
|---|---|---|
| **Publishable / anon** | Cliente final (CLI, frontend, Streamlit). Limitada pelas políticas RLS. | `.env` local + Render + GitHub Secrets |
| **Service role** | Backend confiável que precisa burlar RLS. **Nunca** no frontend ou em código que vaza. | Não usamos no GastoSmart. |

**No GastoSmart:** usamos apenas a publishable key. Nome no Supabase atual: `sb_publishable_XaI_Sb_1onqHfiFMHwwU5Q_wrcAXTxf`. A variável de ambiente que carrega essa chave é **`SUPABASE_PUB_KEY`** (decisão AD-16). Para compatibilidade com setups antigos, `src/config.py` ainda aceita `SUPABASE_KEY` como fallback.

---

### CRUD

Sigla para **Create, Read, Update, Delete** — as 4 operações básicas de persistência.

**No GastoSmart:**

- **Create:** `repository.inserir`
- **Read:** `repository.listar`
- **Update:** não implementado no MVP (Out of Scope em `SRS.md`)
- **Delete:** `repository.remover_por_id`

---

### Camada de repositório (Repository Pattern)

Padrão de projeto que isola o **acesso aos dados** do resto da aplicação. As camadas superiores (serviços, controllers, CLI) não conhecem detalhes do banco.

**No GastoSmart:** `src/repository.py` é a única camada que importa `supabase`. As demais chamam `repository.inserir(...)` etc.

**Vantagem prática:** trocar Supabase por outro banco no futuro = mudar apenas esse arquivo.

---

### Camada de serviços

Onde ficam as **regras de negócio** (validações, cálculos, agregações). Não conhece o banco, só conhece o repositório.

**No GastoSmart:** `src/services.py` (a partir do PR-02). Funções: `adicionar_gasto`, `listar_gastos`, `remover_gasto`, `resumo_gastos`.

---

## Testes

### Mock

Objeto falso que substitui uma dependência real em teste. Permite testar uma função sem precisar do banco real, sem rede, sem efeitos colaterais.

**No GastoSmart:** usamos `unittest.mock.MagicMock` para fingir o cliente Supabase. Exemplo em `tests/test_repository.py` → helper `_client_mock`.

---

### Teste unitário

Testa uma função isoladamente, com todas as dependências mockadas.

**No GastoSmart:** todos os testes em `tests/test_repository.py` e `tests/test_app.py` são unitários.

---

### Teste de integração

Testa o sistema com dependências reais (banco real, rede real).

**No GastoSmart:** `tests/test_integration_supabase.py` (criado no PR-03) roda contra o Supabase real. Marcado com `pytest.mark.skipif` para ser pulado quando faltam credenciais.

---

### Smoke test

Teste rápido e manual, geralmente após uma mudança, só pra confirmar que "nada óbvio quebrou".

**No GastoSmart:** antes de commitar mudanças que tocam o Supabase, rodar:

```bash
python -c "from src.config import get_supabase_client; print(get_supabase_client().table('gastos').select('*').execute())"
```

Esperado: `APIResponse` com `data=[...]` sem erro. Esse é o smoke test obrigatório (Regra Dura #4).

---

### `pytest`

Framework de testes para Python. Roda arquivos que começam com `test_` e funções que começam com `test_`.

**No GastoSmart:** comando padrão `python -m pytest tests/ -q`. Config em `pyproject.toml`.

---

### `pytest.mark.skipif`

Decorador que pula um teste se uma condição for verdadeira. Usamos para pular testes de integração quando o `.env` não está configurado.

```python
@pytest.mark.skipif(not os.getenv("SUPABASE_URL"), reason="Requer SUPABASE_URL configurada")
def test_integracao_real():
    ...
```

---

## Qualidade de código

### `ruff`

Linter e formatador moderno para Python, escrito em Rust. Muito mais rápido que `flake8`/`black`/`isort` combinados.

**No GastoSmart:** regras ativas: `E` (pycodestyle errors), `F` (pyflakes), `W` (pycodestyle warnings), `I` (isort). Linha máxima: 100 colunas. Comando: `ruff check src/ tests/`.

---

### Linter

Ferramenta que analisa código estaticamente para encontrar problemas (sintaxe inválida, imports não usados, variáveis não declaradas, estilo). No nosso caso, é o `ruff check`.

---

### Type hints

Anotações de tipo em Python. Ex.: `def somar(a: int, b: int) -> int:`.

**No GastoSmart:** recomendados em funções públicas e parâmetros de funções de negócio. Não validados em tempo de execução (não usamos `mypy`).

---

## CI/CD

### CI (Continuous Integration)

Prática de rodar automaticamente lint + testes a cada push/PR para detectar erros cedo.

**No GastoSmart:** GitHub Actions, workflow `quality` em `.github/workflows/ci.yml`.

---

### GitHub Actions

Serviço de CI/CD nativo do GitHub. Workflows definidos em YAML em `.github/workflows/`.

---

### CD (Continuous Deployment)

Prática de subir automaticamente o código mais recente da `main` para produção.

**No GastoSmart:** Render faz CD automático a cada push em `main` (configurado no painel do Render).

---

### Pipeline

Sequência de etapas automatizadas. No nosso caso, a pipeline da CI é: checkout → setup Python → install deps → ruff → pytest.

---

## Deploy e Containers

### Render

Plataforma de hospedagem PaaS. Suporta Web Services via Dockerfile, banco gerenciado, cron jobs.

**No GastoSmart:** hospedamos o app como Web Service via Dockerfile. URL: https://gastosmart-3nje.onrender.com.

**Alerta:** plano free dorme após inatividade — primeira execução depois disso demora ~30s ("cold start").

---

### Docker

Tecnologia de containerização. Permite empacotar app + dependências + runtime em uma imagem reproduzível.

**No GastoSmart:** `Dockerfile` na raiz. Imagem base: `python:3.11-slim`.

**Build local:**
```bash
docker build -t gastosmart .
docker run -it --rm gastosmart
```

---

### Dockerfile

Receita declarativa para construir uma imagem Docker. No nosso caso: copia código, instala deps, define comando padrão.

---

### Container

Instância em execução de uma imagem Docker. Isolado do host.

---

## Configuração e Segurança

### `.env`

Arquivo local com variáveis de ambiente sensíveis (credenciais, URLs com tokens). **Nunca versionado.**

**No GastoSmart:** ignorado em `.gitignore`. Cada dev cria o seu a partir de `.env.example`.

---

### `.env.example`

Arquivo versionado com **placeholders** (vazios ou exemplos genéricos) das variáveis esperadas. Serve como documentação.

**No GastoSmart:** é o único `.env*` que vai pro repositório (Regra Dura #3).

---

### `python-dotenv`

Biblioteca que carrega variáveis do `.env` automaticamente quando o app inicia.

**No GastoSmart:** chamado em `src/config.py` via `load_dotenv()`.

---

### Variável de ambiente

Mecanismo do sistema operacional para passar configuração ao processo. Ex.: `SUPABASE_URL`, `OPENWEATHER_API_KEY`.

**No GastoSmart:** todas as configurações sensíveis e ambiente-específicas vêm de env vars. Listadas em `architecture.md` → "Variáveis de ambiente".

---

### Secret (no contexto de CI/CD)

Variável de ambiente armazenada de forma criptografada no provedor (GitHub Actions, Render). Não aparece nos logs.

**No GastoSmart:**
- GitHub: `Settings → Secrets and variables → Actions`
- Render: `Environment` no painel do serviço.

---

## Git e GitHub

### Branch

Linha paralela de desenvolvimento. No nosso fluxo: `main` é a "oficial"; features ficam em branches separadas até serem revisadas e mergeadas.

---

### Pull Request (PR)

Pedido formal de revisão e merge de uma branch para outra (geralmente para a `main`). Inclui diff, descrição, comentários, status da CI.

**No GastoSmart:** **toda mudança passa por PR.** Cada integrante precisa de pelo menos 1 PR mergeado para a nota.

---

### Code Review

Revisão do código por outro humano antes do merge. Foca em correção, segurança, legibilidade e padrões.

**No GastoSmart:** checklist completo em [`pr-review-checklist.md`](pr-review-checklist.md).

---

### Squash and merge

Estratégia de merge que combina todos os commits da branch em um único commit ao mergear na `main`.

**No GastoSmart:** estratégia padrão (AD-13 em `ARD.md`). Histórico da `main` fica linear e fácil de auditar.

---

### Revert

Comando `git revert <commit>` que cria um novo commit desfazendo as mudanças de um commit anterior. **Não reescreve histórico.**

**No GastoSmart:** já foi usado uma vez (durante o desenvolvimento do PR-01) para desfazer um commit direto na `main`.

---

### Conventional Commits

Convenção para mensagens de commit no formato `<tipo>: descrição`. Tipos: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `ci`, `build`.

**No GastoSmart:** obrigatório. Exemplos e regras em [`coding_conventions.md`](../coding_conventions.md) → "Conventional Commits".

---

### CRLF / LF

Tipos de quebra de linha. **Windows usa CRLF** (`\r\n`), **Linux/macOS usam LF** (`\n`).

**No GastoSmart:** rodamos `git config --global core.autocrlf true` no Windows para evitar PRs poluídos por mudança de quebra de linha. `.gitattributes` futuro pode reforçar.

---

## Integrações externas

### OpenWeather API

API pública gratuita para dados meteorológicos. Requer chave (free tier: 1000 chamadas/dia).

**No GastoSmart:** consumimos apenas o endpoint `/data/2.5/weather` com `units=metric` e `lang=pt_br`. Integração opcional — sem chave, o app segue funcionando.

---

### URL endpoint

Caminho de uma API. Ex.: `https://api.openweathermap.org/data/2.5/weather?q=Brasilia&appid=KEY&units=metric&lang=pt_br`.

---

### REST

Estilo arquitetural para APIs HTTP. Recursos identificados por URL, ações por métodos HTTP (GET, POST, DELETE).

**No GastoSmart:** OpenWeather é REST. Supabase também expõe REST por baixo (o `supabase-py` consome essa REST).

---

## Termos diversos

### CLI (Command Line Interface)

Interface de usuário baseada em texto, via terminal.

**No GastoSmart:** é a única interface do MVP. Implementada em `src/app.py`.

---

### MVP (Minimum Viable Product)

Versão mínima do produto que entrega valor. No nosso caso, é o escopo da entrega final do bootcamp.

---

### Issue

Tarefa, bug ou pedido de feature registrado no GitHub. Cada PR geralmente fecha uma ou mais issues via `Closes #N`.

**No GastoSmart:** issues vivem em https://github.com/erickcmendes/gastosmart/issues.

---

### Roadmap

Plano de evolução do projeto. No nosso caso, está em [`docs/PLANO_ENTREGA_FINAL.md`](../../docs/PLANO_ENTREGA_FINAL.md) (fora do `.ai/`, é doc humano).
