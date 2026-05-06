import cv2
import numpy as np

def verificar_presenca_componente_desvio_padrao_sem_reflexo(img, pontos_poligono, limite_presenca=12.0):
    
    pontos_poligono = np.array(pontos_poligono, dtype=np.float32)
    centro = np.mean(pontos_poligono, axis=0)

    pontos_encolhidos = centro + (pontos_poligono - centro) * 0.35
    pontos_encolhidos = np.int32(pontos_encolhidos)
    
    x, y, w, h = cv2.boundingRect(np.int32(pontos_encolhidos))

    altura_img, largura_img = img.shape[:2]
    if w <= 0 or h <=0 or x < 0 or y < 0 or (x+w) > largura_img or (y+h) > altura_img:
        return False, 0.0
    
    recorte_img = img[y:y+h, x:x+w]
    gray = cv2.cvtColor(recorte_img, cv2.COLOR_BGR2GRAY)

    gray = cv2.medianBlur(gray, 3)

    recorte_mascara = np.zeros((h, w), dtype=np.uint8)

    pontos_deslocados = pontos_encolhidos - [x, y]
    cv2.fillPoly(recorte_mascara, [pontos_deslocados], 255)

    _, stddev = cv2.meanStdDev(gray, mask=recorte_mascara)

    nivel_textura = stddev[0][0] if stddev is not None else 0.0

    esta_presente = nivel_textura > limite_presenca

    return esta_presente, nivel_textura  
