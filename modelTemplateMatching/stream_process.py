from flask import Flask, request, jsonify
import base64
from PIL import Image
import io
from extractor import extract_fields

app = Flask(__name__)

@app.route('/streamProcess', methods=['POST'])
def stream_process():
    try:
        data = request.get_json(force=True)
        if not data or 'image' not in data:
            return jsonify({"error": "Image data missing"}), 400

        image_data = base64.b64decode(data['image'])
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        results = extract_fields(image)

        return jsonify(results), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500
