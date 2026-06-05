from __future__ import annotations

import csv
from collections import defaultdict
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "amostra_bolsa.csv"
AGG_CSV_PATH = ROOT / "data" / "fato_bolsa_familia_agregada.csv"

REGIOES = {
    "Norte": {"AC", "AM", "AP", "PA", "RO", "RR", "TO"},
    "Nordeste": {"AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"},
    "Centro-Oeste": {"DF", "GO", "MS", "MT"},
    "Sudeste": {"ES", "MG", "RJ", "SP"},
    "Sul": {"PR", "RS", "SC"},
}

UF_PARA_REGIAO = {uf: regiao for regiao, ufs in REGIOES.items() for uf in ufs}


def parse_valor(valor: str) -> Decimal:
    return Decimal(valor.replace(".", "").replace(",", "."))


def main() -> None:
    total = Decimal("0")
    linhas = 0
    competencias: set[str] = set()
    beneficiarios: set[str] = set()
    municipios: set[str] = set()
    por_regiao: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    with CSV_PATH.open("r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.reader(arquivo)
        next(leitor)

        for row in leitor:
            linhas += 1
            competencia, uf, codigo_municipio, _, _, nis, _, valor = row
            valor_decimal = parse_valor(valor)

            total += valor_decimal
            competencias.add(competencia)
            municipios.add(codigo_municipio)
            if nis:
                beneficiarios.add(nis.split(".")[0])

            por_regiao[UF_PARA_REGIAO[uf]] += valor_decimal

    ticket = total / len(beneficiarios)

    print(f"Linhas: {linhas:,}".replace(",", "."))
    print(f"Competencias: {', '.join(sorted(competencias))}")
    print(f"Total de repasses: R$ {total:,.2f}")
    print(f"Beneficiarios: {len(beneficiarios):,}".replace(",", "."))
    print(f"Municipios: {len(municipios):,}".replace(",", "."))
    print(f"Ticket medio: R$ {ticket:,.2f}")
    print("Repasses por regiao:")
    for regiao, valor in sorted(por_regiao.items(), key=lambda item: item[1], reverse=True):
        print(f"- {regiao}: R$ {valor:,.2f}")

    if AGG_CSV_PATH.exists():
        total_agregado = Decimal("0")
        beneficiarios_agregado = 0
        pagamentos_agregado = 0
        municipios_agregado: set[str] = set()

        with AGG_CSV_PATH.open("r", encoding="utf-8", newline="") as arquivo:
            leitor = csv.DictReader(arquivo)
            for row in leitor:
                total_agregado += Decimal(row["total_repasses"])
                beneficiarios_agregado += int(row["total_beneficiarios"])
                pagamentos_agregado += int(row["quantidade_pagamentos"])
                municipios_agregado.add(row["codigo_municipio_siafi"])

        print("\nValidacao da fato agregada:")
        print(f"- Total de repasses bate: {total_agregado == total}")
        print(f"- Beneficiarios batem: {beneficiarios_agregado == len(beneficiarios)}")
        print(f"- Pagamentos batem: {pagamentos_agregado == linhas}")
        print(f"- Municipios batem: {len(municipios_agregado) == len(municipios)}")


if __name__ == "__main__":
    main()
