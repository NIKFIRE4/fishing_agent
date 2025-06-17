import base64
import numpy as np
from PIL import Image
from io import BytesIO
from ultralytics import YOLO

# model = YOLO("cv_for_person_detect/yolov5n.pt")

# def detect_person(image_base64: str, conf: float = 0.58) -> bool:
#     image_data = base64.b64decode(image_base64)
#     image = Image.open(BytesIO(image_data))
#     if image.mode != 'RGB':
#         image = image.convert('RGB')
#     image_array = np.array(image)
#     results = model(image_array, classes=[0], conf=conf, save=False, verbose=False)
#     has_person = len(results[0].boxes) > 0
#     return has_person


