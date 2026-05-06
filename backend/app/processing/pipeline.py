import os
import cv2
import numpy as np

from app.processing.parser import carregar_componentes
from app.processing.mm_to_pixel import mm_para_pixel_perspectiva
from app.processing.align import carregar_imagem, detectar_contorno_pcb
from app.processing.draw import desenhar_ponto_e_label, desenhar_caixa_aproximada_matriz
from app.kicad.pcb_parser import carregar_edgecuts_pcb, extrair_bbox_edgecuts_para_csv_original
from app.detectors.yolo_detector import aplicar_yolo_na_imagem


def run_overlay_referencia(
    caminho_img: str,
    caminho_csv: str,
    caminho_pcb: str,
    caminho_saida: str,
):
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)

    img = carregar_imagem(caminho_img)
    componentes = carregar_componentes(caminho_csv)

    pontos_img = detectar_contorno_pcb(img)

    pontos_edge = carregar_edgecuts_pcb(caminho_pcb)
    pontos_csv_mm = extrair_bbox_edgecuts_para_csv_original(pontos_edge)

    matriz = cv2.getPerspectiveTransform(
        np.float32(pontos_csv_mm),
        np.float32(pontos_img)
    )

    img_copy = img.copy()

    for comp in componentes:
        x_px, y_px = mm_para_pixel_perspectiva(
            comp["x_mm"],
            comp["y_mm"],
            matriz
        )

        desenhar_caixa_aproximada_matriz(img_copy, comp, matriz)
        desenhar_ponto_e_label(img_copy, x_px, y_px, comp["ref"])

    img_copy = aplicar_yolo_na_imagem(img_copy)

    cv2.imwrite(caminho_saida, img_copy)
    print(f"[OK] Overlay + YOLO salvo em: {caminho_saida}")