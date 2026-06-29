# Issues prontas para o GitHub

> **Status: HISTÓRICO.** Estas issues foram criadas no GitHub durante o desenvolvimento e estão todas **fechadas** após o merge dos PRs correspondentes. Documento mantido como registro do planejamento inicial. Para o resumo do que foi entregue, ver [`PREPARACAO_ENTREGA_FINAL.md`](PREPARACAO_ENTREGA_FINAL.md).

---

Copia e cola cada bloco como uma nova issue em `https://github.com/erickcmendes/gastosmart/issues`. Os números aqui (#1..#7) são apenas referência interna — o GitHub atribui o número real ao criar.

Sugestão de labels a criar antes: `infra`, `backend`, `testes`, `docs`, `deploy`, `boa-primeira-tarefa`.

---

## Issue #1 — Configurar conexão com Supabase

**Labels:** `infra`, `backend`
**Responsável sugerido:** Erick
**Branch:** `feature/supabase-config-e-repository`

### Descrição
Adicionar dependências e código mínimo para conectar a aplicação ao projeto Supabase já provisionado (`https://jqetggonptxjqjpapjps.supabase.co`).

### Tarefas
- [ ] Adicionar `supabase` e `python-dotenv` ao `requirements.txt`
- [ ] Criar `src/config.py` com função `get_supabase_client()` que lê `SUPABASE_URL` e `SUPABASE_KEY` do ambiente
- [ ] Atualizar `.env.example` com as duas variáveis (sem valores reais)
- [ ] Documentar no README a etapa "configure seu `.env`"

### Critério de aceite
- `python -c "from src.config import get_supabase_client; print(get_supabase_client())"` retorna um client válido quando `.env` está configurado
- Sem `.env` configurado, levanta erro claro

---

## Issue #2 — Criar camada de repositório para gastos

**Labels:** `backend`
**Responsável sugerido:** Erick
**Branch:** `feature/supabase-config-e-repository`
**Depende de:** #1

### Descrição
Encapsular o acesso ao Supabase em `src/repository.py`. A camada de negócio nunca deve conhecer o cliente Supabase diretamente.

### Tarefas
- [ ] Criar `src/repository.py` com funções: `inserir(gasto)`, `listar()`, `remover_por_id(id)`
- [ ] Schema da tabela `gastos` aplicado no Supabase (ver `docs/supabase/schema.sql`)
- [ ] Testes unitários em `tests/test_repository.py` usando mock do client
- [ ] Documentar no `docs/ARCHITECTURE.md` a nova camada

### Critério de aceite
- Testes do repositório passam sem rede
- Inserir um registro real via REPL aparece na tabela `gastos` do Supabase

---

## Issue #3 — Migrar regras de negócio para `src/services.py`

**Labels:** `backend`, `refatoração`
**Responsável sugerido:** Lucas
**Branch:** `feature/migrar-services-para-supabase`
**Depende de:** #1, #2

### Descrição
Extrair as funções `adicionar_gasto`, `listar_gastos`, `remover_gasto`, `resumo_gastos` de `src/app.py` para `src/services.py`, fazendo-as usar o `repository` em vez de JSON local.

### Tarefas
- [ ] Criar `src/services.py` com as 4 funções acima
- [ ] Manter validações existentes (descrição vazia, valor zero/negativo, categoria inválida)
- [ ] Substituir uso direto no `src/app.py` para importar de `services`
- [ ] Remover (ou marcar como legado) `carregar_gastos`/`salvar_gastos` do JSON

### Critério de aceite
- `tests/test_services.py` passa com repositório mockado
- App roda interativamente e adiciona/remove gastos no Supabase

---

## Issue #4 — Manter integração com OpenWeather

**Labels:** `backend`, `boa-primeira-tarefa`
**Responsável sugerido:** Lucas
**Branch:** `feature/migrar-services-para-supabase`
**Depende de:** #3

### Descrição
Garantir que `buscar_clima` continua funcional após a refatoração. Sem `OPENWEATHER_API_KEY`, o resumo segue rodando sem clima.

### Tarefas
- [ ] Mover `buscar_clima` para `src/services.py` (ou um `weather.py` separado)
- [ ] Garantir teste existente de mock do OpenWeather continua verde

### Critério de aceite
- Todos os testes legados de clima permanecem passando

---

## Issue #5 — Atualizar suíte de testes e CI

**Labels:** `testes`, `infra`
**Responsável sugerido:** João
**Branch:** `feature/testes-suite-banco`
**Depende de:** #2

### Descrição
Adaptar testes existentes para a nova arquitetura e adicionar bateria de integração opcional contra o Supabase real.

### Tarefas
- [ ] Atualizar `tests/test_app.py` para usar mocks da camada de serviços
- [ ] Criar `tests/test_integration_supabase.py` com `pytest.mark.skipif(not os.getenv("SUPABASE_URL"), ...)`
- [ ] Adicionar job opcional no `.github/workflows/ci.yml` para rodar integração só em push na `main` usando `secrets.SUPABASE_URL` e `secrets.SUPABASE_KEY`
- [ ] Documentar como rodar localmente

### Critério de aceite
- `pytest tests/ -q` passa sem `.env` (pula integração)
- `pytest tests/ -q` com `.env` configurado roda também a integração
- CI verde na `main`

---

## Issue #6 — Atualizar deploy no Render com Supabase

**Labels:** `deploy`, `docs`
**Responsável sugerido:** Cauã
**Branch:** `feature/deploy-render-e-readme`
**Depende de:** #3

### Descrição
Configurar as variáveis de ambiente do Supabase no Render e validar que `https://gastosmart-3nje.onrender.com` está rodando a nova versão conectada ao banco.

### Tarefas
- [ ] Adicionar `SUPABASE_URL` e `SUPABASE_KEY` como Environment Variables no Render
- [ ] Trigger de deploy manual após merge
- [ ] Criar `docs/DEPLOY.md` documentando o passo a passo (com prints opcionais)
- [ ] Validar adicionando um gasto via app implantado e conferindo no Supabase

### Critério de aceite
- App publicado lê e escreve no Supabase
- README aponta para o link funcional

---

## Issue #7 — README final + PDF de entrega

**Labels:** `docs`
**Responsável sugerido:** Cauã
**Branch:** `feature/deploy-render-e-readme`
**Depende de:** #6

### Descrição
Atualizar README com os 4 integrantes, nova stack e link de deploy. Preparar o conteúdo do PDF que Erick vai submeter na plataforma.

### Tarefas
- [ ] Atualizar seção "Tecnologias" do README incluindo Supabase / supabase-py
- [ ] Atualizar seção "Autores" confirmando matrículas e GitHub de cada um
- [ ] Garantir que o link de deploy no topo do README está correto
- [ ] Criar `docs/PDF_ENTREGA.md` com: nome + matrícula dos 4 integrantes, nome do projeto, descrição, link do repo, link do deploy

### Critério de aceite
- PDF gerado a partir de `docs/PDF_ENTREGA.md` está pronto para upload
- README contém todos os elementos exigidos no item 7 do PDF da disciplina
