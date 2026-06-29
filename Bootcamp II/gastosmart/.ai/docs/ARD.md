# ARD — Registros de Decisões de Arquitetura

> ADR (Architecture Decision Records) do GastoSmart. Cada decisão tem **contexto, decisão, alternativas consideradas e consequências**. Sempre que uma nova decisão for tomada, adicione um AD-NN abaixo no mesmo PR que a introduz (mandato em `config/system.md`).

**Projeto:** GastoSmart
**Versão deste documento:** 1.0
**Data:** 2026-06-08
**Status:** Vivo (atualizado a cada decisão nova)

---

## Resumo das decisões

| AD | Tópico | Decisão | Status |
|---|---|---|---|
| AD-01 | Linguagem do backend | Python 3.11+ | Aceita |
| AD-02 | Interface | CLI interativa via terminal | Aceita |
| AD-03 | Banco de dados | PostgreSQL hospedado no Supabase | Aceita |
| AD-04 | Cliente do banco | `supabase-py` ao invés de `psycopg2` direto | Aceita |
| AD-05 | Padrão arquitetural | 3 camadas: CLI → Services → Repository | Aceita |
| AD-06 | Plataforma de deploy | Render (Web Service via Dockerfile) | Aceita |
| AD-07 | CI/CD | GitHub Actions | Aceita |
| AD-08 | Container | Docker baseado em `python:3.11-slim` | Aceita |
| AD-09 | Integração externa de clima | OpenWeather API (opcional, com fallback) | Aceita |
| AD-10 | Segurança no MVP | RLS aberto para `anon` na tabela `gastos` | Aceita (temporário) |
| AD-11 | Estratégia de testes | Unit com mock por padrão; integração opcional via `skipif` | Aceita |
| AD-12 | Gerenciamento de env | `python-dotenv` + `.env.example` versionado | Aceita |
| AD-13 | Estratégia de merge | Squash and merge via PR; nunca commit direto na `main` | Aceita |
| AD-14 | Manutenção do `.ai/` | Mandato de auto-atualização pela IA | Aceita |
| AD-15 | Interface Web | Streamlit (`src/app_web.py`) coexistindo com a CLI | Aceita |
| AD-16 | Nome da variável da chave Supabase | `SUPABASE_PUB_KEY` (com fallback para `SUPABASE_KEY` legado) | Aceita |

---

## AD-01 — Python como linguagem principal

**Contexto:** projeto começou em Python desde a Etapa 1 do bootcamp, com integração ao OpenWeather já implementada.

**Decisão:** manter Python 3.11+ por toda a entrega final.

**Alternativas consideradas:**
- Reescrever em Node.js: descartado por exigir refazer toda a base e perder o histórico de commits e PRs anteriores.
- Adotar Python 3.12+: descartado para garantir compatibilidade com a imagem Docker do Render (`python:3.11-slim` é estável).

**Consequências:**
- Stack de testes (`pytest`), lint (`ruff`) e cliente Supabase (`supabase-py`) seguem como já estavam.
- Type hints opcionais — projeto pequeno, time iniciante; tornar obrigatórios geraria fricção no aprendizado.

---

## AD-02 — Interface CLI

**Contexto:** a Etapa 1 do bootcamp pedia uma aplicação console; a entrega final permite expandir mas não exige web.

**Decisão:** manter CLI interativa em `src/app.py` como única interface.

**Alternativas consideradas:**
- Adicionar FastAPI + frontend simples: descartado por escopo. O foco da entrega final é integração com banco e trabalho em equipe via PRs, não nova interface.
- Adicionar comando não-interativo (`gastosmart add --descricao ...`): registrado como caminho futuro, não implementado.

**Consequências:**
- Curva de aprendizado da equipe permanece baixa.
- A camada de UI fica pequena, deixando espaço pra atenção em testes, CI, banco.

---

## AD-03 — PostgreSQL no Supabase

**Contexto:** entrega final exige banco de dados em nuvem. Opções comuns: Supabase, Firebase, MongoDB Atlas, Neon, PlanetScale.

**Decisão:** Supabase (PostgreSQL) como único banco do projeto.

**Alternativas consideradas:**
- **Firebase/Firestore:** descartado — modelo de dados é relacional (gastos com categoria, data, valor); NoSQL adicionaria atrito sem ganho.
- **MongoDB Atlas:** descartado pela mesma razão.
- **Neon (Postgres):** equivalente técnico ao Supabase; descartado porque o Supabase já tem painel administrativo, SQL editor e RLS prontos.
- **PlanetScale (MySQL):** descartado por preferência de Postgres da equipe e por exigir configuração de schema branching que não é necessária para o escopo.

**Consequências:**
- Dependência de plano gratuito do Supabase. **Alerta:** o free tier **pausa o projeto após ~1 semana de inatividade**. Reativação é manual no painel.
- Auth e Storage do Supabase ficam disponíveis para extensões futuras.

---

## AD-04 — `supabase-py` ao invés de `psycopg2` direto

**Contexto:** existem duas formas de conectar a aplicação ao Postgres do Supabase.

**Decisão:** usar `supabase-py` (`pip install supabase`).

**Alternativas consideradas:**
- **`psycopg2` + connection string Postgres:** descartado porque exigiria expor a connection string completa (mais sensível que a `publishable key`), e complica a configuração no Render (variável separada, sem proteção do RLS).
- **`SQLAlchemy`:** descartado por overhead — apenas uma tabela, sem necessidade de ORM.

**Consequências:**
- Operações CRUD seguem o estilo fluente do `supabase-py`:
  `client.table("gastos").insert(...).execute()`.
- Encapsulamento na `src/repository.py` mantém troca futura barata (se for trocar por outro client, só esse módulo muda).

---

## AD-05 — Arquitetura em 3 camadas (CLI → Services → Repository)

**Contexto:** o estado anterior misturava regras de negócio com persistência em `src/app.py`. Para a entrega final, precisamos separar para facilitar testes e divisão de tarefas entre 4 integrantes.

**Decisão:** introduzir explicitamente três camadas:

1. `src/app.py` — apresentação (menus, prompts, prints).
2. `src/services.py` — regras de negócio, validações, agregações.
3. `src/repository.py` — único módulo que importa `supabase-py`.

**Alternativas consideradas:**
- Manter tudo em `app.py`: descartado, dificultaria PRs paralelos e testes com mock.
- Adotar arquitetura hexagonal completa (ports/adapters): descartado por overhead para o escopo.

**Consequências:**
- Cada PR do time fica naturalmente delimitado em uma camada.
- A regra "nada importa `supabase` fora do repository" é fácil de auditar (Regra Dura #6).

---

## AD-06 — Render para deploy

**Contexto:** entrega final exige hospedagem acessível por link.

**Decisão:** continuar com Render (já configurado desde a Etapa 2). Web Service rodando o `Dockerfile`.

**Alternativas consideradas:**
- **Vercel:** descartado — focado em frontend; CLI Python via container não é o caso de uso natural.
- **Railway:** equivalente técnico ao Render; trocar adicionaria trabalho sem ganho.
- **Fly.io:** mesma análise.

**Consequências:**
- Auto-deploy a cada push em `main`.
- Variáveis de ambiente `SUPABASE_URL` e `SUPABASE_KEY` configuradas no painel do Render (PR-04 documenta).

---

## AD-07 — GitHub Actions para CI

**Contexto:** entrega final exige pipeline verde antes de cada merge.

**Decisão:** GitHub Actions, workflow único `quality` rodando `ruff` + `pytest` em PRs e push para `main`. A partir do PR-03, segundo job `integration` opcional contra Supabase real.

**Alternativas consideradas:**
- **GitLab CI / CircleCI / Travis:** descartados — o repo está no GitHub, ferramenta nativa.
- **Tox + Nox para matriz de versões Python:** descartado por escopo (apenas Python 3.11).

**Consequências:**
- Jobs simples, fáceis de manter.
- Integração com Supabase em CI só roda em `main` para evitar expor `secrets` em PRs vindos de forks.

---

## AD-08 — Docker baseado em `python:3.11-slim`

**Contexto:** padronizar execução local e no Render.

**Decisão:** `Dockerfile` minimal copiando `src/` e instalando `requirements.txt`.

**Alternativas consideradas:**
- **`python:3.11-alpine`:** descartado pela complicação com algumas wheels (especialmente `cryptography` indireta do `supabase-py`).
- **Sem Docker, deploy direto via runtime Python do Render:** descartado pra manter paridade local ↔ produção.

**Consequências:**
- Build do container é rápido (~30s).
- `data/.gitkeep` é copiado para a imagem, mas a pasta `data/` perde relevância após PR-2.

---

## AD-09 — OpenWeather API como integração opcional

**Contexto:** etapa anterior introduziu integração com OpenWeather no resumo. A entrega final não exige manter, mas remover seria perder funcionalidade já validada.

**Decisão:** manter OpenWeather como integração **opcional**. Sem `OPENWEATHER_API_KEY`, o resumo segue funcionando sem clima.

**Alternativas consideradas:**
- Remover: descartado, perderia testes e contexto da etapa anterior.
- Trocar por API gratuita sem key (ex.: wttr.in): registrado como caminho futuro, não prioritário.

**Consequências:**
- `src/weather.py` isola a integração a partir do PR-02 (atualmente está em `src/app.py`).
- Testes usam mock de `urllib.request.urlopen`.

---

## AD-10 — RLS aberto para `anon` no MVP

**Contexto:** sem login de usuário, qualquer cliente com a `publishable key` pode operar. Manter RLS desativado funcionaria, mas RLS desligado em projeto Supabase é um cheiro ruim (e o painel reclama).

**Decisão:** ativar RLS na tabela `gastos` com 4 políticas abertas para a role `anon` (select, insert, update, delete).

**Alternativas consideradas:**
- **RLS desativado:** descartado por boa prática.
- **Autenticação por usuário** (`auth.uid()`): registrado como caminho futuro em "Pontos de extensão" (`architecture.md`). Exigiria tabela `users`, fluxo de login na CLI, e tabela `gastos` com `user_id`. Fora de escopo do bootcamp.

**Consequências:**
- Qualquer pessoa com a key consegue ler/escrever todos os gastos do projeto. Aceitável no contexto acadêmico (dados de teste).
- Documentado claramente em `architecture.md` para que avaliadores saibam que é temporário.

---

## AD-11 — Testes: unit com mock por padrão, integração opcional

**Contexto:** rodar testes contra Supabase real em PRs de forks expõe `secrets`. Rodar em todos os PRs aumenta o risco de instabilidade.

**Decisão:**

- **Unit:** sempre com mock do client (`MagicMock`). Sem rede, sem credenciais. Rodam em todo PR.
- **Integração com Supabase:** marcados com `pytest.mark.skipif(not os.getenv("SUPABASE_URL"), ...)`. Rodam só em push para `main` em ambiente com `secrets` configurados.

**Alternativas consideradas:**
- **Sempre integração:** descartado pelos motivos acima.
- **Sempre mock:** descartado — perderia confiança de que a query real funciona.
- **Supabase local com Docker:** registrado como caminho futuro; complicaria a CI sem ganho proporcional no escopo do bootcamp.

**Consequências:**
- Build da CI mantém-se rápido.
- Bugs específicos de SQL ou políticas RLS aparecem apenas no smoke test manual + no push em `main`.

---

## AD-12 — `python-dotenv` + `.env.example` versionado

**Contexto:** desenvolvedores precisam de uma forma simples de configurar credenciais localmente.

**Decisão:** usar `python-dotenv` em `src/config.py` para carregar `.env` automaticamente. `.env` no `.gitignore`. `.env.example` versionado com placeholders.

**Alternativas consideradas:**
- **`os.environ` puro:** descartado — exigiria scripts `export` manuais ou plug-ins de IDE.
- **`pydantic-settings`:** descartado por overhead para o escopo.

**Consequências:**
- Em produção (Render, GitHub Actions), as variáveis vêm do ambiente real. `python-dotenv` importa silenciosamente se não houver `.env`.
- Atualização do `.env.example` é Regra Dura #3 sempre que adicionar var nova.

---

## AD-13 — Squash and merge via PR; nunca commit direto na `main`

**Contexto:** durante o desenvolvimento do PR-01, um commit foi feito direto na `main` por engano. Foi revertido com `git revert` e reaberto via PR.

**Decisão:** **proibir commits diretos em `main`**. Tudo via PR com revisão de outro integrante. Estratégia de merge: **Squash and merge** para manter o histórico linear e cada feature como um único commit.

**Alternativas consideradas:**
- **Rebase and merge:** descartado, complica para iniciantes.
- **Merge commit normal:** descartado, polui o histórico com merges automáticos.

**Consequências:**
- Configurar "Branch protection rules" para `main` no GitHub (futuro). Por enquanto a regra é apenas social/documental.
- A nota individual do bootcamp depende disso — cada integrante precisa ter um PR mergeado vinculado ao seu user GitHub.

---

## AD-15 — Streamlit como interface web (coexistindo com a CLI)

**Contexto:** o deploy no Render simplesmente não estava funcionando rodando a CLI Python pura. O container subia mas a interface não era usável pela web (CLI espera `stdin` interativo, o que Render Web Service não fornece). Isso bloqueou a validação da entrega final por dias.

**Decisão:** adicionar uma **segunda interface** via Streamlit (`src/app_web.py`) que reaproveita 100% da camada de `services` e `repository`. A CLI continua existindo para uso local. O Render passa a rodar `streamlit run src/app_web.py --server.port 8501 --server.address 0.0.0.0`.

**Alternativas consideradas:**
- **Trocar Render por outra plataforma** (Railway, Fly.io): descartado pelo tempo; o time já tinha conta e variáveis configuradas no Render.
- **Construir uma API REST com FastAPI** e um frontend separado: descartado pelo escopo e prazo da entrega final.
- **Gradio em vez de Streamlit:** equivalente técnico; Streamlit foi escolhido pela familiaridade da comunidade brasileira e por ter dataframes/charts nativos suficientes para o caso de uso.

**Consequências:**
- `requirements.txt` ganha `streamlit`.
- `Dockerfile` muda o `CMD` para iniciar o Streamlit, expõe porta 8501.
- O time mantém duas interfaces. Mudanças de regra de negócio acontecem em um lugar (services) e propagam pras duas.
- Ambas dependem do mesmo `OPENWEATHER_API_KEY` quando opcional.
- Decisão executada pelos integrantes Erick (solicitação) e Lucas (implementação), entregue no PR #13.

---

## AD-16 — `SUPABASE_PUB_KEY` como nome canônico da variável

**Contexto:** durante o desenvolvimento, surgiu inconsistência entre nomes da chave Supabase no projeto. O `.env.example` foi atualizado para `SUPABASE_PUB_KEY` (refletindo nomenclatura mais clara — é a *publishable* key, não a service role), mas `src/config.py` ainda lia `SUPABASE_KEY`, causando potencial falha de boot pra qualquer dev novo clonando o repo.

**Decisão:** padronizar **`SUPABASE_PUB_KEY`** como nome oficial em todo o projeto:

- `.env.example`
- `src/config.py` (com fallback para `SUPABASE_KEY` por compatibilidade com setups antigos)
- README
- Painel do Render (variável de ambiente do serviço)
- Secrets do GitHub Actions (se forem usados em PR-3 de integração)
- Toda documentação do `.ai/`

**Alternativas consideradas:**
- **Padronizar `SUPABASE_KEY`** (mais curto, era o original): descartado por ambiguidade — Supabase tem múltiplas chaves (anon/publishable e service_role), e o nome neutro pode levar a alguém colocar a chave errada (com permissões maiores) por engano.
- **Padronizar `SUPABASE_ANON_KEY`**: equivalente, mas o termo "pub" (publishable) é o que aparece no painel Supabase mais recente, então alinhamos com a fonte.

**Consequências:**
- `config.py` aceita ambas no curto prazo (fallback) pra não quebrar workflows.
- Em PR futuro, remover o fallback quando todos os ambientes estiverem migrados.
- Regra Dura #11 adicionada em `config/system.md` exigindo sincronia entre todos os locais.

---

## AD-14 — Manutenção viva do `.ai/`

**Contexto:** sem disciplina, pastas de contexto para IA viram artefatos mortos. A IA passa a operar com informação obsoleta.

**Decisão:** declarar o **Mandato de Auto-Atualização** em `config/system.md` (seção dedicada). Toda IA é responsável por atualizar o `.ai/` quando o projeto mudar — incluindo links de issues/PRs novos.

**Alternativas consideradas:**
- Atualização manual por humanos: descartado, ninguém vai lembrar.
- Pré-commit hook que valida coerência: registrado como caminho futuro; demanda esforço de implementação.

**Consequências:**
- Cada PR que muda código deve incluir mudanças no `.ai/` correspondentes.
- O Checklist em `coding_conventions.md` traz isso como item obrigatório antes do commit.
- Em PRs apenas de manutenção do `.ai/`, usar `chore(.ai):` como tipo do commit.
