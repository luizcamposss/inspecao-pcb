
from pathlib import Path
from export_csv import exportar_componentes_normalizados
from cpl_parser import carregar_cpl
from pads import (
    extrair_pads_gerber,
    filtrar_pads_por_tamanho,
    aplicar_footprints_por_ref,
)

# Encontra a raiz do backend (subindo 3 níveis a partir de backend/app/gerber/script.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Define os caminhos absolutos baseados na raiz do projeto
caminho_cpl = BASE_DIR / "data" / "projetos" / "teste" / "UNOSMD_V3-all-pos.csv"
caminho_paste = BASE_DIR / "data" / "projetos" / "teste" / "UNOSMD_V3-F_Paste.gbr"
caminho_exportar = BASE_DIR / "data" / "projetos" / "teste" / "componentes_normalizados.csv"


componentes = carregar_cpl(caminho_cpl)

pads = extrair_pads_gerber(caminho_paste, origem="top_paste")
pads = filtrar_pads_por_tamanho(pads)

componentes = aplicar_footprints_por_ref(
    componentes=componentes,
    pads=pads,
    margem_mm=0.4,
)

print("Pads encontrados:", len(pads))
print("Componentes com footprint:", len(componentes))

for comp in componentes[:20]:
    print(comp)


saida_csv = exportar_componentes_normalizados(
    componentes,
    caminho_exportar
)

print("CSV gerado em:", saida_csv)