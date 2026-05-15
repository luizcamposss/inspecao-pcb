from pathlib import Path


def identificar_tipo_gerber(caminho: Path):
    nome = caminho.name.lower()

    # Top Paste - melhor para componentes SMD pequenos
    if (
        nome.endswith(".gtp")
        or "f_paste" in nome
        or "f.paste" in nome
        or "top_paste" in nome
        or "toppaste" in nome
    ):
        return "top_paste"

    # Bottom Paste
    if (
        nome.endswith(".gbp")
        or "b_paste" in nome
        or "b.paste" in nome
        or "bottom_paste" in nome
        or "bottompaste" in nome
    ):
        return "bottom_paste"

    # Top Mask
    if (
        nome.endswith(".gts")
        or "f_mask" in nome
        or "f.mask" in nome
        or "top_mask" in nome
        or "topmask" in nome
    ):
        return "top_mask"

    # Bottom Mask
    if (
        nome.endswith(".gbs")
        or "b_mask" in nome
        or "b.mask" in nome
        or "bottom_mask" in nome
        or "bottommask" in nome
    ):
        return "bottom_mask"

    # Top Copper
    if (
        nome.endswith(".gtl")
        or "f_cu" in nome
        or "f.cu" in nome
        or "top_copper" in nome
        or "topcopper" in nome
    ):
        return "top_copper"

    # Bottom Copper
    if (
        nome.endswith(".gbl")
        or "b_cu" in nome
        or "b.cu" in nome
        or "bottom_copper" in nome
        or "bottomcopper" in nome
    ):
        return "bottom_copper"

    # Top Silk
    if (
        nome.endswith(".gto")
        or "f_silks" in nome
        or "f.silks" in nome
        or "top_silk" in nome
        or "topsilk" in nome
    ):
        return "top_silk"

    # Bottom Silk
    if (
        nome.endswith(".gbo")
        or "b_silks" in nome
        or "b.silks" in nome
        or "bottom_silk" in nome
        or "bottomsilk" in nome
    ):
        return "bottom_silk"

    # Board outline
    if (
        nome.endswith(".gko")
        or nome.endswith(".gm1")
        or nome.endswith(".gml")
        or "edge_cuts" in nome
        or "edge.cuts" in nome
        or "outline" in nome
        or "boardoutline" in nome
    ):
        return "outline"

    # Drill
    if (
        nome.endswith(".drl")
        or nome.endswith(".xln")
        or "drill" in nome
    ):
        return "drill"

    return "desconhecido"


def identificar_camadas_gerber(pasta_gerber: Path):
    camadas = {
        "top_paste": [],
        "bottom_paste": [],
        "top_mask": [],
        "bottom_mask": [],
        "top_copper": [],
        "bottom_copper": [],
        "top_silk": [],
        "bottom_silk": [],
        "outline": [],
        "drill": [],
        "desconhecido": [],
    }

    for arquivo in pasta_gerber.rglob("*"):
        if not arquivo.is_file():
            continue

        tipo = identificar_tipo_gerber(arquivo)
        camadas[tipo].append(arquivo)

    return camadas


def escolher_melhor_camada_pads(camadas, side="top"):
    """
    Escolhe a melhor camada para extrair pads dos componentes.
    Para componentes pequenos SMD:
    1. Paste
    2. Mask
    3. Copper
    """

    side = side.lower()

    if side == "top":
        prioridade = ["top_paste", "top_mask", "top_copper"]
    else:
        prioridade = ["bottom_paste", "bottom_mask", "bottom_copper"]

    for tipo in prioridade:
        arquivos = camadas.get(tipo, [])
        if arquivos:
            return arquivos[0], tipo

    return None, None