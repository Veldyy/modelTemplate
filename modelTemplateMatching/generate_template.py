import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

os.makedirs("templates_personal", exist_ok=True)
os.makedirs("templates_ocra", exist_ok=True)


helvetica = "Helvetica.ttf"
helveticaBold = "Helvetica-Bold.ttf"
arial = "Arial.ttf"
arialBold = "Arial Bold.ttf"
# Separate sizes for each font
personal_font_config = {
    "target_size": (50, 40),
    "font_size": 52,
    "font_path": helvetica # as default
}

ocra_config = {
    "target_size": (40, 30),  # works well for NIK
    "font_size": 48,
    "font_path": "OCRA.ttf"
}

def create_char_template(char, config):
    img = Image.new("L", (100, 100), 255)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(config["font_path"], config["font_size"])
    bbox = draw.textbbox((0, 0), char, font=font)
    x = (100 - (bbox[2] - bbox[0])) // 2
    y = (100 - (bbox[3] - bbox[1])) // 2
    draw.text((x, y), char, font=font, fill=0)

    img_np = np.array(img)
    coords = cv2.findNonZero(255 - img_np)
    if coords is not None:
        x, y, w, h = cv2.boundingRect(coords)
        cropped = img_np[y:y+h, x:x+w]
    else:
        cropped = img_np

    h, w = cropped.shape
    scale = min(config["target_size"][0] / h, config["target_size"][1] / w)
    resized = cv2.resize(cropped, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
    canvas = np.ones(config["target_size"], dtype=np.uint8) * 255
    x_off = (config["target_size"][1] - resized.shape[1]) // 2
    y_off = (config["target_size"][0] - resized.shape[0]) // 2
    canvas[y_off:y_off+resized.shape[0], x_off:x_off+resized.shape[1]] = resized

    return canvas

# Generate Helvetica templates (for Nama, Alamat, Pekerjaan)
# ==== Generate Helvetica templates (for Nama, Alamat, Pekerjaan) ====
chars_arial = ["O"]
chars_arial_bold = ["L", "I"]
chars_helvetica_bold = ["M", "E", "O"]
chars_default = [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                 if c not in chars_arial + chars_arial_bold + chars_helvetica_bold]

font_groups = [
    (chars_arial, arial),
    (chars_arial_bold, arialBold),
    (chars_helvetica_bold, helveticaBold),
    (chars_default, personal_font_config["font_path"]),
]

for group, font_path in font_groups:
    for char in group:
        config = {**personal_font_config, "font_path": font_path}
        tmpl = create_char_template(char, config)
        cv2.imwrite(f"templates_personal/{char}.png", tmpl)



# Generate OCRA templates (for NIK)
for char in "0123456789":
    tmpl = create_char_template(char, ocra_config)
    cv2.imwrite(f"templates_ocra/{char}.png", tmpl)
