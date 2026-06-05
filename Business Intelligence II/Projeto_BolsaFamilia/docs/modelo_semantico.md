# Modelo Semantico

## Tabelas

### fato_bolsa_familia

Tabela fato agregada por `mes_competencia`, `uf`, `codigo_municipio_siafi` e `nome_municipio`.

A base bruta possui 2.324.900 linhas; a fato agregada possui 5.556 linhas. Essa decisao melhora a performance do Power BI e mantem todos os indicadores solicitados no exercicio.

Colunas principais:

- `total_repasses`
- `total_beneficiarios`
- `quantidade_pagamentos`
- `ano`
- `mes`
- `data_competencia`
- `mes_ano`

### dim_regioes

Tabela de apoio criada no Power Query com o mapeamento de UF para regiao geografica.

### dim_usuarios_rls

Tabela de apoio para RLS dinamico com `email_usuario` e `regiao_permitida`.

## Relacionamentos

| Origem | Destino | Cardinalidade | Direcao |
| --- | --- | --- | --- |
| `fato_bolsa_familia[uf]` | `dim_regioes[uf]` | Muitos para um | Unica |
| `dim_regioes[regiao]` | `dim_usuarios_rls[regiao_permitida]` | Muitos para um | Unica |

## Medidas DAX

```DAX
Total de Repasses = SUM('fato_bolsa_familia'[total_repasses])
Total de Beneficiarios = SUM('fato_bolsa_familia'[total_beneficiarios])
Ticket Medio = DIVIDE([Total de Repasses], [Total de Beneficiarios])
Municipios Atendidos = DISTINCTCOUNT('fato_bolsa_familia'[codigo_municipio_siafi])
Quantidade de Pagamentos = SUM('fato_bolsa_familia'[quantidade_pagamentos])
Repasse Medio por Municipio = DIVIDE([Total de Repasses], [Municipios Atendidos])
Regiao Lider = TOPN(1, regioes ordenadas por [Total de Repasses])
UF Lider = TOPN(1, UFs ordenadas por [Total de Repasses])
Participacao no Total = DIVIDE([Total de Repasses], CALCULATE([Total de Repasses], ALL('dim_regioes'[regiao])))
Rank Municipio por Repasse = RANKX(ALLSELECTED('fato_bolsa_familia'[nome_municipio]), [Total de Repasses],, DESC, Dense)
Repasse Top 10 Municipios = IF([Rank Municipio por Repasse] <= 10, [Total de Repasses], BLANK())
Concentracao Top 10 Municipios = DIVIDE(repasses dos 10 maiores municipios, [Total de Repasses])
```

As medidas `Regiao Lider`, `UF Lider` e `Concentracao Top 10 Municipios` foram adicionadas para enriquecer a leitura executiva e podem ser usadas em novos cartoes ou tooltips.
