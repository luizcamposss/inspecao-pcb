import os
import zipfile
import shutil

from services.kicad_cli_service import converter_para_kicad, exportar_csv
from services.footprint_service import gerar_csv_footprints
from core.config import get_project_paths

def criar_estrutura_projeto(nome_projeto):
    paths = get_project_paths(nome_projeto)

    return {
        "base": str(paths["base"]),
        "original": str(paths["original"]),
        "pcb": str(paths["pcb"]),
        "csv": str(paths["csv"]),
        "uploads": str(paths["uploads"]),
        "output": str(paths["output"]),
        "temp": str(paths["temp"]),
        "convert": str(paths["convert"]),
    }


def extrair_zip(caminho_zip, destino):
    with zipfile.ZipFile(caminho_zip, "r") as zip_ref:
        zip_ref.extractall(destino)


def encontrar_arquivos(pasta):
    encontrados = {
        "kicad_pcb": [],
        "brd": [],
        "sch": [],
        "pcbdoc": [],
        "pcb": [],
    }

    for root, _, files in os.walk(pasta):
        for file in files:
            caminho = os.path.join(root, file)
            nome = file.lower()

            if nome.endswith(".kicad_pcb"):
                encontrados["kicad_pcb"].append(caminho)
            elif nome.endswith(".brd"):
                encontrados["brd"].append(caminho)
            elif nome.endswith(".sch"):
                encontrados["sch"].append(caminho)
            elif nome.endswith(".pcbdoc"):
                encontrados["pcbdoc"].append(caminho)
            elif nome.endswith(".pcb"):
                encontrados["pcb"].append(caminho)

    return encontrados


def validar_kicad_pcb(caminho):
    if not os.path.exists(caminho):
        return False

    with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
        inicio = f.read(500)

    return "(kicad_pcb" in inicio


def brd_eagle_valido(caminho_brd):
    with open(caminho_brd, "r", encoding="utf-8", errors="ignore") as f:
        conteudo = f.read().lower()

    return "<eagle" in conteudo and "<board" in conteudo


def preparar_eagle_para_conversao(arquivo_brd, arquivos_sch, pasta_convert, nome_projeto):
    os.makedirs(pasta_convert, exist_ok=True)

    brd_destino = os.path.join(pasta_convert, f"{nome_projeto}.brd")
    shutil.copyfile(arquivo_brd, brd_destino)

    if arquivos_sch:
        sch_destino = os.path.join(pasta_convert, f"{nome_projeto}.sch")
        shutil.copyfile(arquivos_sch[0], sch_destino)

    return brd_destino


def reparar_kicad_pcb(caminho_pcb):
    with open(caminho_pcb, "r", encoding="utf-8", errors="ignore") as f:
        conteudo = f.read()

    conteudo = conteudo.replace('(layer "UNDEFINED")', '(layer "Dwgs.User")')

    with open(caminho_pcb, "w", encoding="utf-8") as f:
        f.write(conteudo)


def importar_projeto_universal(caminho_upload, nome_projeto):
    estrutura = criar_estrutura_projeto(nome_projeto)

    caminho_original = os.path.join(
        estrutura["original"],
        os.path.basename(caminho_upload)
    )

    shutil.copyfile(caminho_upload, caminho_original)

    # ZIP ou direto
    if caminho_original.lower().endswith(".zip"):
        extrair_zip(caminho_original, estrutura["temp"])
        pasta_busca = estrutura["temp"]
    else:
        pasta_busca = estrutura["original"]

    arquivos = encontrar_arquivos(pasta_busca)

    caminho_pcb = os.path.join(
        estrutura["pcb"],
        f"{nome_projeto}.kicad_pcb"
    )

    caminho_csv = os.path.join(
        estrutura["csv"],
        f"{nome_projeto}.csv"
    )

    # 🔹 1 - KiCad direto
    if arquivos["kicad_pcb"]:
        origem = arquivos["kicad_pcb"][0]

        if not validar_kicad_pcb(origem):
            raise RuntimeError("Arquivo .kicad_pcb inválido")

        shutil.copyfile(origem, caminho_pcb)

    # 🔹 2 - Eagle
    elif arquivos["brd"]:
        brd = arquivos["brd"][0]

        if not brd_eagle_valido(brd):
            raise RuntimeError("BRD não é Eagle válido")

        brd_convert = preparar_eagle_para_conversao(
            brd, arquivos["sch"], estrutura["convert"], nome_projeto
        )

        converter_para_kicad(brd_convert, caminho_pcb)

    # 🔹 3 - Altium
    elif arquivos["pcbdoc"]:
        converter_para_kicad(arquivos["pcbdoc"][0], caminho_pcb)

    # 🔹 4 - PCB genérico
    elif arquivos["pcb"]:
        converter_para_kicad(arquivos["pcb"][0], caminho_pcb)

    else:
        raise RuntimeError("Nenhum formato suportado encontrado")

    # 🔧 pós-processamento
    reparar_kicad_pcb(caminho_pcb)

    if not validar_kicad_pcb(caminho_pcb):
        raise RuntimeError("Conversão falhou → PCB inválido")

    # 📊 gerar CSV padrão KiCad
    try:
        gerar_csv_footprints(caminho_pcb, caminho_csv)
    except Exception as erro:
        print(f"[WARN] Falha ao gerar CSV por footprint: {erro}")
        print("[WARN] Usando CSV padrão do kicad-cli como fallback.")
        exportar_csv(caminho_pcb, caminho_csv)

    return {
        "pcb": caminho_pcb,
        "csv": caminho_csv,
    }