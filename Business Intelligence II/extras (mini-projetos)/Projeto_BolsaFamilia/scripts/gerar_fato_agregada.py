from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "amostra_bolsa.csv"
OUTPUT_CSV = ROOT / "data" / "fato_bolsa_familia_agregada.csv"


@dataclass
class GrupoPagamento:
    total_repasses: Decimal = Decimal("0")
    quantidade_pagamentos: int = 0
    beneficiarios: set[str] = field(default_factory=set)


def parse_valor(valor: str) -> Decimal:
    return Decimal(valor.replace(".", "").replace(",", "."))


def main() -> None:
    grupos: dict[tuple[str, str, str, str], GrupoPagamento] = defaultdict(GrupoPagamento)

    with RAW_CSV.open("r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.reader(arquivo)
        next(leitor)

        for row in leitor:
            mes_competencia = row[0]
            uf = row[1].strip().upper()
            codigo_municipio = row[2]
            nome_municipio = row[3].strip()
            nis = row[5].split(".")[0] if row[5] else ""
            valor = parse_valor(row[7])

            chave = (mes_competencia, uf, codigo_municipio, nome_municipio)
            grupo = grupos[chave]
            grupo.total_repasses += valor
            grupo.quantidade_pagamentos += 1
            if nis:
                grupo.beneficiarios.add(nis)

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(
            [
                "mes_competencia",
                "uf",
                "codigo_municipio_siafi",
                "nome_municipio",
                "ano",
                "mes",
                "data_competencia",
                "mes_ano",
                "total_repasses",
                "total_beneficiarios",
                "quantidade_pagamentos",
            ]
        )

        for chave, grupo in sorted(grupos.items()):
            mes_competencia, uf, codigo_municipio, nome_municipio = chave
            ano = int(mes_competencia[:4])
            mes = int(mes_competencia[4:])
            escritor.writerow(
                [
                    mes_competencia,
                    uf,
                    codigo_municipio,
                    nome_municipio,
                    ano,
                    mes,
                    f"{ano:04d}-{mes:02d}-01",
                    f"{mes:02d}/{ano:04d}",
                    f"{grupo.total_repasses:.2f}",
                    len(grupo.beneficiarios),
                    grupo.quantidade_pagamentos,
                ]
            )

    print(f"Arquivo gerado: {OUTPUT_CSV}")
    print(f"Linhas agregadas: {len(grupos):,}".replace(",", "."))


if __name__ == "__main__":
    main()
