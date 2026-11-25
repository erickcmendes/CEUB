"""Executa o notebook de evidências (todas as células) e grava as saídas no próprio arquivo."""
import nbformat
from nbclient import NotebookClient

PATH = "notebooks/AV3_Evidencias_Pipeline.ipynb"

nb = nbformat.read(PATH, as_version=4)
NotebookClient(nb, timeout=600, kernel_name="python3",
               resources={"metadata": {"path": "/work/jobs"}}).execute()
nbformat.write(nb, PATH)

code_cells = [c for c in nb.cells if c.cell_type == "code"]
errors = [o for c in code_cells for o in c.get("outputs", []) if o.get("output_type") == "error"]
print(f"Notebook executado: {len(code_cells)} células de código, {len(errors)} erros")
for e in errors:
    print(e["ename"], e["evalue"])
