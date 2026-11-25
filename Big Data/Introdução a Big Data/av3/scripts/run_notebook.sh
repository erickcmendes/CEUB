#!/usr/bin/env bash
# Gera e executa o notebook de evidências dentro da rede mybridge (imagem do Airflow + nbclient).
# A saída executada fica em notebooks/AV3_Evidencias_Pipeline.ipynb.
set -euo pipefail
cd "$(dirname "$0")/.."
docker run --rm --network mybridge --env-file .env \
  -e HOME=/tmp -e PYTHONPATH=/tmp/nbdeps:/work/jobs -e MPLCONFIGDIR=/tmp/mpl \
  -u "$(id -u):0" -v "$PWD:/work" -w /work --entrypoint bash av3-airflow:2.10.3 -c '
    # numpy fixado na versão da imagem: o matplotlib puxaria o numpy 2.x e quebraria o pandas instalado
    NP=$(PYTHONPATH= python -c "import numpy; print(numpy.__version__)")
    pip install --quiet --no-cache-dir --target /tmp/nbdeps nbformat nbclient ipykernel matplotlib "numpy==$NP"
    python notebooks/build_notebook.py
    python notebooks/execute_notebook.py'
