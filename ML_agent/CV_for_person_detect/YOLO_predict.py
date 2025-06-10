from ultralytics import YOLO

model = YOLO(r"cv_for_person_detect/yolov5n.pt")

def detect_person(img_path: str, conf: float = 0.58) -> bool:
    res = model(img_path, classes=[0], conf=conf, save=True)
    print(res[0].boxes.cls.tolist())
    return bool(res[0].boxes.cls.tolist())

