
import csv
from typing import List, Dict
import numpy as np


PACKAGE_SIZES_MM = {
    "C0603-ROUND": (1.6, 0.8),
    "R0603-ROUND": (1.6, 0.8),
    "CHIP-LED0805": (2.0, 1.25),
    "0805": (2.0, 1.25),
    "SOT-23": (2.9, 1.3),
    "SOT23-DBV": (2.9, 1.6),
    "SOT223": (6.5, 3.5),
    "MLF32": (5.0, 5.0),
    "ATMEL_QFN32": (5.0, 5.0),
    "MSOP08": (3.0, 3.0),
    "CAY16": (3.2, 1.6),
    "QS": (11.5, 4.5),
    "RESONATOR": (3.2, 1.3),
    "PANASONIC_D": (6.3, 6.3),
    "POWERSUPPLY_DC-21MM": (14.0, 12.0),
    "PN61729": (16.0, 13.0),
    "2X03": (7.6, 5.0),
    "2X02": (5.0, 5.0),
    "1X14-CUSTOM": (36.0, 2.5),
    "1X18-CUSTOM": (46.0, 2.5),
}


IGNORAR_PREFIXOS = (
    "TP_",
)

IGNORAR_REFS = {
    "FRAME1",
    "ORIGIN0",
}

IGNORAR_PACKAGES = {
    "FRAME",
    "TP-SP",
    "FD-1-1.5",
}

IGNORAR_VALORES = {
    "DNP",
}


def deve_ignorar(row: dict) -> bool:
    ref = row.get("Ref", "").strip().replace('"', "")
    val = row.get("Val", "").strip().replace('"', "")
    package = row.get("Package", "").strip().replace('"', "")
    side = row.get("Side", "").strip().lower().replace('"', "")

    if side != "top":
        return True

    if ref in IGNORAR_REFS:
        return True

    if any(ref.startswith(prefix) for prefix in IGNORAR_PREFIXOS):
        return True

    if package in IGNORAR_PACKAGES:
        return True

    if val in IGNORAR_VALORES:
        return True

    return False

def pegar_float(row, *nomes, padrao=0.0):
    for nome in nomes:
        valor = row.get(nome)

        if valor is not None and str(valor).strip() != "":
            return float(str(valor).replace(",", "."))

    return padrao

def carregar_componentes(caminho_csv: str) -> List[Dict]:
    componentes = []

    with open(caminho_csv, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if deve_ignorar(row):
                continue

            try:
                package = row["Package"].strip().replace('"', "")
                w_mm, h_mm = PACKAGE_SIZES_MM.get(package, (2.0, 2.0))

                comp = {
                    "ref": row["Ref"].strip().replace('"', ""),
                    "val": row.get("Val", "").strip().replace('"', ""),
                    "package": package,

                    "x_mm": pegar_float(row, "x_mm", "PosX"),
                    "y_mm": pegar_float(row, "y_mm", "PosY"),

                    "w_mm": pegar_float(row, "w_mm", "width_mm", padrao=2.0),
                    "h_mm": pegar_float(row, "h_mm", "height_mm", padrao=2.0),

                    "rot": pegar_float(row, "Rot"),
                    "side": row.get("Side", "").strip().lower().replace('"', ""),
                }

                componentes.append(comp)

            except Exception as e:
                print(f"[WARN] Linha ignorada: {row} | erro: {e}")

    return componentes


