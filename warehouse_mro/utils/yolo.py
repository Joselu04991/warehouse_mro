import os
from typing import Tuple, List, Dict
from flask import current_app

try:
    from ultralytics import YOLO
    import cv2
except Exception:  # ultralytics no instalado / sin opencv
    YOLO = None
    cv2 = None


_model_cache = {
    "loaded": False,
    "model": None,
}


def _load_model():
    if _model_cache["loaded"]:
        return _model_cache["model"]

    model_path = current_app.config.get("YOLO_MODEL_PATH")
    if not model_path or not os.path.exists(model_path):
        _model_cache["loaded"] = True
        _model_cache["model"] = None
        return None

    if YOLO is None:
        _model_cache["loaded"] = True
        _model_cache["model"] = None
        return None

    model = YOLO(model_path)
    _model_cache["loaded"] = True
    _model_cache["model"] = model
    return model


def detect_bultos(image_path: str) -> Tuple[int, List[Dict], str]:
    """
    Retorna:
      count: número estimado de bultos
      detections: lista de dicts con bbox y score
      annotated_path: ruta de la imagen anotada (o None)
    """
    model = _load_model()
    if model is None or cv2 is None:
        return 0, [], None

    results = model(image_path)
    detections = []
    count = 0

    img = cv2.imread(image_path)
    if img is None:
        return 0, [], None

    for r in results:
        boxes = r.boxes
        for b in boxes:
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            conf = float(b.conf[0])
            cls = int(b.cls[0])
            detections.append(
                {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "conf": conf, "cls": cls}
            )
            count += 1
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

    annotated_path = os.path.splitext(image_path)[0] + "_yolo.jpg"
    cv2.imwrite(annotated_path, img)

    return count, detections, annotated_path
