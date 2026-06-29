# Projeto Bolsa Familia + RLS

Projeto da disciplina **Business Intelligence II** com relatorio Power BI em formato `.pbip`, modelo semantico documentado e implementacao de **Row Level Security (RLS)** estatico e dinamico.

## Objetivo

Construir um painel gerencial para acompanhamento dos repasses do Programa Bolsa Familia, permitindo visao nacional para administradores e visao regional restrita para gestores regionais.

## Estrutura

```text
.
├── data/
│   └── README.md
├── docs/
│   ├── dashboard.md
│   ├── modelo_semantico.md
│   ├── rls.md
│   └── solucao_carga_powerbi.md
├── instrucoes/
│   └── exercicio_rls.pdf
├── scripts/
│   └── validar_dados.py
├── Projeto_BolsaFamilia+RLS.pbip
├── Projeto_BolsaFamilia+RLS.Report/
└── Projeto_BolsaFamilia+RLS.SemanticModel/
```

## Como Abrir

1. Instale/abra o Power BI Desktop.
2. Abra `Projeto_BolsaFamilia+RLS.pbip`.
3. Atualize os dados. A carga principal usa `data/fato_bolsa_familia_agregada.csv`, uma versao resumida da base bruta para acelerar o Power BI.
4. Confira as paginas `Visao Geral Nacional` e `Detalhe por Regiao e Estado`.
5. Teste as regras em `Modelagem > Exibir como`.

Se o projeto for clonado em outro computador, baixe a base publica, gere a fato agregada e atualize a origem do CSV no Power Query para apontar para `data/fato_bolsa_familia_agregada.csv` dentro da nova pasta local.

## Fonte de Dados

Fonte publica: [Google Drive](http://drive.google.com/file/d/1Zc3JTXYEUaLdVvawZ92PVdkqRtqgpJs-/view)

Arquivo bruto local: `data/amostra_bolsa.csv`

Arquivo usado na carga do dashboard: `data/fato_bolsa_familia_agregada.csv`

Cada linha representa um beneficio pago a um favorecido. A base contem:

| Indicador | Valor de validacao |
| --- | ---: |
| Linhas | 2.324.900 |
| Competencia | 202601 |
| Total de repasses | R$ 1.550.985.743,00 |
| Beneficiarios com NIS | 2.293.601 |
| Municipios atendidos | 5.556 |
| Ticket medio | R$ 676,22 |

> Os CSVs nao devem ser versionados no GitHub. A pasta `data/` mantem apenas a documentacao da fonte e o processo de geracao local.

Para evitar travamentos no Power Query, a tabela fato carregada no modelo e agregada por competencia, UF e municipio. Ela mantem os indicadores necessarios para o painel: repasses, beneficiarios distintos, quantidade de pagamentos, municipios, ticket medio e ranking de municipios.

## Tratamento no Power Query

A tabela `fato_bolsa_familia` usa o arquivo agregado e aplica:

- Tipagem de `mes_competencia`, `ano`, `mes`, `data_competencia` e metricas numericas.
- Leitura de uma tabela com 5.556 linhas, em vez das 2.324.900 linhas da base bruta.
- Preservacao dos totais validados da base original.

## Modelo Semantico

Tabelas:

- `fato_bolsa_familia`: pagamentos agregados por competencia, UF e municipio.
- `dim_regioes`: mapeia UF para regiao geografica.
- `dim_usuarios_rls`: mapeia e-mail do gestor para a regiao permitida.

Relacionamentos:

| Origem | Destino | Uso |
| --- | --- | --- |
| `fato_bolsa_familia[uf]` | `dim_regioes[uf]` | Filtrar fatos por UF/regiao |
| `dim_regioes[regiao]` | `dim_usuarios_rls[regiao_permitida]` | Propagar filtro do usuario para regioes |

## Medidas DAX

- `Total de Repasses`
- `Total de Beneficiarios`
- `Ticket Medio`
- `Municipios Atendidos`
- `Quantidade de Pagamentos`
- `Repasse Medio por Municipio`
- `Regiao Lider`
- `UF Lider`
- `Participacao no Total`
- `Rank Municipio por Repasse`
- `Repasse Top 10 Municipios`
- `Concentracao Top 10 Municipios`

As definicoes completas estao em [docs/modelo_semantico.md](docs/modelo_semantico.md).

A decisao de performance para evitar travamento no Power Query esta documentada em [docs/solucao_carga_powerbi.md](docs/solucao_carga_powerbi.md).

## Dashboard

### Pagina 1 - Visao Geral Nacional

- Cartoes: Total de Repasses, Total de Beneficiarios, Ticket Medio e Municipios Atendidos.
- Graficos comparativos por regiao: repasses, beneficiarios, ticket medio e municipios atendidos.
- Ranking nacional de municipios por repasse.
- Ranking de UFs com participacao no total.
- Sem segmentadores de periodo, pois a amostra possui apenas a competencia `01/2026`.

### Pagina 2 - Detalhe por Regiao e Estado

- Tabela por UF com municipios atendidos, beneficiarios, repasses e ticket medio.
- Grafico de barras com Top 10 municipios por valor de repasse.
- Segmentadores: Regiao e UF.

Paleta visual: roxo/magenta com fundo escuro, definida no tema `BolsaFamiliaRoxoMagenta`.

## RLS

### Estatico

Funcoes criadas:

- `Admin`
- `Gestor_Norte`
- `Gestor_Nordeste`
- `Gestor_CentroOeste`
- `Gestor_Sudeste`
- `Gestor_Sul`

### Dinamico

Funcao criada:

```DAX
'dim_usuarios_rls'[email_usuario] = USERPRINCIPALNAME()
```

Usuarios de teste:

| Usuario | Regiao |
| --- | --- |
| `gestor.norte@ministerio.br` | Norte |
| `gestor.nordeste@ministerio.br` | Nordeste |
| `gestor.centroeste@ministerio.br` | Centro-Oeste |
| `gestor.sudeste@ministerio.br` | Sudeste |
| `gestor.sul@ministerio.br` | Sul |

Na publicacao no Power BI Service, atribua `pedro.mpereira@ceub.edu.br` a funcao `Admin`.

## Validacao Local

Para recalcular os principais totais da base:

```powershell
python scripts/validar_dados.py
```

Para regenerar a fato agregada a partir da base bruta:

```powershell
python scripts/gerar_fato_agregada.py
```

## Publicacao no GitHub

```powershell
git init
git add .
git commit -m "Projeto Power BI Bolsa Familia com RLS"
git remote add origin <url-do-repositorio>
git push -u origin main
```

## Referencias

- [Row-level security (RLS) with Power BI](https://learn.microsoft.com/en-us/power-bi/enterprise/service-admin-rls)
- [USERPRINCIPALNAME function (DAX)](https://learn.microsoft.com/en-us/dax/userprincipalname-function-dax)
- [Power BI Desktop project report folder](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report)
- [Portal de Dados Abertos - Bolsa Familia Pagamentos](https://dados.gov.br/dados/conjuntos-dados/bolsa-familia-pagamentos)
