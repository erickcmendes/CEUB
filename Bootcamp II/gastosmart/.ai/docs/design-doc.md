# Design Doc — Interação CLI

> Documento de design da experiência de uso do GastoSmart. Foca nas **telas** da CLI, nas mensagens e nos estados. Padrões visuais (emojis, separadores) ficam em [`../ui_guidelines.md`](../ui_guidelines.md).

---

## Telas do MVP

| ID | Tela | Função em `src/app.py` |
|---|---|---|
| T-01 | Menu Principal | `exibir_menu()` |
| T-02 | Adicionar Gasto | `tela_adicionar()` |
| T-03 | Listar Gastos | `tela_listar()` |
| T-04 | Remover Gasto | `tela_remover()` |
| T-05 | Resumo | `tela_resumo()` |
| T-06 | Boas-vindas / Despedida | `main()` |

---

## T-01 — Menu Principal

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
Escolha uma opção: _
```

**Comportamento:**

- Loop infinito até o usuário escolher `[0]`.
- Opção inválida → imprime `❌ Opção inválida. Tente novamente.` e re-exibe o menu.
- Após cada operação, retorna ao menu sem prompt adicional.

**Estados de erro:**

- Input vazio → tratado como inválido (mesmo fluxo de "Opção inválida").

---

## T-02 — Adicionar Gasto

**Sequência de prompts:**

```
── Adicionar Gasto ──
Descrição: _
Valor (R$): _

Categorias disponíveis:
  [1] Alimentação
  [2] Transporte
  [3] Saúde
  [4] Lazer
  [5] Educação
  [6] Moradia
  [7] Outros
Escolha o número da categoria: _
```

**Sucesso:**

```
✅ Gasto adicionado! ID #12 — Almoço — R$ 35.50
```

**Falhas comuns e mensagens:**

| Situação | Mensagem |
|---|---|
| Descrição vazia ou só espaços | `❌ Erro: A descrição não pode ser vazia.` |
| Valor não numérico (ex.: `abc`) | `❌ Digite um número válido.` (re-prompt) |
| Valor zero ou negativo | `❌ O valor deve ser maior que zero.` (re-prompt) |
| Número de categoria fora do intervalo | `❌ Opção inválida.` (re-prompt) |
| Categoria não numérica | `❌ Digite um número.` (re-prompt) |

**Estados:**

- Validações de número (`input_valor`, `input_categoria`) usam loop interno — usuário não retorna ao menu até dar entrada válida ou interromper com Ctrl+C.
- Validações de regra de negócio (em `services.adicionar_gasto`) levantam `ValueError`. A CLI imprime a mensagem com prefixo `❌ Erro: ` e retorna ao menu.

---

## T-03 — Listar Gastos

**Quando há gastos:**

```
── Lista de Gastos ──
ID    Data         Categoria       Descrição                 Valor
----------------------------------------------------------------------
1     2026-06-08   Alimentação     Almoço                     R$    35.50
2     2026-06-08   Transporte      Uber                       R$    20.00
3     2026-06-07   Lazer           Cinema                     R$    45.00
```

**Quando não há gastos:**

```
── Lista de Gastos ──
Nenhum gasto cadastrado ainda.
```

**Estado de erro de banco:**

- A partir do PR-02, se o repository levantar exceção (ex.: Supabase offline), a CLI deve imprimir:
  ```
  ⚠️  Não foi possível obter os gastos no momento.
  ```
  e voltar ao menu. **Sem stack trace exposto.**

**Ordenação:** sempre por `data DESC` (gastos mais recentes no topo).

---

## T-04 — Remover Gasto

```
── Remover Gasto ──
Digite o ID do gasto a remover: _
```

**Sucesso:**

```
✅ Gasto #12 removido com sucesso.
```

**Falhas:**

| Situação | Mensagem |
|---|---|
| ID não numérico | `❌ ID inválido.` |
| ID não existe na tabela | `❌ Gasto #N não encontrado.` |
| Erro de banco | `⚠️  Não foi possível concluir a remoção no momento.` (após PR-02) |

**Observação:** o MVP **não pede confirmação** antes de remover. Para um app de gastos pessoais sem multi-user, é aceitável. Registrar confirmação como ideia para extensão futura caso seja levantado em review.

---

## T-05 — Resumo

**Quando há gastos (sem chave OpenWeather):**

```
── Resumo de Gastos ──
Total geral:         R$ 1234.56

Por categoria:
  Alimentação        R$ 450.00
  Transporte         R$ 200.00
  Saúde              R$ 150.00
  Lazer              R$ 100.00
  Outros             R$ 334.56
```

**Quando há gastos (com chave OpenWeather válida):**

```
── Resumo de Gastos ──
Total geral:         R$ 1234.56

Por categoria:
  Alimentação        R$ 450.00
  ...

── Clima Atual ──
  📍 Brasilia
  🌡️  28.5°C — Céu limpo
```

**Quando há gastos mas clima falha:**

```
── Resumo de Gastos ──
Total geral:         R$ 1234.56
...

── Clima Atual ──
  ⚠️  Não foi possível obter o clima no momento.
```

**Quando não há gastos:**

```
── Resumo de Gastos ──
Total geral:         R$ 0.00
Nenhum gasto registrado.
```

(O bloco de clima ainda aparece se `OPENWEATHER_API_KEY` estiver setada — clima independe de haver gastos.)

**Ordenação por categoria:** decrescente por valor (`sorted(..., key=lambda x: -x[1])`).

---

## T-06 — Boas-vindas e Despedida

**Início do app:**

```
Bem-vindo ao GastoSmart! 💰
```

**Saída pelo `[0]`:**

```
Até logo! 👋
```

**Saída por Ctrl+C ou Ctrl+D:** comportamento atual é o do Python (KeyboardInterrupt / EOFError). Aceitável no MVP. Para tratar com elegância no futuro, ver [`ARD.md`](ARD.md) → caminho futuro de "captura de interrupção".

---

## Fluxograma resumido

```
[início] → boas-vindas → menu
                          ├─ [1] → adicionar → menu
                          ├─ [2] → listar → menu
                          ├─ [3] → remover → menu
                          ├─ [4] → resumo (+ clima opcional) → menu
                          └─ [0] → despedida → [fim]
```

---

## Acessibilidade e i18n

- **Idioma:** apenas português brasileiro no MVP.
- **Suporte a screen reader:** texto puro funciona naturalmente. Emojis podem ou não ser lidos dependendo do leitor.
- **Cores:** não usamos cor ANSI hoje. Se for adicionar (extensão futura), respeitar `NO_COLOR` env var como flag de desativação.

---

## Pontos a discutir no time (open questions)

1. Adicionar confirmação antes de remover? (Hoje não tem.)
2. Adicionar comando rápido para listar **apenas** a categoria mais cara?
3. Exibir contagem de gastos junto do total no resumo?

Quando uma dessas for decidida, registrar em `ARD.md` (novo AD) e atualizar este documento.
