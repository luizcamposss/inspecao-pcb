from pathlib import Path

from pads import (
    extrair_pads_gerber,
    filtrar_pads_por_tamanho,
)

arquivo_gerber = Path("data/projetos/teste/UNOSMD_V3-F_Paste.gbr")

pads = extrair_pads_gerber(arquivo_gerber, origem="top_paste")
pads = filtrar_pads_por_tamanho(pads)

print("Quantidade de pads encontrados:", len(pads))

for pad in pads[:20]:
    print(pad)