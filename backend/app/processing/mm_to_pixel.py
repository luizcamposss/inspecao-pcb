from typing import List, Dict, Tuple
import cv2
import numpy as np

def mm_para_pixel_perspectiva(x_mm: float, y_mm: float, matriz_transformacao) -> tuple[int,int]:
    pontos_mm = np.float32([[[x_mm,y_mm]]])

    pontos_foto = cv2.perspectiveTransform(pontos_mm, matriz_transformacao)

    x_px = int(round(pontos_foto[0][0][0]))
    y_px = int(round(pontos_foto[0][0][1]))

    return x_px, y_px