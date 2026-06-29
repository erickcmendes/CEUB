# Glossário de Negócio

> Termos do domínio do GastoSmart. Quando um termo novo do negócio aparecer (ex.: "orçamento mensal", "limite por categoria"), adicione aqui. Para termos técnicos (Supabase, RLS, etc.), ver [`glossario-tecnico.md`](glossario-tecnico.md).

---

### Gasto

Registro individual de uma despesa pessoal feita pelo usuário. É a **entidade central** do sistema.

**Atributos:**

| Atributo | Tipo | Obrigatório | Observação |
|---|---|---|---|
| `id` | inteiro auto-incremento | Sim (gerado) | Único; serve para remoção. |
| `descricao` | texto | Sim | Não vazia após strip. Ex.: "Almoço", "Uber pra faculdade". |
| `valor` | decimal (2 casas) | Sim | Maior que zero. Em reais (R$). |
| `categoria` | texto | Sim | Um dos valores da lista fixa em "Categoria". |
| `data` | data (AAAA-MM-DD) | Sim | Padrão: data de hoje. |
| `criado_em` | timestamp | Sim (gerado) | Quando a linha foi inserida no banco. |

**Regras de negócio:**

- Descrição não pode ser vazia ou só espaços.
- Valor precisa ser estritamente positivo (> 0).
- Categoria precisa estar na lista predefinida.
- Não há limite mínimo nem máximo de valor (além de > 0).

**Sinônimos comuns no time:** despesa, transação, registro. Padronizamos "gasto" em código e UI.

---

### Categoria

Rótulo predefinido usado para classificar e agrupar gastos no resumo.

**Lista fixa no MVP** (definida em `src/services.py` ou `src/app.py`):

| Categoria | Uso típico |
|---|---|
| Alimentação | Mercado, restaurante, delivery, café |
| Transporte | Uber, ônibus, combustível, estacionamento |
| Saúde | Farmácia, consulta, plano de saúde |
| Lazer | Cinema, streaming, jogos, viagens curtas |
| Educação | Cursos, livros, mensalidade |
| Moradia | Aluguel, condomínio, energia, internet |
| Outros | Qualquer despesa que não se encaixa nas anteriores |

**Regras:**

- O usuário escolhe pelo número no menu, não digita o nome.
- Não é possível criar categoria nova pela CLI (lista é hardcoded).
- "Outros" é o fallback consciente — não é "indefinido".

**Extensão futura registrada:** categorias customizáveis por usuário (ver `ARD.md` → AD-10 e "Pontos de extensão" em `architecture.md`).

---

### Resumo

Visão agregada dos gastos cadastrados. **Não é** uma entidade persistida — é calculada a cada chamada de `services.resumo_gastos()`.

**Composição:**

```python
{
    "total": float,                      # soma de todos os valores
    "por_categoria": {                   # totais agrupados
        "Alimentação": float,
        "Transporte": float,
        ...
    }
}
```

**Regras de exibição:**

- Categorias ordenadas decrescente por valor.
- Categorias com total zero não aparecem.
- Quando `OPENWEATHER_API_KEY` está setada, o resumo é seguido por um bloco de clima atual da cidade configurada.

---

### Total geral

Soma de todos os valores dos gastos cadastrados no banco. Em reais.

Quando não há gastos: `0.00`.

---

### Total por categoria

Soma dos valores dos gastos pertencentes a uma mesma categoria. Aparece no resumo apenas se a categoria tiver pelo menos 1 gasto.

---

### Cidade

Localidade usada na integração opcional com o OpenWeather. Definida pela env `OPENWEATHER_CIDADE`. Padrão: `Brasilia`.

**Observação:** não tem relação direta com os gastos (gasto não tem campo `cidade`). É apenas um parâmetro do bloco de clima no resumo.

---

### Clima atual

Informação opcional exibida no fim do resumo, vinda da API OpenWeather. Composto por:

- Nome da cidade (como devolvido pela API; pode diferir do que foi enviado).
- Temperatura em graus Celsius (arredondada a 1 casa decimal).
- Descrição textual (ex.: "Céu limpo", "Chuva leve") — vem em português via parâmetro `lang=pt_br` da API.

Quando indisponível (sem key, erro de rede, JSON inesperado), exibimos aviso `⚠️` e seguimos. **Nunca é bloqueante.**

---

### Operação

Termo genérico para qualquer das 4 ações principais da CLI: adicionar, listar, remover ou ver resumo. Usado no critério de aceite NFR-04 (< 2s por operação).

---

### MVP

Sigla para *Minimum Viable Product*. Neste projeto, refere-se ao escopo da **entrega final do bootcamp** (14/06/2026). Tudo que está em `SRS.md` como prioridade "MVP" precisa estar funcionando no deploy do Render no dia da avaliação.

---

### Entrega final

Marco da disciplina **Bootcamp II — Turma C 0226 (CEUB)** com vencimento em 14/06/2026 às 23:55. Envio via PDF na plataforma SalaOnline. Critérios em `SRS.md` → "Critérios da barema".
