import cv2
import numpy as np
from app.processing.analyze import  verificar_presenca_componente_desvio_padrao_sem_reflexo


def desenhar_ponto_e_label(img, x_px, y_px, texto):
    cv2.circle(img, (x_px, y_px), 4, (0, 255, 0), -1)
    cv2.putText(
        img,
        texto,
        (x_px + 6, y_px - 6),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.35,
        (0, 255, 0),
        1,
        cv2.LINE_AA,
    )



def desenhar_caixa_aproximada_matriz(img, comp, matriz_transformacao, padding_px=0):
    w_mm = comp["w_mm"]
    h_mm = comp["h_mm"]
    x_mm = comp["x_mm"]
    y_mm = comp["y_mm"]
    rot = comp["rot"]

    img_copy = img.copy()

    if abs(rot) % 180 == 90:
        w_mm = h_mm
        h_mm = w_mm

    cantos_mm = np.float32([[
        [x_mm - w_mm / 2, y_mm - h_mm / 2],
        [x_mm + w_mm / 2, y_mm - h_mm / 2],
        [x_mm + w_mm / 2, y_mm + h_mm / 2],
        [x_mm - w_mm / 2, y_mm + h_mm / 2]
    ]])

    cantos_px = cv2.perspectiveTransform(cantos_mm, matriz_transformacao)
    pontos = cantos_px[0]

    centro_px = np.mean(pontos, axis=0)

    pontos_com_padding = []
    for pt in pontos:
        vetor_direcao = pt - centro_px

        distancia = np.linalg.norm(vetor_direcao)

        if distancia > padding_px:
            vetor_movimento = (vetor_direcao / distancia) * padding_px
            novo_pt = pt+vetor_movimento
        else:
            novo_pt = pt
        
        pontos_com_padding.append(novo_pt)

    cantos_finais_px = np.int32([pontos_com_padding])


    esta_presente, score = verificar_presenca_componente_desvio_padrao_sem_reflexo(img_copy, cantos_finais_px)
    color = (0,255,0) if esta_presente else (0,0,255)


    cv2.polylines(img, cantos_finais_px, isClosed=True, color=color, thickness=2)

def calcular_caixa_componente_px(comp, matriz_transformacao, padding_px=0):
    w_mm = comp["w_mm"]
    h_mm = comp["h_mm"]
    x_mm = comp["x_mm"]
    y_mm = comp["y_mm"]
    rot = comp.get("rot", 0)

    if abs(rot) % 180 == 90:
        w_mm, h_mm = h_mm, w_mm

    cantos_mm = np.float32([[
        [x_mm - w_mm / 2, y_mm - h_mm / 2],
        [x_mm + w_mm / 2, y_mm - h_mm / 2],
        [x_mm + w_mm / 2, y_mm + h_mm / 2],
        [x_mm - w_mm / 2, y_mm + h_mm / 2],
    ]])

    cantos_px = cv2.perspectiveTransform(cantos_mm, matriz_transformacao)
    pontos = cantos_px[0]

    centro_px = np.mean(pontos, axis=0)

    pontos_com_padding = []

    for pt in pontos:
        vetor_direcao = pt - centro_px
        distancia = np.linalg.norm(vetor_direcao)

        if distancia > 0:
            vetor_movimento = (vetor_direcao / distancia) * padding_px
            novo_pt = pt + vetor_movimento
        else:
            novo_pt = pt

        pontos_com_padding.append(novo_pt)

    pontos_finais = np.int32([pontos_com_padding])
    x, y, w, h = cv2.boundingRect(pontos_finais)

    return {
        "pontos": pontos_finais,
        "box": [int(x), int(y), int(x + w), int(y + h)],
    }


def desenhar_footprint_status(img, pontos, cor, texto):
    cv2.polylines(img, pontos, isClosed=True, color=cor, thickness=2)

    x, y, _, _ = cv2.boundingRect(pontos)

    cv2.putText(
        img,
        texto,
        (x, max(y - 6, 15)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        cor,
        1,
        cv2.LINE_AA,
    )


def desenhar_box_yolo_status(img, box, cor, texto=None):
    x1, y1, x2, y2 = map(int, box)

    cv2.rectangle(img, (x1, y1), (x2, y2), cor, 2)

    if texto:
        cv2.putText(
            img,
            texto,
            (x1, max(y1 - 6, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            cor,
            1,
            cv2.LINE_AA,
        )