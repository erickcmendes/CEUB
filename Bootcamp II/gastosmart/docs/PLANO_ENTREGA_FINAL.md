# Plano de Execução — Entrega Final (Bootcamp II)

Documento mestre para destravar a Etapa 3 do GastoSmart. Resume estado atual, requisitos do PDF, arquitetura alvo, divisão de PRs entre os 4 integrantes, riscos e checklist de aceite.

---

## 1. Estado atual do repositório

| Item | Situação | Observação |
|---|---|---|
| App Python CLI (`src/app.py`) | OK | Persistência em JSON local |
| Testes (`tests/test_app.py`) | OK, 18+ casos | Não cobrem banco em nuvem |
| CI GitHub Actions | Verde | Roda `ruff` e `pytest` em PRs/main |
| Deploy Render | Publicado | https://gastosmart-3nje.onrender.com (rodando JSON local) |
| Docker | Pronto | `Dockerfile` para Python 3.11-slim |
| `.env.example` | Pronto | Só com chaves OpenWeather e arquivo local |
| Branches | `main`, `entrega-intermediaria` | `entrega-intermediaria` está atrás de `main` (já mergeada) |
| Colaboradores no GitHub | A confirmar | Convidar Lucas, João e Cauã se ainda não feito |
| Banco em nuvem | **Faltando integração** | Projeto Supabase já criado (URL e key fornecidos) |
| Issues no GitHub | Nenhuma | Criar 7 issues a partir deste plano |

> Aviso: o `git status` mostra 6 arquivos modificados não commitados, mas o diff é só normalização CRLF/LF. Antes de criar branches, rode `git checkout -- .` ou configure `git config core.autocrlf true` para evitar PRs poluídos.

---

## 2. Requisitos do PDF mapeados para entregáveis

| Critério da barema | Como provamos |
|---|---|
| **Integração com BD** | App lê/grava na tabela `gastos` no Supabase. Demonstrável via `python src/app.py` apontando para `.env` com `SUPABASE_URL` e `SUPABASE_KEY` |
| **Trabalho em equipe e PRs** | 4+ PRs, um por integrante, cada PR revisado por outro membro. Histórico de issues fechadas |
| **Manutenção da qualidade** | CI verde no merge da `main`. Suite de testes inclui mocks do client Supabase |
| **Deploy funcional** | Render atualizado e conectado ao Supabase via secrets. Link no README e no PDF de entrega |
| **README** | Lista de integrantes, nova stack (Supabase + supabase-py), instruções de rodar local, link de deploy |
| **PDF de entrega** | Erick envia. Contém nomes/matrículas, link do repo, link do deploy |

---

## 3. Engenharia de requisitos

### 3.1 Requisitos funcionais

| ID | Requisito | Critério de aceite |
|---|---|---|
| RF-01 | Adicionar gasto persistindo em Supabase | Após chamar `adicionar_gasto`, a linha aparece em `SELECT * FROM gastos` no Supabase |
| RF-02 | Listar gastos do Supabase | `listar_gastos()` retorna lista com mesmo conteúdo do banco |
| RF-03 | Remover gasto por ID no Supabase | `DELETE` físico ou flag `ativo=false`; `listar_gastos` não retorna o item |
| RF-04 | Resumo continua funcionando com dados do banco | `resumo_gastos()` agrega `valor` por `categoria` lendo do banco |
| RF-05 | OpenWeather continua opcional no resumo | Sem chave: resumo segue funcionando; com chave: mostra clima |

### 3.2 Requisitos não funcionais

- **RNF-01** Sem credenciais commitadas. Tudo via `.env` local e secrets do Render/GitHub Actions.
- **RNF-02** Testes unitários rodam sem rede e sem banco real (mock do client).
- **RNF-03** Testes de integração com Supabase são opcionais e só rodam quando `SUPABASE_URL` está presente (skip caso contrário) — para o CI continuar verde sem expor segredos.
- **RNF-04** Tempo de resposta da CLI < 2s por operação (limite prático do plano free do Supabase).
- **RNF-05** Compatível com Python 3.11 (versão do CI e do Render).

### 3.3 Fora de escopo desta entrega

- Multiusuário com autenticação.
- API HTTP / frontend web (continua CLI).
- Migrations versionadas com Alembic.

---

## 4. Arquitetura alvo

```
┌──────────────────┐         ┌────────────────────┐         ┌──────────────────┐
│   CLI (app.py)   │ ──────▶ │  Camada de negócio │ ──────▶ │  Repositório     │
│  menu, prompts   │         │  (regras/validação)│         │  (Supabase)      │
└──────────────────┘         └────────────────────┘         └────────┬─────────┘
                                                                     │
                                                                     ▼
                                                            ┌──────────────────┐
                                                            │ Postgres Supabase│
                                                            │  tabela: gastos  │
                                                            └──────────────────┘
```

### 4.1 Estrutura de pastas alvo

```
src/
├── app.py              # CLI (menus e prints) — fica fino
├── services.py         # Regras de negócio (validações, cálculo de resumo)
├── repository.py       # Acesso ao Supabase (CRUD)
└── config.py           # Lê variáveis de ambiente e cria client supabase

tests/
├── test_services.py    # Mock do repositório
├── test_repository.py  # Mock do client supabase
└── test_app.py         # (mantido) testes legados / smoke
```

### 4.2 Decisão técnica (mini-ADR)

**Decisão:** usar `supabase-py` (cliente oficial, `pip install supabase`) ao invés de `psycopg2` direto.

**Motivos:** API mais simples para CRUD, evita expor a connection string do Postgres, alinhado com a key `publishable` já provisionada, suporta RLS no plano free.

**Alternativas descartadas:** `psycopg2` (mais complexo de configurar no Render free), `SQLAlchemy` (overhead para 1 tabela).

---

## 5. Divisão de PRs (4 integrantes)

Cada PR deve ser **pequeno** e mergeável de forma independente, com testes próprios. Ordem sugerida segue dependências.

### PR-1 — Erick (owner do repo) — **Infra + camada de repositório**
- Branch: `feature/supabase-config-e-repository`
- Issues vinculadas: #1, #2
- Entrega:
  - Adiciona `supabase` e `python-dotenv` ao `requirements.txt`.
  - Cria `src/config.py` que carrega `.env` e expõe `get_supabase_client()`.
  - Cria `src/repository.py` com funções `inserir`, `listar`, `remover_por_id`.
  - Atualiza `.env.example` com `SUPABASE_URL` e `SUPABASE_KEY`.
  - Inclui `docs/supabase/schema.sql` (já fornecido neste plano).
  - Testes: `tests/test_repository.py` com mock do client.
- Revisor: Lucas.

### PR-2 — Lucas — **Migração da camada de negócio**
- Branch: `feature/migrar-services-para-supabase`
- Issues vinculadas: #3, #4
- Depende do PR-1 mergeado.
- Entrega:
  - Cria `src/services.py` com `adicionar_gasto`, `listar_gastos`, `remover_gasto`, `resumo_gastos` chamando o repositório.
  - `src/app.py` passa a importar de `services` (sem regra de negócio inline).
  - Mantém compatibilidade com `OPENWEATHER_API_KEY`.
  - Testes: `tests/test_services.py` com `repository` mockado.
- Revisor: João.

### PR-3 — João — **Refatorar testes + integração CI**
- Branch: `feature/testes-suite-banco`
- Issues vinculadas: #5
- Depende do PR-1 (pode iniciar em paralelo após PR-1).
- Entrega:
  - Atualiza `tests/test_app.py` para a nova arquitetura.
  - Adiciona `tests/test_integration_supabase.py` com `pytest.mark.skipif` quando `SUPABASE_URL` não está setada.
  - Adiciona job opcional no `ci.yml` para rodar a integração via `secrets` (apenas em push na `main`, não em PRs de fork).
- Revisor: Cauã.

### PR-4 — Cauã — **Deploy, README e PDF de entrega**
- Branch: `feature/deploy-render-e-readme`
- Issues vinculadas: #6, #7
- Depende dos PRs 1, 2 e 3.
- Entrega:
  - Adiciona `SUPABASE_URL` e `SUPABASE_KEY` como env vars no Render (passo manual, registrado em `docs/DEPLOY.md`).
  - Atualiza `README.md`: stack (Supabase), instruções de setup com banco, link de deploy validado.
  - Atualiza `docs/ARCHITECTURE.md` para a arquitetura alvo (3 camadas).
  - Cria `docs/PDF_ENTREGA.md` com o conteúdo que vai no PDF (nomes, matrículas, links).
- Revisor: Erick.

### Cronograma sugerido (até 14 jun 2026)

| Semana | Marco |
|---|---|
| Sem 1 (08–14 jun)... espera, prazo é 14/06 | Hoje 08/06 — criar issues, abrir PR-1 já |
| Dias 1–2 | PR-1 (Erick) revisado e mergeado |
| Dias 3–4 | PR-2 (Lucas) e PR-3 (João) em paralelo |
| Dia 5 | PR-4 (Cauã), deploy validado |
| Dia 6 | Erick envia PDF na plataforma |

---

## 6. Riscos e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Aluno não abre PR a tempo | Média | Alto (perde nota individual) | Combinar deadline interno 2 dias antes do prazo final |
| Credenciais expostas em commit | Baixa | Alto | Pre-commit + revisão obrigatória; `.env` no `.gitignore` |
| CI quebra por flake do supabase | Média | Médio | Testes de integração com `skipif`; mocks por padrão |
| Deploy Render falha ao subir | Baixa | Médio | Validar build em PR-4 antes do merge; manter Dockerfile como fallback |
| RLS do Supabase bloqueia inserts | Média | Alto | Política aberta para `anon` na tabela `gastos` enquanto não há autenticação (documentado no schema) |
| Merge conflicts entre PRs 2 e 3 | Média | Médio | Mergear PR-1 primeiro; PR-2 e PR-3 rebasam diariamente |

---

## 7. Checklist final (Definition of Done)

Antes do Erick subir o PDF, o time confere:

- [ ] 4 PRs mergeados na `main` (um por integrante)
- [ ] Cada PR tem ao menos 1 revisão aprovada por outro membro
- [ ] CI verde no último commit da `main`
- [ ] App rodando localmente lê e escreve no Supabase (testar `adicionar_gasto` e ver linha aparecer no painel)
- [ ] Deploy no Render acessível e usando o Supabase
- [ ] README com 4 integrantes, stack atualizada (Supabase) e link de deploy
- [ ] `.env` **não** está no repositório (`git ls-files | grep .env` retorna só `.env.example`)
- [ ] 7 issues criadas e fechadas (linkadas aos PRs via `Closes #N`)
- [ ] PDF de entrega gerado com: nomes completos + matrículas, descrição, link repo, link deploy
