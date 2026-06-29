# Preparação para a entrega final

Este documento separa o que foi preparado agora do que ainda deve ser desenvolvido pela equipe na entrega final.

## Objetivo desta preparação

Elevar a base atual do GastoSmart sem implementar ainda os requisitos finais. O foco deste momento é deixar o repositório mais claro, testável e colaborativo para receber quatro integrantes trabalhando por Pull Requests.

## O que fica pronto agora

- `.env.example` com variáveis esperadas.
- `.gitignore` para proteger ambiente local, cache e dados sensíveis.
- `CONTRIBUTING.md` com fluxo de colaboração.
- Template de Pull Request.
- Documentação de arquitetura e desenvolvimento.
- Persistência JSON local um pouco mais robusta.
- Testes adicionais para a camada de persistência.
- Estrutura `data/` versionada sem commitar dados reais.
- Dockerfile para padronizar execução em container.

## O que ainda é requisito da entrega final

### Trabalho em equipe

- Definir integrantes oficiais.
- Convidar todos como colaboradores do repositório.
- Criar issues para dividir o trabalho.
- Garantir pelo menos 1 PR por integrante.
- Fazer revisão cruzada entre integrantes.

### Banco de dados em nuvem

A aplicação não deve continuar dependendo apenas de JSON local na versão final.

Opções possíveis:

- Supabase PostgreSQL.
- Neon PostgreSQL.
- MongoDB Atlas.
- Firebase.

Recomendação inicial para este projeto: **Supabase ou Neon com PostgreSQL**, porque o domínio de gastos se encaixa bem em tabelas relacionais e facilita consultas por categoria, data e total.

### Qualidade

- Manter `pytest` cobrindo regras principais.
- Manter `ruff` no CI.
- Criar testes para a camada de banco escolhida.
- Evitar testes que dependam de dados reais ou credenciais pessoais.

### Deploy

- Confirmar o serviço de deploy usado.
- Configurar variáveis de ambiente no deploy.
- Validar que a versão publicada usa o banco em nuvem.
- Garantir que o CI aprove PRs antes do merge.

## Sugestão de divisão inicial de issues

- Configurar banco em nuvem e documentar variáveis.
- Criar camada de repositório para gastos.
- Migrar comandos da CLI para usar a nova camada de persistência.
- Criar testes unitários da camada de negócio com mock do repositório.
- Criar testes de integração controlados para o banco.
- Atualizar deploy com variáveis do banco.
- Atualizar README com instruções finais.

## Cuidados importantes

- Não commitar chaves do banco.
- Não usar credenciais pessoais em testes automatizados.
- Manter PRs pequenos para facilitar review.
- Fazer merge somente com CI passando.
- Registrar decisões técnicas na documentação.

