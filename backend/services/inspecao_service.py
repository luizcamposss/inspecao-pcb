from pathlib import Path
import shutil

from core.config import get_project_paths, normalizar_nome_projeto
from app.processing.pipeline import run_overlay_referencia


def inspecionar_placa(imagem, projeto_csv, nome_projeto=None):
    if nome_projeto:
        nome_base = normalizar_nome_projeto(nome_projeto)
    else:
        nome_base = normalizar_nome_projeto(Path(projeto_csv).stem)

    paths = get_project_paths(nome_base)

    caminho_csv = paths["csv"] / projeto_csv
    caminho_pcb = paths["pcb"] / f"{nome_base}.kicad_pcb"
    caminho_img = paths["uploads"] / "imagem_placa.jpg"
    caminho_saida = paths["output"] / f"resultado_{nome_base}.png"

    if not caminho_csv.exists():
        return {"erro": f"CSV não encontrado: {caminho_csv}"}

    if not caminho_pcb.exists():
        return {"erro": f"PCB não encontrado: {caminho_pcb}"}

    with open(caminho_img, "wb") as buffer:
        shutil.copyfileobj(imagem.file, buffer)

    run_overlay_referencia(
        caminho_img=str(caminho_img),
        caminho_csv=str(caminho_csv),
        caminho_pcb=str(caminho_pcb),
        caminho_saida=str(caminho_saida),
    )

    return {
        "ok": True,
        "resultado": caminho_saida.name,
        "url": f"http://127.0.0.1:8000/resultado/{nome_base}/{caminho_saida.name}"
    }