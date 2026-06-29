# SRS — Especificação de Requisitos de Software

> Resumo dos requisitos funcionais e não-funcionais do GastoSmart. Mantenha sincronizado com a realidade do código. Para o histórico das decisões que originaram alguns desses requisitos, ver [`ARD.md`](ARD.md).

**Projeto:** GastoSmart
**Versão deste documento:** 1.0
**Data:** 2026-06-08
**Status:** Vivo

---

## O que o sistema é

Aplicação de linha de comando para registro e controle de gastos pessoais. O usuário interage via menu textual, insere gastos com descrição/valor/categoria/data, lista os existentes, remove pelo ID e visualiza um resumo agregado por categoria. Dados são persistidos em PostgreSQL hospedado no Supabase.

**Usuários-alvo:** pessoas físicas querendo controle simples de orçamento; estudantes praticando Python; equipe avaliadora do bootcamp.

**Não-objetivos:** não é um sistema multiusuário com login, não é uma API REST, não tem frontend web. Esses são extensões futuras (ver [`ARD.md`](ARD.md) e [`architecture.md`](../architecture.md)).

---

## Requisitos Funcionais

| FR | Prioridade | Resumo | Critério de aceite |
|---|---|---|---|
| **FR-01** | MVP | Adicionar gasto persistindo no Supabase | Após chamar `services.adicionar_gasto`, a linha aparece em `SELECT * FROM gastos` no painel do Supabase com o `id` retornado. |
| **FR-02** | MVP | Listar gastos do Supabase ordenados por data desc | `services.listar_gastos()` retorna lista com mesmo conteúdo da tabela, ordenado por `data DESC`. |
| **FR-03** | MVP | Remover gasto pelo ID no Supabase | `services.remover_gasto(id)` retorna `True` se removeu, `False` se não encontrou. `listar_gastos` não devolve o item removido. |
| **FR-04** | MVP | Resumo com total geral e total por categoria | `services.resumo_gastos()` retorna `{"total": float, "por_categoria": {str: float}}` agregando os dados da tabela. |
| **FR-05** | MVP | Resumo opcionalmente exibe clima atual da cidade | Sem `OPENWEATHER_API_KEY`, o resumo funciona sem clima. Com a key válida, mostra cidade + temperatura + descrição. Em caso de erro de rede, exibe aviso (não derruba o app). |
| **FR-06** | MVP | Categorias fixas no MVP | Lista hardcoded em `src/services.py` (ou `src/app.py` enquanto não há services): `Alimentação`, `Transporte`, `Saúde`, `Lazer`, `Educação`, `Moradia`, `Outros`. Validação rejeita categorias fora dessa lista. |
| **FR-07** | MVP | Validações de entrada | `descricao` não vazia (após strip), `valor > 0`, `categoria ∈ CATEGORIAS`. Violações levantam `ValueError` com mensagem em português. |
| FR-04a | Pós-MVP | Filtrar resumo por período (mês, ano) | Sai do escopo do bootcamp. |
| FR-04b | Pós-MVP | Editar gasto existente | Sai do escopo do bootcamp. |
| FR-04c | Pós-MVP | Importar gastos via CSV | Sai do escopo do bootcamp. |
| FR-04d | Pós-MVP | Multiusuário com autenticação | Sai do escopo do bootcamp. |

---

## Requisitos Não-Funcionais

| NFR | Prioridade | Requisito | Como verificar |
|---|---|---|---|
| **NFR-01** | MVP | Aplicação não armazena credenciais no código | `git ls-files | grep .env` retorna apenas `.env.example`. `.env` é ignorado. |
| **NFR-02** | MVP | Testes unitários rodam sem rede e sem banco real | `pytest tests/ -q` passa em máquina sem `.env` e sem internet. |
| **NFR-03** | MVP | Testes de integração contra Supabase real são opcionais | `pytest.mark.skipif` pula testes quando `SUPABASE_URL` não está setada. |
| **NFR-04** | MVP | Tempo de resposta da CLI < 2s por operação | Limite prático do plano free do Supabase. Validar manualmente. |
| **NFR-05** | MVP | Compatibilidade com Python 3.11 | CI roda em 3.11; Dockerfile usa `python:3.11-slim`. |
| **NFR-06** | MVP | CI verde antes de qualquer merge na `main` | Workflow `quality` precisa estar com check verde no PR. |
| **NFR-07** | MVP | Deploy no Render mantém-se acessível | https://gastosmart-3nje.onrender.com responde com a CLI funcional após cada push em `main`. |
| **NFR-08** | MVP | Cada integrante abre ≥1 PR revisado e mergeado | Critério da barema da disciplina. Auditoria via aba "Pull Requests" do repo. |
| **NFR-09** | MVP | Nenhuma credencial aparece em logs, prints ou mensagens de erro | Auditoria manual nos PRs e na CLI. |
| **NFR-10** | MVP | `.ai/` é mantida sincronizada com o estado do projeto | Toda PR que muda código também atualiza arquivo(s) em `.ai/` correspondentes (Regra Dura + checklist). |

---

## Constraints

- **Plano free do Supabase:** pode pausar o projeto após inatividade. A equipe precisa reativar manualmente no painel se isso acontecer durante a avaliação.
- **Plano free do Render:** "cold start" possível após inatividade — a primeira execução pode demorar até 30s.
- **OpenWeather:** dependência opcional; quando indisponível, app continua funcional sem clima.
- **Disciplina (Bootcamp II — CEUB):** prazo final **14/06/2026 às 23:55**. Entrega via PDF na plataforma SalaOnline.

---

## Out of Scope (entrega final do bootcamp)

- Login / cadastro / sessão de usuário.
- Edição de gastos (apenas add, list, remove, summarize).
- Filtros temporais avançados no resumo.
- Categorias customizáveis pelo usuário.
- Importação ou exportação de dados (CSV, OFX, JSON estruturado).
- API REST / webhooks / agendamentos.
- Frontend web ou mobile.
- Notificações por email ou push.
- Internacionalização (app é só em português brasileiro).
- Migrations versionadas (Alembic). O `schema.sql` é aplicado manualmente uma vez no Supabase.

---

## Critérios da barema (rastreamento de cobertura)

Mapeamento direto da barema do PDF da disciplina para requisitos:

| Critério da barema | Requisitos cobertos |
|---|---|
| Integração com Banco de Dados | FR-01, FR-02, FR-03, FR-04 + NFR-04, NFR-07 |
| Trabalho em equipe e PRs | NFR-08 |
| Manutenção da qualidade (CI + testes) | NFR-02, NFR-03, NFR-06 |
| Deploy funcional | NFR-07 |
| Documentação (README) | (não é requisito de produto, é entrega) — coberto no PR-04 |
| Formato da entrega (PDF) | (não é requisito de produto) — coberto no PR-04 |

---

## Glossário rápido (versão completa em `glossario-negocio.md`)

- **Gasto:** registro individual de uma despesa, contendo descrição, valor, categoria e data.
- **Categoria:** rótulo predefinido para agrupar gastos no resumo.
- **Resumo:** agregação dos gastos exibindo total geral e total por categoria.
