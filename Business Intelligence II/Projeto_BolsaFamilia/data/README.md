# Fonte de Dados

Esta pasta armazena:

- `amostra_bolsa.csv`: base bruta original.
- `fato_bolsa_familia_agregada.csv`: base agregada usada pelo Power BI para evitar travamentos na carga.

Os arquivos CSV nao devem ser versionados no GitHub. A fonte publica esta no Drive:

[Fonte publica - Google Drive](http://drive.google.com/file/d/1Zc3JTXYEUaLdVvawZ92PVdkqRtqgpJs-/view)

Baixe a base bruta para:

```text
data/amostra_bolsa.csv
```

O projeto `.pbip` referencia a fato agregada:

```text
data/fato_bolsa_familia_agregada.csv
```

Para recriar o arquivo agregado:

```powershell
python scripts/gerar_fato_agregada.py
```
