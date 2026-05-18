import re
import math
from pathlib import Path


def coordenada_gerber_para_mm(valor: str):
    """
    Converte coordenada Gerber do formato 4.6 em mm.

    Exemplo:
    X134150100 -> 134.150100 mm
    Y-102082600 -> -102.082600 mm
    """
    if valor is None:
        return None

    return int(valor) / 1_000_000


def extrair_apertures(caminho_gerber: Path):
    """
    Lê as definições D10, D11, D12... e tenta descobrir o tamanho
    da abertura usada em cada pad.

    Para flash D03, o tamanho do pad vem da abertura atual.
    """

    texto = Path(caminho_gerber).read_text(encoding="utf-8", errors="ignore")

    apertures = {}

    # Circular: %ADD10C,0.304800*%
    padrao_circular = re.compile(r"%ADD(\d+)C,([\d\.\-]+)\*%")

    for match in padrao_circular.finditer(texto):
        codigo = int(match.group(1))
        diametro = float(match.group(2))

        apertures[codigo] = {
            "tipo": "circle",
            "w_mm": diametro,
            "h_mm": diametro,
        }

    # RoundRect:
    # %ADD12RoundRect,0.318720X-0.079680X0.180480X...*%
    padrao_roundrect = re.compile(r"%ADD(\d+)RoundRect,([^*]+)\*%")

    for match in padrao_roundrect.finditer(texto):
        codigo = int(match.group(1))
        params = match.group(2).split("X")

        numeros = []

        for p in params:
            try:
                numeros.append(float(p))
            except ValueError:
                pass

        # O primeiro número é o raio.
        # Depois vêm os pontos dos 4 cantos:
        # x1,y1,x2,y2,x3,y3,x4,y4
        coords = numeros[1:]

        xs = coords[0::2]
        ys = coords[1::2]

        if xs and ys:
            w = max(xs) - min(xs)
            h = max(ys) - min(ys)

            apertures[codigo] = {
                "tipo": "roundrect",
                "w_mm": abs(w),
                "h_mm": abs(h),
            }

    return apertures


def extrair_pads_gerber(caminho_gerber: Path, origem="top_paste"):
    """
    Extrai pads de um Gerber F.Paste/.GTP exportado pelo KiCad.

    Suporta:
    - flashes D03
    - regiões G36/G37
    - atributos %TO.C,REF*%

    Retorna:
    [
        {
            "ref": "R1",
            "x_mm": 134.15,
            "y_mm": -102.08,
            "w_mm": 0.36,
            "h_mm": 0.16,
            "source": "top_paste"
        }
    ]
    """

    caminho_gerber = Path(caminho_gerber)

    if not caminho_gerber.exists():
        raise FileNotFoundError(f"Gerber não encontrado: {caminho_gerber}")

    texto = caminho_gerber.read_text(encoding="utf-8", errors="ignore")
    linhas = texto.splitlines()

    apertures = extrair_apertures(caminho_gerber)

    pads = []

    ref_atual = None
    aperture_atual = None

    dentro_regiao = False
    pontos_regiao = []

    for linha in linhas:
        linha = linha.strip()

        # Exemplo: %TO.C,R1*%
        match_ref = re.search(r"%TO\.C,([^*]+)\*%", linha)
        if match_ref:
            ref_atual = match_ref.group(1).strip()
            continue

        # Fim do atributo do componente
        if linha.startswith("%TD"):
            ref_atual = None
            continue

        # Seleção de aperture: D12*
        match_aperture = re.fullmatch(r"D(\d+)\*", linha)
        if match_aperture:
            aperture_atual = int(match_aperture.group(1))
            continue

        # Início de região
        if linha.startswith("G36"):
            dentro_regiao = True
            pontos_regiao = []
            continue

        # Fim de região
        if linha.startswith("G37"):
            if pontos_regiao:
                xs = [p[0] for p in pontos_regiao]
                ys = [p[1] for p in pontos_regiao]

                x_min = min(xs)
                x_max = max(xs)
                y_min = min(ys)
                y_max = max(ys)

                w = x_max - x_min
                h = y_max - y_min

                if w > 0 and h > 0:
                    pads.append({
                        "ref": ref_atual,
                        "x_mm": x_min + w / 2,
                        "y_mm": y_min + h / 2,
                        "w_mm": w,
                        "h_mm": h,
                        "source": origem,
                        "tipo": "region",
                    })

            dentro_regiao = False
            pontos_regiao = []
            continue

        # Coordenada X/Y
        match_xy = re.search(r"X(-?\d+)Y(-?\d+)", linha)

        if not match_xy:
            continue

        x_mm = coordenada_gerber_para_mm(match_xy.group(1))
        y_mm = coordenada_gerber_para_mm(match_xy.group(2))

        # Se estiver dentro de G36/G37, guarda ponto da região
        if dentro_regiao:
            pontos_regiao.append((x_mm, y_mm))
            continue

        # Flash D03: pad individual
        if "D03" in linha:
            ap = apertures.get(aperture_atual)

            if ap:
                w_mm = ap["w_mm"]
                h_mm = ap["h_mm"]
            else:
                # fallback se não conseguir descobrir aperture
                w_mm = 0.5
                h_mm = 0.5

            pads.append({
                "ref": ref_atual,
                "x_mm": x_mm,
                "y_mm": y_mm,
                "w_mm": w_mm,
                "h_mm": h_mm,
                "source": origem,
                "tipo": "flash",
                "aperture": aperture_atual,
            })

    return pads


def filtrar_pads_por_tamanho(
    pads,
    min_w_mm=0.03,
    min_h_mm=0.03,
    max_w_mm=20.0,
    max_h_mm=20.0,
):
    filtrados = []

    for pad in pads:
        w = abs(pad["w_mm"])
        h = abs(pad["h_mm"])

        if w < min_w_mm or h < min_h_mm:
            continue

        if w > max_w_mm or h > max_h_mm:
            continue

        filtrados.append(pad)

    return filtrados


def buscar_pads_proximos(pads, x_mm, y_mm, raio_mm=5.0):
    proximos = []

    for pad in pads:
        dx = pad["x_mm"] - x_mm
        dy = pad["y_mm"] - y_mm
        dist = math.sqrt(dx * dx + dy * dy)

        if dist <= raio_mm:
            novo = dict(pad)
            novo["distancia_centro_mm"] = dist
            proximos.append(novo)

    proximos.sort(key=lambda p: p["distancia_centro_mm"])
    return proximos


def estimar_footprint_por_pads(pads_proximos, margem_mm=0.4, min_pads=1):
    if len(pads_proximos) < min_pads:
        return None

    x_min = min(p["x_mm"] - p["w_mm"] / 2 for p in pads_proximos)
    x_max = max(p["x_mm"] + p["w_mm"] / 2 for p in pads_proximos)

    y_min = min(p["y_mm"] - p["h_mm"] / 2 for p in pads_proximos)
    y_max = max(p["y_mm"] + p["h_mm"] / 2 for p in pads_proximos)

    w_mm = (x_max - x_min) + margem_mm
    h_mm = (y_max - y_min) + margem_mm

    return {
        "x_mm": x_min + (x_max - x_min) / 2,
        "y_mm": y_min + (y_max - y_min) / 2,
        "w_mm": w_mm,
        "h_mm": h_mm,
        "pads_usados": len(pads_proximos),
    }


def aplicar_footprints_estimados(componentes, pads, raio_mm=5.0):
    componentes_com_footprint = []

    for comp in componentes:
        x = comp.get("x_mm")
        y = comp.get("y_mm")

        novo_comp = dict(comp)

        if x is None or y is None:
            novo_comp["origem_footprint"] = "sem_posicao"
            componentes_com_footprint.append(novo_comp)
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


from collections import defaultdict


def agrupar_pads_por_ref(pads):
    """
    Agrupa os pads pelo nome do componente vindo do Gerber.
    Exemplo:
    {
        "R1": [pad1, pad2],
        "C1": [pad1, pad2],
        "U1": [pad1, pad2, ...]
    }
    """

    grupos = defaultdict(list)

    for pad in pads:
        ref = pad.get("ref")

        if not ref:
            continue

        grupos[str(ref).strip()].append(pad)

    return dict(grupos)


def estimar_footprint_por_ref(pads_do_ref, margem_mm=0.4):
    """
    Calcula w_mm/h_mm usando apenas os pads daquele componente.
    """

    if not pads_do_ref:
        return None

    x_min = min(p["x_mm"] - p["w_mm"] / 2 for p in pads_do_ref)
    x_max = max(p["x_mm"] + p["w_mm"] / 2 for p in pads_do_ref)

    y_min = min(p["y_mm"] - p["h_mm"] / 2 for p in pads_do_ref)
    y_max = max(p["y_mm"] + p["h_mm"] / 2 for p in pads_do_ref)

    w_mm = (x_max - x_min) + margem_mm
    h_mm = (y_max - y_min) + margem_mm

    centro_x = x_min + (x_max - x_min) / 2
    centro_y = y_min + (y_max - y_min) / 2

    return {
        "x_mm": float(centro_x),
        "y_mm": float(centro_y),
        "w_mm": float(w_mm),
        "h_mm": float(h_mm),
        "pads_usados": len(pads_do_ref),
    }


def aplicar_footprints_por_ref(componentes, pads, margem_mm=0.4):
    """
    Melhor versão para Gerbers do KiCad, porque usa o atributo %TO.C,REF*%.

    Em vez de buscar pads por proximidade, usa:
    comp["ref"] == pad["ref"]
    """

    pads_por_ref = agrupar_pads_por_ref(pads)
    componentes_final = []

    for comp in componentes:
        novo_comp = dict(comp)
        ref = str(comp.get("ref", "")).strip()

        pads_do_ref = pads_por_ref.get(ref, [])

        footprint = estimar_footprint_por_ref(
            pads_do_ref,
            margem_mm=margem_mm,
        )

        if footprint:
            novo_comp["w_mm"] = footprint["w_mm"]
            novo_comp["h_mm"] = footprint["h_mm"]
            novo_comp["origem_footprint"] = "gerber_ref"
            novo_comp["pads_usados"] = footprint["pads_usados"]

            # Opcional: manter o centro do CPL, não o centro dos pads.
            # Isso é melhor porque o CPL representa o centro do componente.
            # Então NÃO sobrescrevemos x_mm e y_mm aqui.

        else:
            novo_comp["w_mm"] = novo_comp.get("w_mm", 2.0)
            novo_comp["h_mm"] = novo_comp.get("h_mm", 2.0)
            novo_comp["origem_footprint"] = "fallback_padrao"
            novo_comp["pads_usados"] = 0

        componentes_final.append(novo_comp)

    return componentes_final