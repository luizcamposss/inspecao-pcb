from pathlib import Path

from app.parsers.cpl_parser import carregar_cpl
from app.gerber.pads import (
    extrair_pads_gerber,
    filtrar_pads_por_tamanho,
    aplicar_footprints_estimados,
)

caminho_cpl = Path("backend/data/projetos/teste/teste.csv")
caminho_paste = Path("backend/data/projetos/teste/UNOSMD_V3-F_Paste.gbr")

componentes = carregar_cpl(caminho_cpl)

pads = extrair_pads_gerber(caminho_paste, origem="top_paste")
pads = filtrar_pads_por_tamanho(pads)

componentes = aplicar_footprints_estimados(
    componentes=componentes,
    pads=pads,
    raio_mm=4.0,
)

print("Pads encontrados:", len(pads))
print("Componentes com footprint:", len(componentes))

for comp in componentes[:20]:
    print(comp)