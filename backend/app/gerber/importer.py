import zipfile
from pathlib import Path

from app.gerber.layers import identificar_camadas_gerber, escolher_melhor_camada_pads


def extrair_gerber_zip(caminho_zip: Path, pasta_destino: Path):
    pasta_destino.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(caminho_zip, "r") as zip_ref:
        zip_ref.extractall(pasta_destino)

    return pasta_destino


def importar_gerbers(caminho_zip: Path, pasta_destino: Path):
    pasta_extraida = extrair_gerber_zip(caminho_zip, pasta_destino)

    camadas = identificar_camadas_gerber(pasta_extraida)

    arquivo_pads_top, tipo_pads_top = escolher_melhor_camada_pads(
        camadas,
        side="top"
    )

    resultado = {
        "pasta": pasta_extraida,
        "camadas": camadas,
        "arquivo_pads_top": arquivo_pads_top,
        "tipo_pads_top": tipo_pads_top,
    }

    return resultado