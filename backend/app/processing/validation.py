from app.processing.analyze import verificar_presenca_componente_desvio_padrao_sem_reflexo


def area_box(box):
    x1, y1, x2, y2 = box
    return max(0, x2 - x1) * max(0, y2 - y1)


def intersecao_box(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    x1 = max(ax1, bx1)
    y1 = max(ay1, by1)
    x2 = min(ax2, bx2)
    y2 = min(ay2, by2)

    return max(0, x2 - x1) * max(0, y2 - y1)


def iou_box(box_a, box_b):
    inter = intersecao_box(box_a, box_b)
    union = area_box(box_a) + area_box(box_b) - inter

    if union <= 0:
        return 0.0

    return inter / union


def centro_box(box):
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def ponto_dentro_box(ponto, box):
    x, y = ponto
    x1, y1, x2, y2 = box
    return x1 <= x <= x2 and y1 <= y <= y2


def escolher_melhor_match_yolo(box_esperada, detections, deteccoes_usadas):
    melhor = None
    melhor_score = 0.0

    for idx, det in enumerate(detections):
        if idx in deteccoes_usadas:
            continue

        x1, y1, x2, y2, label, tipo, conf = det

        if tipo != "comp":
            continue

        box_yolo = [x1, y1, x2, y2]

        iou = iou_box(box_esperada, box_yolo)
        inter = intersecao_box(box_esperada, box_yolo)

        area_esp = area_box(box_esperada)
        area_yolo = area_box(box_yolo)

        cobertura_esperada = inter / area_esp if area_esp > 0 else 0.0
        cobertura_yolo = inter / area_yolo if area_yolo > 0 else 0.0

        centro_yolo = centro_box(box_yolo)
        centro_dentro = ponto_dentro_box(centro_yolo, box_esperada)

        score = max(
            iou,
            cobertura_esperada,
            cobertura_yolo,
            0.80 if centro_dentro else 0.0,
        )

        if score > melhor_score:
            melhor_score = score
            melhor = {
                "idx": idx,
                "box": box_yolo,
                "label": label,
                "conf": conf,
                "iou": iou,
                "cobertura_esperada": cobertura_esperada,
                "cobertura_yolo": cobertura_yolo,
                "centro_dentro": centro_dentro,
                "score": score,
            }

    return melhor


def validar_componente(img_original, comp, caixa_info, detections, deteccoes_usadas):
    box_esperada = caixa_info["box"]
    pontos_footprint = caixa_info["pontos"]

    melhor = escolher_melhor_match_yolo(
        box_esperada=box_esperada,
        detections=detections,
        deteccoes_usadas=deteccoes_usadas,
    )

    if melhor:
        if melhor["centro_dentro"]:
            deteccoes_usadas.add(melhor["idx"])
            return {
                "status": "presente",
                "metodo": "yolo_centro",
                "score": melhor["score"],
                "yolo": melhor,
            }

        if melhor["iou"] >= 0.15:
            deteccoes_usadas.add(melhor["idx"])
            return {
                "status": "presente",
                "metodo": "yolo_iou",
                "score": melhor["iou"],
                "yolo": melhor,
            }

        if melhor["cobertura_esperada"] >= 0.25:
            deteccoes_usadas.add(melhor["idx"])
            return {
                "status": "presente",
                "metodo": "yolo_cobertura",
                "score": melhor["cobertura_esperada"],
                "yolo": melhor,
            }

    if melhor:
        if melhor["iou"] >= 0.05 or melhor["cobertura_esperada"] >= 0.10:
            return {
                "status": "incerto",
                "metodo": "yolo_fraco",
                "score": melhor["score"],
                "yolo": melhor,
            }

    presente_textura, score_textura = verificar_presenca_componente_desvio_padrao_sem_reflexo(
        img_original,
        pontos_footprint
    )

    if presente_textura:
        return {
            "status": "incerto",
            "metodo": "textura",
            "score": float(score_textura),
            "yolo": melhor,
        }

    return {
        "status": "ausente",
        "metodo": "sem_match",
        "score": 0.0,
        "yolo": melhor,
    }