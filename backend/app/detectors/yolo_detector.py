from pathlib import Path
import cv2
from ultralytics import YOLO


BASE_DIR = Path(__file__).resolve().parents[2]
MODELS_DIR = BASE_DIR / "models"

COMPONENTES_DIR = MODELS_DIR / "componentes"
DEFEITOS_DIR = MODELS_DIR / "defeitos"


def carregar_modelos(pasta: Path):
    modelos = []

    if not pasta.exists():
        print(f"[YOLO] Pasta não encontrada: {pasta}")
        return modelos

    for arquivo in pasta.glob("*.pt"):
        print(f"[YOLO] Carregando modelo: {arquivo}")
        modelos.append(YOLO(str(arquivo)))

    return modelos


modelos_componentes = carregar_modelos(COMPONENTES_DIR)
modelos_defeitos = carregar_modelos(DEFEITOS_DIR)


def tem_sobreposicao(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    return not (x2 < x1 or y2 < y1)


def iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter = max(0, x2 - x1) * max(0, y2 - y1)

    area1 = max(0, box1[2] - box1[0]) * max(0, box1[3] - box1[1])
    area2 = max(0, box2[2] - box2[0]) * max(0, box2[3] - box2[1])

    union = area1 + area2 - inter

    return inter / union if union > 0 else 0


def aplicar_nms(detections, iou_thresh=0.9):
    detections = sorted(detections, key=lambda x: x[6], reverse=True)
    resultado = []

    while detections:
        melhor = detections.pop(0)
        resultado.append(melhor)

        detections = [
            det for det in detections
            if not (
                det[4] == melhor[4]
                and iou(det, melhor) > iou_thresh
            )
        ]

    return resultado


def caixas_proximas(box1, box2, margem=3):
    return not (
        box1[2] + margem < box2[0] or
        box1[0] - margem > box2[2] or
        box1[3] + margem < box2[1] or
        box1[1] - margem > box2[3]
    )


def merge_boxes(box1, box2):
    return [
        min(box1[0], box2[0]),
        min(box1[1], box2[1]),
        max(box1[2], box2[2]),
        max(box1[3], box2[3]),
    ]


def juntar_caixas(detections):
    detections = list(detections)
    resultado = []

    while detections:
        atual = detections.pop(0)
        x1, y1, x2, y2, label, tipo, conf = atual

        mudou = True

        while mudou:
            mudou = False

            for i, det in enumerate(detections):
                x1b, y1b, x2b, y2b, label_b, tipo_b, conf_b = det

                if label == label_b and caixas_proximas(
                    (x1, y1, x2, y2),
                    (x1b, y1b, x2b, y2b),
                    margem=3
                ):
                    x1, y1, x2, y2 = merge_boxes(
                        (x1, y1, x2, y2),
                        (x1b, y1b, x2b, y2b)
                    )

                    detections.pop(i)
                    mudou = True
                    break

        resultado.append((x1, y1, x2, y2, label, tipo, conf))

    return resultado


def adicionar_componentes(img, results, detections, boxes_ignoradas=None):
    ignorar_classes = ["pins", "pads"]
    boxes = results.boxes.xyxy.cpu().numpy()
    names = results.names

    area_img = img.shape[0] * img.shape[1]

    for i, box in enumerate(boxes):
        if boxes_ignoradas is not None:
            if any(tem_sobreposicao(box, outra) for outra in boxes_ignoradas):
                continue

        x1, y1, x2, y2 = map(int, box)

        conf = float(results.boxes.conf[i])
        cls = int(results.boxes.cls[i])
        label = names[cls]

        if label.lower() in ignorar_classes:
            continue

        if label.lower() == "capacitor":
            area = (box[2] - box[0]) * (box[3] - box[1])

            if area <= area_img * 0.00022:
                continue

        detections.append((x1, y1, x2, y2, label, "comp", conf))

    detections = aplicar_nms(detections)
    detections = juntar_caixas(detections)

    return detections, boxes


def adicionar_defeitos(img, results, detections, boxes_componentes):
    boxes_defeitos = results.boxes.xyxy.cpu().numpy()
    names_defeitos = results.names

    area_img = img.shape[0] * img.shape[1]

    for i, box_def in enumerate(boxes_defeitos):
        ignorar = False

        for box_comp in boxes_componentes:
            if tem_sobreposicao(box_def, box_comp):
                area = (box_comp[2] - box_comp[0]) * (box_comp[3] - box_comp[1])

                if area > area_img * 0.001:
                    ignorar = True
                    break

        if ignorar:
            continue

        x1, y1, x2, y2 = map(int, box_def)
        roi = img[y1:y2, x1:x2]

        if roi.size == 0:
            continue

        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        if gray_roi.mean() > 100:
            continue

        conf = float(results.boxes.conf[i])
        cls = int(results.boxes.cls[i])
        label = names_defeitos[cls]

        detections.append((x1, y1, x2, y2, label, "def", conf))

    return detections


def detectar_yolo(img):
    detections = []
    boxes_componentes_total = []

    if not modelos_componentes and not modelos_defeitos:
        print("[YOLO] Nenhum modelo carregado.")
        return detections

    for modelo in modelos_componentes:
        results = modelo(img, conf=0.1)[0]

        detections, boxes_modelo = adicionar_componentes(
            img=img,
            results=results,
            detections=detections,
            boxes_ignoradas=boxes_componentes_total
        )

        boxes_componentes_total.extend(list(boxes_modelo))

    for modelo in modelos_defeitos:
        results = modelo(img, conf=0.09)[0]

        detections = adicionar_defeitos(
            img=img,
            results=results,
            detections=detections,
            boxes_componentes=boxes_componentes_total
        )

    return detections


def desenhar_yolo(img, detections):
    for x1, y1, x2, y2, label, tipo, conf in detections:
        cor = (255, 0, 0) if tipo == "comp" else (0, 0, 255)

        cv2.rectangle(img, (x1, y1), (x2, y2), cor, 2)

        texto = f"{label} {conf:.2f}"

        cv2.putText(
            img,
            texto,
            (x1, max(y1 - 6, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            cor,
            1,
            cv2.LINE_AA
        )

    return img


def aplicar_yolo_na_imagem(img):
    detections = detectar_yolo(img)
    return desenhar_yolo(img, detections)