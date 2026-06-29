# Row Level Security

## RLS Estatico

Funcoes criadas no modelo:

| Funcao | Filtro |
| --- | --- |
| `Admin` | Sem filtro; visualiza todos os dados |
| `Gestor_Norte` | `'dim_regioes'[regiao] = "Norte"` |
| `Gestor_Nordeste` | `'dim_regioes'[regiao] = "Nordeste"` |
| `Gestor_CentroOeste` | `'dim_regioes'[regiao] = "Centro-Oeste"` |
| `Gestor_Sudeste` | `'dim_regioes'[regiao] = "Sudeste"` |
| `Gestor_Sul` | `'dim_regioes'[regiao] = "Sul"` |

## RLS Dinamico

Funcao criada:

```DAX
'dim_usuarios_rls'[email_usuario] = USERPRINCIPALNAME()
```

Mapeamento de usuarios:

| Usuario | Regiao permitida |
| --- | --- |
| `gestor.norte@ministerio.br` | Norte |
| `gestor.nordeste@ministerio.br` | Nordeste |
| `gestor.centroeste@ministerio.br` | Centro-Oeste |
| `gestor.sudeste@ministerio.br` | Sudeste |
| `gestor.sul@ministerio.br` | Sul |

## Checklist de Teste

1. Abrir o arquivo `Projeto_BolsaFamilia+RLS.pbip` no Power BI Desktop.
2. Atualizar os dados.
3. Acessar `Modelagem > Exibir como`.
4. Testar `Admin` e confirmar que todas as regioes aparecem.
5. Testar cada perfil estatico e confirmar que apenas a respectiva regiao aparece.
6. Testar `Gestor_Regional_Dinamico` informando um dos e-mails de gestor.
7. Publicar no Power BI Service.
8. No Service, atribuir `pedro.mpereira@ceub.edu.br` a funcao `Admin`.
9. Atribuir os gestores regionais a `Gestor_Regional_Dinamico`.
