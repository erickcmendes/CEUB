# Solucao Para Travamento de Carga no Power BI

## Problema

A base `amostra_bolsa.csv` possui 2.324.900 linhas. Ao aplicar varias etapas linha a linha no Power Query, a previa pode exibir:

```text
Preview.Error: O valor de visualizacao atual e muito complexo para exibir.
```

Em alguns computadores, a atualizacao completa tambem pode demorar demais ou travar.

## Solucao Aplicada

Foi criada a tabela `data/fato_bolsa_familia_agregada.csv`, gerada a partir da base bruta por:

- `mes_competencia`
- `uf`
- `codigo_municipio_siafi`
- `nome_municipio`

A tabela agregada mantem:

- `total_repasses`
- `total_beneficiarios`
- `quantidade_pagamentos`
- campos de tempo (`ano`, `mes`, `data_competencia`, `mes_ano`)

Com isso, o Power BI carrega 5.556 linhas em vez de 2.324.900.

Os CSVs ficam apenas no ambiente local e nao devem ser enviados ao GitHub. A origem publica da base bruta e:

[Fonte publica - Google Drive](http://drive.google.com/file/d/1Zc3JTXYEUaLdVvawZ92PVdkqRtqgpJs-/view)

## Como Regerar

```powershell
python scripts/gerar_fato_agregada.py
```

## Como Validar

```powershell
python scripts/validar_dados.py
```

O script compara os totais da base bruta com a fato agregada.
