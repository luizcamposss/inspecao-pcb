import csv
from pathlib import Path


def limpar_numero(valor):
    """
    Converte valores como:
    '25.4mm', '25,4', ' 25.4 ' para float.
    """

    if valor is None:
        return None

    valor = str(valor).strip()
    valor = valor.replace("mm", "")
    valor = valor.replace("MM", "")
    valor = valor.replace(",", ".")
    valor = valor.strip()

    if valor == "":
        return None

    try:
        return float(valor)
    except ValueError:
        return None


def normalizar_lado(valor):
    if valor is None:
        return "top"

    valor = str(valor).strip().lower()

    if valor in ["top", "t", "front", "f", "f.cu", "toplayer"]:
        return "top"

    if valor in ["bottom", "bot", "b", "back", "b.cu", "bottomlayer"]:
        return "bottom"

    return "top"


def pegar_coluna(row, nomes_possiveis):
    """
    Tenta pegar uma coluna mesmo que o CSV use nomes diferentes.
    Exemplo:
    Ref, Designator, Comment, Mid X, PosX etc.
    """

    for nome in nomes_possiveis:
        for chave in row.keys():
            if chave.strip().lower() == nome.strip().lower():
                return row[chave]

    return None


def carregar_cpl(caminho_csv: Path):
    """
    Lê um arquivo Pick and Place / CPL e retorna os componentes
    no formato usado pelo pipeline.
    """

    caminho_csv = Path(caminho_csv)

    if not caminho_csv.exists():
        raise FileNotFoundError(f"CPL não encontrado: {caminho_csv}")

    componentes = []

    with open(caminho_csv, "r", encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)

        for row in leitor:
            ref = pegar_coluna(row, [
                "Ref",
                "Reference",
                "Designator",
                "Designator Name",
                "Comment",
            ])

            val = pegar_coluna(row, [
                "Val",
                "Value",
                "Comment",
                "Description",
            ])

            package = pegar_coluna(row, [
                "Package",
                "Footprint",
                "Footprint Name",
                "Package Name",
            ])

            x = pegar_coluna(row, [
                "X",
                "PosX",
                "Mid X",
                "Center X",
                "Location X",
            ])

            y = pegar_coluna(row, [
                "Y",
                "PosY",
                "Mid Y",
                "Center Y",
                "Location Y",
            ])

            rot = pegar_coluna(row, [
                "Rot",
                "Rotation",
                "Rotate",
                "Angle",
            ])

            side = pegar_coluna(row, [
                "Side",
                "Layer",
                "Mount Layer",
            ])

            if not ref:
                continue

            x_mm = limpar_numero(x)
            y_mm = limpar_numero(y)
            rot = limpar_numero(rot)

            if x_mm is None or y_mm is None:
                continue

            comp = {
                "ref": str(ref).strip(),
                "val": str(val).strip() if val else "",
                "package": str(package).strip() if package else "",
                "x_mm": x_mm,
                "y_mm": y_mm,
                "rot": rot if rot is not None else 0,
                "side": normalizar_lado(side),
            }

            componentes.append(comp)

    return componentes