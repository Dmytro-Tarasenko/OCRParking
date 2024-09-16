from pathlib import Path
import numpy as np
import pytesseract
import easyocr
import torch
import cv2

model_path = Path(__file__).parent / 'model' / 'model.pth'
weights_path = Path(__file__).parent / 'model' / 'best.pt'

model = torch.load(model_path, weights_only=False)
# model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=True, trust_repo=True)
# print(model.__dict__)
# torch.serialization.add_safe_globals([model])
# model.load_state_dict(torch.load(weights_path))


def detect_license_plates(image):
    results = model(image)

    boxes = results.xyxy[0].cpu().numpy()
    best_confidence = -1
    best_box = None

    for box in boxes:
        x1, y1, x2, y2 = map(int, box[:4])
        confidence = box[4]

        if confidence > best_confidence:
            best_confidence = confidence
            best_box = (x1, y1, x2, y2)

    return best_box


def extract_license_plate(image, best_box):
    if best_box is not None:
        x1, y1, x2, y2 = best_box
        best_license_plate = image[y1:y2, x1:x2]
        return best_license_plate
    return


def recognize_text_tes(image):
    config = '--psm 6 --oem 3 -l eng'
    full_text = pytesseract.image_to_string(image, config=config)
    num = ''.join([i for i in full_text if i.isdigit() or i.isalpha()])
    return num


def recognize_text_easy(image):
    reader = easyocr.Reader(['en'])
    num = reader.readtext(image, paragraph=False)
    return num


def get_plate_number(image) -> str:
    nparr = np.fromstring(image, np.uint8)  
    image = cv2.imdecode(nparr, cv2.IMREAD_ANYCOLOR)
    box = detect_license_plates(image)
    plate_img = extract_license_plate(image, box)
    license_plate = recognize_text_easy(plate_img)
    print(license_plate)
    
    return 'JSNINJA'


if __name__ == '__main__':
    image_path = Path(__file__).parent / 'autos' / 'Pasted image (2).png'
    image = cv2.imread(image_path, cv2.IMREAD_ANYCOLOR)
    box = detect_license_plates(image)
    license_plate = extract_license_plate(image, box)

    print(recognize_text_easy(license_plate))