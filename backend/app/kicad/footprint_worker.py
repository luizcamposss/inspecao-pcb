import csv
import sys
from pathlib import Path

import pcbnew


def to_mm(value):
    """
    Converte unidade interna do KiCad para milímetros.
    Melhor usar pcbnew.ToMM do que dividir manualmente.
    """
    return pcbnew.ToMM(value)


def get_footprint_side(footprint):
    layer = footprint.GetLayer()

    if layer == pcbnew.F_Cu:
        return "top"

    if layer == pcbnew.B_Cu:
        return "bottom"

    return "unknown"


def get_footprint_package(footprint):
    try:
        return str(footprint.GetFPID().GetLibItemName())
    except Exception:
        return ""


def get_footprint_value(footprint):
    try:
        return footprint.GetValue()
    except Exception:
        return ""


def get_footprint_rotation(footprint):
    """
    Em versões recentes do KiCad, GetOrientationDegrees costuma funcionar.
    Deixamos fallback para evitar quebrar se mudar algo.
    """
    try:
        return float(footprint.GetOrientationDegrees())
    except Exception:
        try:
            return float(footprint.GetOrientation().AsDegrees())
        except Exception:
            return 0.0


def get_bbox_from_pads_or_footprint(footprint):
    """
    Mede o tamanho do footprint.

    Preferência:
    1. pads, porque representam melhor a área útil do componente;
    2. bounding box do footprint, se não houver pads.
    """
    pads = list(footprint.Pads())

    if pads:
        min_x = min(pad.GetBoundingBox().GetLeft() for pad in pads)
        max_x = max(pad.GetBoundingBox().GetRight() for pad in pads)
        min_y = min(pad.GetBoundingBox().GetTop() for pad in pads)
        max_y = max(pad.GetBoundingBox().GetBottom() for pad in pads)
    else:
        bbox = footprint.GetBoundingBox()
        min_x = bbox.GetLeft()
        max_x = bbox.GetRight()
        min_y = bbox.GetTop()
        max_y = bbox.GetBottom()

    width_mm = to_mm(max_x - min_x)
    height_mm = to_mm(max_y - min_y)

    return width_mm, height_mm


def extrair_footprints(caminho_pcb, caminho_csv_saida):
    board = pcbnew.LoadBoard(str(caminho_pcb))

    linhas = []

    for footprint in board.GetFootprints():
        ref = footprint.GetReference().strip()

        if not ref:
            continue

        # Evita pegar coisas que não são componentes reais, se existirem.
        if ref.upper().startswith("#"):
            continue

        pos = footprint.GetPosition()

        x_mm = to_mm(pos.x)
        y_mm = -to_mm(pos.y)

        val = get_footprint_value(footprint)
        package = get_footprint_package(footprint)
        rot = get_footprint_rotation(footprint)
        side = get_footprint_side(footprint)

        w_mm, h_mm = get_bbox_from_pads_or_footprint(footprint)

        linhas.append({
            "Ref": ref,
            "Val": val,
            "Package": package,
            "PosX": round(x_mm, 4),
            "PosY": round(y_mm, 4),
            "Rot": round(rot, 4),
            "Side": side,
            "x_mm": round(x_mm, 4),
            "y_mm": round(y_mm, 4),
            "w_mm": round(w_mm, 4),
            "h_mm": round(h_mm, 4),
        })

    linhas.sort(key=lambda item: item["Ref"])

    colunas = [
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
    ]

    caminho_csv_saida = Path(caminho_csv_saida)
    caminho_csv_saida.parent.mkdir(parents=True, exist_ok=True)

    with open(caminho_csv_saida, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=colunas)
        writer.writeheader()
        writer.writerows(linhas)

    print(f"CSV gerado: {caminho_csv_saida}")
    print(f"Footprints extraídos: {len(linhas)}")


def main():
    if len(sys.argv) != 3:
        print("Uso:")
        print("python footprint_worker.py entrada.kicad_pcb saida.csv")
        sys.exit(1)

    caminho_pcb = Path(sys.argv[1])
    caminho_csv_saida = Path(sys.argv[2])

    if not caminho_pcb.exists():
        print(f"Arquivo .kicad_pcb não encontrado: {caminho_pcb}")
        sys.exit(1)

    extrair_footprints(caminho_pcb, caminho_csv_saida)


if __name__ == "__main__":
    main()