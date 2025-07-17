from flask import Flask, request
from PIL import Image
import numpy as np
import cv2
import os
from datetime import datetime
from extractor import extract_fields


UPLOAD_FOLDER = 'uploads'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def process_image_route():
    if 'file' not in request.files:
        return {"error": "No file part"}, 400

    file = request.files['file']
    if file.filename == '':
        return {"error": "No selected file"}, 400

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    saved_path = os.path.join(UPLOAD_FOLDER, f'ktp_{timestamp}.jpg')
    file.save(saved_path)

    image = Image.open(saved_path)

    try:
        fields = extract_fields(image)
        return fields
    except Exception as e:
        return {"error": f"Processing failed: {str(e)}"}, 500
