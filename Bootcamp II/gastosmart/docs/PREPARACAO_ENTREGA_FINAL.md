# Entrega Final — Resumo do que foi entregue

Este documento registra o estado final do GastoSmart na entrega da disciplina **Bootcamp II — Turma C 0226, Campus Virtual (CEUB)**. Todos os requisitos foram cumpridos e estão funcionando em produção.

## Objetivo

Construir software em equipe sobre um mesmo repositório, garantindo trabalho colaborativo via Pull Requests revisados, persistência em banco de dados em nuvem, pipeline de CI verde e deploy contínuo acessível por link público.

## Equipe

- Cauã de Godoy Araujo — matrícula 22507326 — [@Caua-Godoy](https://github.com/Caua-Godoy)
- Erick Cardoso Mendes — matrícula 22509170 — [@erickcmendes](https://github.com/erickcmendes)
- Lucas Patriota Malinski da Silva Pinto — matrícula 22452112 — [@lucasmalinski](https://github.com/lucasmalinski)
- João Vicente Burin Souza — matrícula 22501001 — [@joaovicente04](https://github.com/joaovicente04)

## Links do projeto

- **Repositório:** https://github.com/erickcmendes/gastosmart
- **Deploy (Streamlit no Render):** https://gastosmart-3nje.onrender.com

## Requisitos atingidos

### Trabalho em equipe

- Todos os integrantes foram adicionados como colaboradores do repositório.
- Cada integrante abriu, revisou e mergeou ao menos um Pull Request vinculado ao seu usuário do GitHub.
- Issues do GitHub foram usadas para dividir o trabalho e referenciadas nos PRs via `Closes #N`.
- Revisão cruzada obrigatória — nenhum PR foi mergeado sem aprovação de outro integrante.

### Banco de dados em nuvem

- **Supabase PostgreSQL** integrado como persistência oficial.
- Schema da tabela `gastos` aplicado via `docs/supabase/schema.sql`.
- Row Level Security habilitado com políticas abertas para a role `anon` (aceitável no MVP sem autenticação).
- Camada de repositório isolada em `src/repository.py` — único módulo que importa o cliente Supabase.

### Interface

- **CLI interativa** em `src/app.py` para uso local via terminal.
- **Aplicação web em Streamlit** em `src/app_web.py`, com identidade visual própria (logo, paleta verde da marca, tipografia ajustada), publicada no Render.
- Ambas as interfaces compartilham a mesma camada de serviços (`src/services.py`) e repositório.

### Qualidade

- `pytest` cobrindo regras de negócio (`tests/test_services.py`), camada de repositório com mock (`tests/test_repository.py`) e delegação do app para os serviços (`tests/test_app.py`).
- `ruff` configurado em `pyproject.toml` e rodando no CI.
- Pipeline do GitHub Actions (`.github/workflows/ci.yml`) executa lint e testes em todo push e pull request para a `main`.
- Nenhum teste depende de dados reais ou credenciais pessoais — todos os mocks isolam I/O.

### Deploy

- **Render** hospeda o serviço web rodando Streamlit em container Docker.
- Variáveis de ambiente (`SUPABASE_URL`, `SUPABASE_PUB_KEY`, `OPENWEATHER_API_KEY`) configuradas no painel do Render.
- Auto-deploy a cada push para a `main`, com CI obrigatoriamente verde antes do merge.
- Versão publicada lê e escreve no Supabase em tempo real.

### Documentação

- `README.md` atualizado com stack final (Supabase, Streamlit, etc.), instruções de setup e link de deploy.
- `docs/ARCHITECTURE.md` e `docs/DEVELOPMENT.md` mantidos consistentes com o código.
- `docs/PDF_ENTREGA.md` com o conteúdo da submissão.
- `docs/supabase/CONFIGURACAO.md` com o passo a passo do banco.
- Pasta `.ai/` com contexto estruturado para IAs copilotas (arquitetura, decisões, requisitos, padrões de código, glossários e fluxos de trabalho), facilitando onboarding e manutenção futura.

## Pull Requests entregues

| PR | Responsável | Descrição |
|---|---|---|
| #3 | Erick | Infraestrutura Supabase e camada de repositório |
| #9 | Lucas | Migração da camada de serviços para o Supabase |
| #10 | João | Testes adicionais e ajustes no pipeline de CI |
| #11 | Cauã | Deploy no Render, README final e documentação |
| #13 | Erick & Lucas | Interface web em Streamlit publicada no Render |
| #14 | Erick | Sincronização do contexto `.ai/` e padronização de variáveis |

## Cuidados aplicados durante o desenvolvimento

- Nenhuma chave de banco ou credencial foi commitada — apenas o `.env.example` está versionado.
- Testes automatizados não dependem de credenciais ou rede.
- PRs mantidos pequenos para facilitar revisão.
- Merge somente após CI verde e aprovação de outro integrante.
- Decisões técnicas registradas em `.ai/docs/ARD.md` (Architecture Decision Records).
