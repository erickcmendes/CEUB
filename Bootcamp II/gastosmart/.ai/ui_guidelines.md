# UI Guidelines — CLI

> O GastoSmart é uma aplicação de **linha de comando**. Não há interface gráfica. Este documento define padrões visuais e de interação no terminal. Para o design detalhado das telas, ver [`docs/design-doc.md`](docs/design-doc.md).

---

## Princípios

1. **Clareza acima de elegância.** Mensagens devem ser inequívocas. Se houver dúvida entre "bonito" e "claro", escolha claro.
2. **Idioma:** **português brasileiro** em todas as mensagens, prompts, erros e nomes de categoria visíveis ao usuário.
3. **Feedback imediato.** Toda ação do usuário gera resposta visual no terminal: confirmação de sucesso, mensagem de erro, ou aviso.
4. **Não assuma terminal colorido.** O design usa caracteres ASCII + emojis Unicode. Não use sequências ANSI de cor sem detecção de suporte.
5. **Largura segura:** quebrar tabelas para caber em 80 colunas.

---

## Iconografia (emojis)

| Emoji | Uso |
|---|---|
| 💸 | Logo / cabeçalho do app |
| 💰 | Boas-vindas iniciais |
| ✅ | Operação bem-sucedida (gasto adicionado, removido) |
| ❌ | Erro de validação ou operação que falhou |
| ⚠️ | Aviso não-crítico (ex.: clima indisponível) |
| 📍 | Localização no resumo de clima |
| 🌡️ | Temperatura no resumo de clima |
| 👋 | Despedida ao sair do app |
| 📊 | Resumo / estatísticas |
| 📝 | Operação que altera dados (adicionar, editar) |
| 🗑️ | Remoção |

**Regra:** no máximo 1 emoji por linha de output. Não polua.

---

## Separadores

```
========================================         # cabeçalho principal (40 = ou =)
----------------------------------------         # separador de seção (40 -)
──                                                # separador interno fino (caractere Box Drawing)
```

A linha de 40 caracteres é o padrão atual do `src/app.py`. Manter consistente.

---

## Cabeçalho do menu principal

```
========================================
       💸 GastoSmart v1.1.0
========================================
  [1] Adicionar gasto
  [2] Listar gastos
  [3] Remover gasto
  [4] Ver resumo
  [0] Sair
========================================
```

Versão exibida vem do `__version__` ou do `pyproject.toml`. Atualizar a cada release.

---

## Prompts de entrada

Padrão:

```
Descrição: _
Valor (R$): _
```

Regras:

- Sufixo `:` seguido de **um espaço** antes da entrada do usuário.
- Sem emoji nos prompts.
- Unidades em parênteses quando aplicável (`Valor (R$)`, `Data (AAAA-MM-DD)`).
- Após erro de validação, **re-pedir o mesmo campo** sem voltar ao menu.

Exemplo de loop de validação (já implementado em `input_valor`):

```
Valor (R$): abc
❌ Digite um número válido.
Valor (R$): -5
❌ O valor deve ser maior que zero.
Valor (R$): 35.50
```

---

## Mensagens de sucesso

Formato:

```
✅ <verbo no passado> <descrição curta> <dado relevante>
```

Exemplos:

```
✅ Gasto adicionado! ID #12 — Almoço — R$ 35.50
✅ Gasto #12 removido com sucesso.
```

---

## Mensagens de erro

Formato:

```
❌ <descrição do problema em português, frase completa, com ponto final>
```

Exemplos:

```
❌ A descrição não pode ser vazia.
❌ O valor deve ser maior que zero.
❌ Categoria inválida. Escolha entre: Alimentação, Transporte, Saúde, ...
❌ Gasto #99 não encontrado.
```

Regras:

- Frase completa, **com sujeito implícito ou explícito** (não `Inválido!`).
- Ponto final obrigatório.
- Sem stack trace exposto ao usuário (a menos que seja modo de debug).

---

## Avisos não-críticos

Formato:

```
⚠️  <descrição do que aconteceu e o que isso significa pro usuário>
```

Exemplo:

```
⚠️  Não foi possível obter o clima no momento.
```

Note o **espaço duplo** após o emoji ⚠️ — convenção visual para distinguir do ✅/❌ (caracteres mais estreitos).

---

## Listagens em tabela

Formato padrão (`tela_listar`):

```
ID    Data         Categoria       Descrição                 Valor
----------------------------------------------------------------------
1     2026-06-08   Alimentação     Almoço                     R$    35.50
2     2026-06-08   Transporte      Uber                       R$    20.00
```

Especificação de larguras (já refletido em `src/app.py`):

```
{'ID':<5} {'Data':<12} {'Categoria':<15} {'Descrição':<25} {'Valor':>10}
```

- IDs e datas alinhados à esquerda.
- Valores alinhados à direita.
- Linha separadora horizontal de 70 traços.

---

## Resumo

Formato:

```
── Resumo de Gastos ──
Total geral:         R$ 1234.56

Por categoria:
  Alimentação        R$ 450.00
  Transporte         R$ 200.00
  Saúde              R$ 150.00
```

- Categorias ordenadas **decrescente por valor** (`sorted(..., key=lambda x: -x[1])`).
- Quando há clima disponível:

```
── Clima Atual ──
  📍 Brasilia
  🌡️  28.5°C — Céu limpo
```

---

## Boas-vindas e despedida

```
Bem-vindo ao GastoSmart! 💰
```

```
Até logo! 👋
```

Mantenha o tom amigável, mas sem exageros (sem ASCII art, sem múltiplas linhas).

---

## Categorias (fixas no MVP)

A lista hardcoded em `src/app.py`:

```python
CATEGORIAS = ["Alimentação", "Transporte", "Saúde", "Lazer", "Educação", "Moradia", "Outros"]
```

**Regra de exibição:** numeradas a partir de 1 no prompt de seleção. Ordem da lista é a ordem de exibição.

---

## Quando o terminal não suporta UTF-8

Se algum integrante reportar "quadrinhos" ao invés de emojis, a solução é setar `PYTHONIOENCODING=utf-8` antes de executar. Documentado em `docs/CONTRIBUTING.md`.

**Não removeremos os emojis.** Eles fazem parte da identidade visual do app.

---

## Mudanças futuras (registradas em `docs/ARD.md` se acontecerem)

- Adicionar cor (via `rich` ou `colorama`) — atualmente fora de escopo.
- Modo `--json` que retorna saída estruturada (útil pra automação) — fora de escopo.
- Modo interativo com setas (TUI via `prompt_toolkit`) — fora de escopo.
