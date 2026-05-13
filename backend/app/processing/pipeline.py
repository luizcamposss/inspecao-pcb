import os
import cv2
import numpy as np

from app.processing.draw import (
    calcular_caixa_componente_px,
    desenhar_footprint_status,
    desenhar_box_yolo_status,
)

from app.processing.parser import carregar_componentes
from app.processing.align import carregar_imagem, detectar_contorno_pcb
from app.kicad.pcb_parser import carregar_edgecuts_pcb, extrair_bbox_edgecuts_para_csv_original

from app.detectors.yolo_detector import detectar_yolo
from app.processing.validation import validar_componente


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

    detections = detectar_yolo(img)

    img_resultado = img.copy()
    deteccoes_usadas = set()

    for comp in componentes:
        caixa_info = calcular_caixa_componente_px(
            comp=comp,
            matriz_transformacao=matriz,
            padding_px=2,
        )

        validacao = validar_componente(
            img_original=img,
            comp=comp,
            caixa_info=caixa_info,
            detections=detections,
            deteccoes_usadas=deteccoes_usadas,
        )

        nome_comp = comp["ref"]
        texto = f"{nome_comp} {validacao['status']}"

        if validacao["status"] == "presente":
            desenhar_box_yolo_status(
                img_resultado,
                validacao["yolo"]["box"],
                (0, 255, 0),
                None,
            )

        elif validacao["status"] == "incerto":
            desenhar_footprint_status(
                img_resultado,
                caixa_info["pontos"],
                (0, 255, 255),
                texto,
            )

        else:
            desenhar_footprint_status(
                img_resultado,
                caixa_info["pontos"],
                (0, 0, 255),
                texto,
            )

    cv2.imwrite(caminho_saida, img_resultado)
    print(f"[OK] Overlay + validação salvo em: {caminho_saida}")