import csv
from pathlib import Path


def exportar_componentes_normalizados(componentes, caminho_saida: Path):
    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    campos = [
        "Ref",
        "Val",
        "Package",
        "PosX",
        "PosY",
        "Rot",
        "Side",
        "x_mm",
        "y_mm",
        "w_mm",
        "h_mm",
        "origem_footprint",
        "pads_usados",
    ]

    with open(caminho_saida, "w", newline="", encoding="utf-8") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=campos)
        writer.writeheader()

        for comp in componentes:
            writer.writerow({
                "Ref": comp.get("ref", ""),
                "Val": comp.get("val", ""),
                "Package": comp.get("package", ""),
                "PosX": comp.get("x_mm", ""),
                "PosY": comp.get("y_mm", ""),
                "Rot": comp.get("rot", 0),
                "Side": comp.get("side", "top"),
                "x_mm": comp.get("x_mm", ""),
                "y_mm": comp.get("y_mm", ""),
                "w_mm": comp.get("w_mm", ""),
                "h_mm": comp.get("h_mm", ""),
                "origem_footprint": comp.get("origem_footprint", ""),
                "pads_usados": comp.get("pads_usados", ""),
            })

    return caminho_saida