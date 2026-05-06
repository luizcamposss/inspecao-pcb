
import cv2
import numpy as np

def carregar_imagem(caminho: str):
    img = cv2.imread(caminho)
    if img is None:
        raise FileNotFoundError(f"Não foi possível abrir a imagem: {caminho}")
    return img

def detectar_contorno_pcb(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower = np.array([70, 35, 35])
    upper = np.array([100, 255, 255])

    mask = cv2.inRange(hsv, lower, upper)

    kernel = np.ones((9, 9), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        raise Exception("Nenhum contorno de PCB encontrado.")

    maior = max(contours, key=cv2.contourArea)

    rect = cv2.minAreaRect(maior)
    box = cv2.boxPoints(rect)
    box = np.float32(box)

    return ordenar_pontos(box)

def ordenar_pontos(pts):
    pts = pts.astype("float32")

    soma = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)

    return np.array([
        pts[np.argmin(soma)],     # topo-esquerda
        pts[np.argmin(diff)],     # topo-direita
        pts[np.argmax(soma)],     # baixo-direita
        pts[np.argmax(diff)]      # baixo-esquerda
    ])
