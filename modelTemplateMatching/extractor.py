from flask import Flask, request
from PIL import Image
import numpy as np
import cv2
import os
from datetime import datetime
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)


TEMPLATE_NUMERIC_FOLDER = 'templates_ocra'
TEMPLATE_TEXT_FOLDER = 'templates_personal'

def tesseract_ocr(roi_img):
    config = "--psm 6"
    return pytesseract.image_to_string(roi_img, config=config).strip()


# ==== Load Templates ====
def load_templates(folder_path):
    templates = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".png"):
            label = os.path.splitext(filename)[0]
            img = cv2.imread(os.path.join(folder_path, filename), cv2.IMREAD_GRAYSCALE)
            _, bin_img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
            templates[label] = bin_img
    return templates

templates_ocra = load_templates(TEMPLATE_NUMERIC_FOLDER)      # NIK
templates_personal = load_templates(TEMPLATE_TEXT_FOLDER)     # Nama, Alamat, Pekerjaan

# ==== ROI ====
def auto_expand_roi(gray_img, y_start, y_end, x_start, x_end, margin=0):
    h, w = gray_img.shape
    y1 = max(0, y_start - margin)
    y2 = min(h, y_end + margin)
    x1 = max(0, x_start - margin)
    x2 = min(w, x_end + margin)
    return gray_img[y1:y2, x1:x2]

# ==== Character Segmentation ====
def segment_characters_with_position(roi_img):
    _, thresh = cv2.threshold(roi_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    thresh = 255 - thresh
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(thresh, connectivity=8)
    chars = []
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        if area > 20 and h > 8:
            char_img = roi_img[y:y+h, x:x+w]
            chars.append((x, char_img))
    chars.sort(key=lambda x: x[0])
    return chars

# ==== Template Matching ====
def match_template(char_img, templates):
    best_score = -1
    best_char = None
    char_img = cv2.resize(char_img, (40, 40))
    _, char_img = cv2.threshold(char_img, 127, 255, cv2.THRESH_BINARY)
    for label, tmpl in templates.items():
        tmpl_resized = cv2.resize(tmpl, (40, 40))
        result = cv2.matchTemplate(char_img, tmpl_resized, cv2.TM_CCOEFF_NORMED)
        _, score, _, _ = cv2.minMaxLoc(result)
        if score > best_score:
            best_score = score
            best_char = label
    return best_char

# ==== OCR Logic ====
def recognize_text(roi_img, templates):
    chars_with_pos = segment_characters_with_position(roi_img)
    result = ""

    for _, char_img in chars_with_pos:
        matched = match_template(char_img, templates)
        result += matched if matched else '?'
    
    return result

# ==== Main Extraction ====
def extract_fields(image: Image):
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    rois = {
        "NIK": auto_expand_roi(gray, 163, 163+97, 474, 474+829),
        "Nama": auto_expand_roi(gray, 295, 295+46, 516, 516+488),
        "Alamat": auto_expand_roi(gray, 459, 459+58, 515, 515+584),
        "Pekerjaan": auto_expand_roi(gray, 792, 792+53, 516, 516+595),
    }

    results = {}
    for field, roi in rois.items():
        templates = templates_ocra if field == "NIK" else templates_personal
        if field == "NIK":
            result = recognize_text(roi, templates_ocra)  # Use template matching
        else:
            result = tesseract_ocr(roi)  # More flexible Tesseract OCR
        results[field] = result
        cv2.imwrite(f"debug_roi_{field}.png", roi)

    return results