# Contribuindo com o GastoSmart

Este guia existe para ajudar a equipe a trabalhar no mesmo repositório sem quebrar o fluxo de entrega.

## Fluxo recomendado

1. Atualize sua branch local a partir da `main`.
2. Crie uma branch para a tarefa, por exemplo `feature/nome-da-tarefa` ou `fix/nome-do-ajuste`.
3. Faça commits pequenos e com mensagens claras.
4. Antes de abrir PR, rode:

```bash
python -m pytest tests/ -q
python -m ruff check src/ tests/
```

5. Abra um Pull Request para a `main`.
6. Peça revisão de outro integrante.
7. Só faça merge com CI passando e aprovação de revisão.

## Regras simples para a entrega final

- Cada integrante deve abrir pelo menos 1 PR relevante.
- Cada PR deve ser revisado por outra pessoa.
- Mudanças de banco de dados devem vir com testes ou explicação clara de validação.
- O deploy e o GitHub Actions precisam continuar funcionando após cada merge.

## Segurança

- Nunca commite `.env`.
- Nunca commite chaves de API, senhas ou tokens.
- Dados locais em `data/*.json` são ignorados pelo Git.
- Use `.env.example` como referência para configurar o ambiente.

