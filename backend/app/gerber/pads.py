from pathlib import Path
import math


def _to_float_mm(valor):
    """
    Garante que um valor vindo do Gerber esteja em float.
    Se vier None ou inválido, retorna None.
    """
    try:
        if valor is None:
            return None
        return float(valor)
    except Exception:
        return None


def _bbox_valida(x_min, y_min, x_max, y_max):
    if x_min is None or y_min is None or x_max is None or y_max is None:
        return False

    if x_max <= x_min or y_max <= y_min:
        return False

    return True


def _pad_a_partir_bbox(x_min, y_min, x_max, y_max, origem="gerber"):
    """
    Converte uma bounding box em um pad no formato usado pelo nosso sistema.
    """
    if not _bbox_valida(x_min, y_min, x_max, y_max):
        return None

    w_mm = x_max - x_min
    h_mm = y_max - y_min

    x_mm = x_min + w_mm / 2
    y_mm = y_min + h_mm / 2

    return {
        "x_mm": float(x_mm),
        "y_mm": float(y_mm),
        "w_mm": float(w_mm),
        "h_mm": float(h_mm),
        "source": origem,
    }


def _tentar_bbox_objeto(obj):
    """
    Tenta extrair a bounding box de um objeto do Gerber.

    A biblioteca pode representar objetos de formas diferentes.
    Por isso essa função tenta alguns formatos comuns.
    """

    # Caso 1: objeto tem método bounding_box()
    if hasattr(obj, "bounding_box"):
        try:
            bbox = obj.bounding_box(unit="mm")
            if bbox and len(bbox) == 4:
                return bbox
        except Exception:
            pass

        try:
            bbox = obj.bounding_box()
            if bbox and len(bbox) == 4:
                return bbox
        except Exception:
            pass

    # Caso 2: objeto tem método bounds()
    if hasattr(obj, "bounds"):
        try:
            bbox = obj.bounds(unit="mm")
            if bbox and len(bbox) == 4:
                return bbox
        except Exception:
            pass

        try:
            bbox = obj.bounds()
            if bbox and len(bbox) == 4:
                return bbox
        except Exception:
            pass

    # Caso 3: objeto já tem bbox como atributo
    if hasattr(obj, "bbox"):
        try:
            bbox = obj.bbox
            if bbox and len(bbox) == 4:
                return bbox
        except Exception:
            pass

    return None


def _normalizar_bbox(bbox):
    """
    Tenta transformar diferentes formatos de bbox em:
    x_min, y_min, x_max, y_max
    """

    if bbox is None:
        return None

    # Formato esperado:
    # (x_min, y_min, x_max, y_max)
    if len(bbox) == 4:
        x1, y1, x2, y2 = bbox

        x1 = _to_float_mm(x1)
        y1 = _to_float_mm(y1)
        x2 = _to_float_mm(x2)
        y2 = _to_float_mm(y2)

        if _bbox_valida(x1, y1, x2, y2):
            return x1, y1, x2, y2

    return None


def extrair_pads_gerber(caminho_gerber: Path, origem="top_paste"):
    """
    Lê um Gerber, normalmente F.Paste/.GTP, e tenta extrair pads.

    Retorna uma lista:
    [
        {
            "x_mm": 25.4,
            "y_mm": 10.2,
            "w_mm": 0.8,
            "h_mm": 1.0,
            "source": "top_paste"
        }
    ]
    """

    caminho_gerber = Path(caminho_gerber)

    if not caminho_gerber.exists():
        raise FileNotFoundError(f"Gerber não encontrado: {caminho_gerber}")

    try:
        from gerbonara.rs274x import GerberFile
    except ImportError:
        raise ImportError(
            "Biblioteca gerbonara não instalada. "
            "Adicione 'gerbonara' no requirements.txt e rode pip install -r requirements.txt"
        )

    gerber = GerberFile.open(caminho_gerber)

    pads = []

    for obj in gerber.objects:
        bbox = _tentar_bbox_objeto(obj)
        bbox_norm = _normalizar_bbox(bbox)

        if bbox_norm is None:
            continue

        x_min, y_min, x_max, y_max = bbox_norm

        pad = _pad_a_partir_bbox(
            x_min=x_min,
            y_min=y_min,
            x_max=x_max,
            y_max=y_max,
            origem=origem,
        )

        if pad is None:
            continue

        pads.append(pad)

    return pads


def filtrar_pads_por_tamanho(
    pads,
    min_w_mm=0.05,
    min_h_mm=0.05,
    max_w_mm=15.0,
    max_h_mm=15.0,
):
    """
    Remove objetos muito pequenos ou muito grandes.

    Muito pequeno pode ser ruído.
    Muito grande pode ser região de cobre/máscara que não é pad de componente.
    """

    filtrados = []

    for pad in pads:
        w = pad["w_mm"]
        h = pad["h_mm"]

        if w < min_w_mm or h < min_h_mm:
            continue

        if w > max_w_mm or h > max_h_mm:
            continue

        filtrados.append(pad)

    return filtrados


def buscar_pads_proximos(pads, x_mm, y_mm, raio_mm=5.0):
    """
    Busca pads próximos ao centro de um componente do CPL/Pick and Place.
    """

    proximos = []

    for pad in pads:
        dx = pad["x_mm"] - x_mm
        dy = pad["y_mm"] - y_mm
        dist = math.sqrt(dx * dx + dy * dy)

        if dist <= raio_mm:
            novo_pad = dict(pad)
            novo_pad["distancia_centro_mm"] = dist
            proximos.append(novo_pad)

    proximos.sort(key=lambda p: p["distancia_centro_mm"])

    return proximos


def estimar_footprint_por_pads(
    pads_proximos,
    margem_mm=0.4,
    min_pads=1,
):
    """
    Recebe pads próximos de um componente e calcula uma caixa aproximada.

    Essa caixa vira:
    w_mm e h_mm do componente.
    """

    if len(pads_proximos) < min_pads:
        return None

    x_min = min(p["x_mm"] - p["w_mm"] / 2 for p in pads_proximos)
    x_max = max(p["x_mm"] + p["w_mm"] / 2 for p in pads_proximos)

    y_min = min(p["y_mm"] - p["h_mm"] / 2 for p in pads_proximos)
    y_max = max(p["y_mm"] + p["h_mm"] / 2 for p in pads_proximos)

    w_mm = (x_max - x_min) + margem_mm
    h_mm = (y_max - y_min) + margem_mm

    centro_x = x_min + (x_max - x_min) / 2
    centro_y = y_min + (y_max - y_min) / 2

    return {
        "x_mm": float(centro_x),
        "y_mm": float(centro_y),
        "w_mm": float(w_mm),
        "h_mm": float(h_mm),
        "pads_usados": len(pads_proximos),
    }


def aplicar_footprints_estimados(componentes, pads, raio_mm=5.0):
    """
    Para cada componente vindo do CPL/Pick and Place:
    - busca pads próximos no Gerber
    - estima w_mm e h_mm
    - adiciona esses valores ao componente

    componentes precisa ter:
    ref, x_mm, y_mm, rot, side
    """

    componentes_com_footprint = []

    for comp in componentes:
        x = comp.get("x_mm")
        y = comp.get("y_mm")

        if x is None or y is None:
            componentes_com_footprint.append(comp)
            continue

        pads_proximos = buscar_pads_proximos(
            pads=pads,
            x_mm=float(x),
            y_mm=float(y),
            raio_mm=raio_mm,
        )

        footprint = estimar_footprint_por_pads(
            pads_proximos=pads_proximos,
            margem_mm=0.4,
            min_pads=1,
        )

        novo_comp = dict(comp)

        if footprint:
            novo_comp["w_mm"] = footprint["w_mm"]
            novo_comp["h_mm"] = footprint["h_mm"]
            novo_comp["origem_footprint"] = "gerber_pads"
            novo_comp["pads_usados"] = footprint["pads_usados"]
        else:
            novo_comp["w_mm"] = novo_comp.get("w_mm", 2.0)
            novo_comp["h_mm"] = novo_comp.get("h_mm", 2.0)
            novo_comp["origem_footprint"] = "fallback_padrao"
            novo_comp["pads_usados"] = 0

        componentes_com_footprint.append(novo_comp)

    return componentes_com_footprint