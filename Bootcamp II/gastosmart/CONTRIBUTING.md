# Contribuindo com o GastoSmart

Guia rápido para trabalhar no repositório mantendo a integridade do projeto.

## Fluxo recomendado

1. Atualize sua branch local a partir da `main`.
2. Crie uma branch por tarefa: `feature/<descricao>`, `fix/<descricao>`, `docs/<descricao>` ou `chore/<descricao>`.
3. Faça commits pequenos com mensagens claras (Conventional Commits).
4. Antes de abrir o PR, rode os checks locais:

```bash
python -m pytest tests/ -q
python -m ruff check src/ tests/
```

5. Abra um Pull Request para a `main`.
6. Peça revisão de outro integrante.
7. Faça merge somente com CI verde e aprovação de revisão.

## Boas práticas mantidas no projeto

- Cada PR é revisado por outro integrante antes do merge.
- Mudanças de banco de dados vêm acompanhadas de testes ou explicação clara de validação.
- O deploy do Render e o pipeline do GitHub Actions são mantidos verdes após cada merge.
- Mudanças arquiteturais são registradas em `.ai/docs/ARD.md` (Architecture Decision Records).

## Segurança

- Nunca commite `.env` — apenas o `.env.example` está versionado.
- Nunca commite chaves de API, senhas ou tokens.
- Arquivos `data/*.json` são ignorados pelo Git.
- Use `.env.example` como referência para configurar o ambiente local.
