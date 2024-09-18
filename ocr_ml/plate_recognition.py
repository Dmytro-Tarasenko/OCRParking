from pathlib import Path
from collections import namedtuple
from typing import List

import numpy as np
# import pytesseract
import easyocr
import torch
import cv2

model_path = Path(__file__).parent / 'model' / 'model.pth'
weights_path = Path(__file__).parent / 'model' / 'best.pt'

Recognition = namedtuple('Recognition', ['box', 'text', 'confidence'])

model = torch.load(model_path, weights_only=False)


def detect_license_plates(image):
    """
        Detects the license plate in an image using an object detection model.

        Args:
            image (numpy.ndarray): The input image in which to detect the license plate.

        Returns:
            tuple: Coordinates (x1, y1, x2, y2) of the detected license plate's bounding box with the highest confidence.
                   If no box is found, returns None.
        """
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
    """
        Extracts the detected license plate from the image based on the bounding box.

        Args:
            image (numpy.ndarray): The input image containing the license plate.
            best_box (tuple): A tuple containing the coordinates (x1, y1, x2, y2) of the license plate bounding box.

        Returns:
            numpy.ndarray: The cropped image of the license plate.
                          If no box is found, returns None.
        """
    if best_box is not None:
        x1, y1, x2, y2 = best_box
        best_license_plate = image[y1:y2, x1:x2]
        return best_license_plate
    return


# def recognize_text_tes(image):
#     config = '--psm 6 --oem 3 -l eng'
#     full_text = pytesseract.image_to_string(image, config=config)
#     num = ''.join([i for i in full_text if i.isdigit() or i.isalpha()])
#     return num


def recognize_text_easy(image):
    """
        Recognizes text from the extracted license plate image using EasyOCR.

        Args:
            image (numpy.ndarray): The image of the license plate to recognize text from.

        Returns:
            list: A list of recognized text data, where each element is a tuple containing the bounding box and recognized text.
        """
    reader = easyocr.Reader(['en'])
    num = reader.readtext(image, paragraph=False)
    return num


def get_plate_number(image) -> List[Recognition]:
    """
        Processes the input image to detect, extract, and recognize the license plate number.

        Args:
            image (bytes): The input image in byte format, representing the vehicle's image.

        Returns:
            List[Recognition]: A list of recognized license plate text and bounding boxes.
        """
    nparr = np.fromstring(image, np.uint8)  
    image = cv2.imdecode(nparr, cv2.IMREAD_ANYCOLOR)
    box = detect_license_plates(image)
    plate_img = extract_license_plate(image, box)
    
    # license_plate = recognize_text_tes(plate_img)
    license_plate = [Recognition(*i) for i in recognize_text_easy(plate_img)]
    print(license_plate[0].text)
    
    return license_plate


if __name__ == '__main__':
    image_path = Path(__file__).parent / 'autos' / 'Pasted image (2).png'
    image = cv2.imread(image_path, cv2.IMREAD_ANYCOLOR)
    box = detect_license_plates(image)
    license_plate = extract_license_plate(image, box)

    print(recognize_text_easy(license_plate))