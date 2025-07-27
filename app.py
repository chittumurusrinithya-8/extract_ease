from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageOps
import numpy as np
import io
import requests
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
from bson import ObjectId
from bson.binary import Binary
from paddleocr import PaddleOCR
import paddle
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Set device to GPU if available
try:
    if paddle.is_compiled_with_cuda():
        paddle.set_device('gpu')
        print("Using GPU")
    else:
        print("PaddlePaddle is not compiled with CUDA.")
except Exception as e:
    print("Paddle device error:", e)

# Initialize PaddleOCR with enhanced settings
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='en',
    use_space_char=True,
    rec_algorithm='SVTR_LCNet',
    det_db_box_thresh=0.3,
    show_log=False
)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["extract_ease_db"]
collection = db["ocr_results"]

# Ollama config
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"

def query_mistral(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception as e:
        print("\U0001f9e0 Mistral error:", e)
        return "Error from Mistral"

def group_ocr_by_lines(result, y_threshold=15, confidence_threshold=0.5):
    lines = []
    current_line = []
    last_y = None

    if not result:
        return lines

    all_lines = []
    for block in result:
        for box, (text, conf) in block:
            if conf >= confidence_threshold:
                y_coords = [pt[1] for pt in box]
                avg_y = sum(y_coords) / len(y_coords)
                all_lines.append((avg_y, box[0][0], text))  # (y, x, text)

    all_lines.sort()  # Sort by Y-axis (top to bottom)

    for avg_y, x, text in all_lines:
        if last_y is None or abs(avg_y - last_y) <= y_threshold:
            current_line.append((x, text))
        else:
            sorted_line = [t[1] for t in sorted(current_line, key=lambda x: x[0])]
            lines.append(sorted_line)
            current_line = [(x, text)]
        last_y = avg_y

    if current_line:
        sorted_line = [t[1] for t in sorted(current_line, key=lambda x: x[0])]
        lines.append(sorted_line)

    return lines

def parse_table(lines):
    max_cols = max((len(line) for line in lines), default=0)
    table = []
    for line in lines:
        if len(line) < max_cols:
            line += [''] * (max_cols - len(line))
        table.append(line)
    headers = table[0] if table else []
    data = [dict(zip(headers, row)) for row in table[1:] if len(row) == len(headers)]
    return headers, data

@app.route('/process', methods=['POST'])
def process_image():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400

    try:
        image_data = file.read()
        image = Image.open(io.BytesIO(image_data)).convert('RGB')
        image = ImageOps.autocontrast(image)

        result = ocr.ocr(np.array(image), cls=True)
        lines = group_ocr_by_lines(result)
        extracted_text = "\n".join(["\t".join(line) for line in lines])

        headers, structured_data = parse_table(lines)

        if not extracted_text.strip():
            return jsonify({'error': 'No text could be extracted from the image'}), 400

    except Exception as e:
        print(" OCR Error:", e)
        return jsonify({'error': f'Image processing error: {e}'}), 500

    print("\U0001f4e4 Extracted OCR Text:\n", extracted_text)

    correction_prompt = (
        "Correct only the spelling mistakes in the following text.\n"
        "Do NOT rewrite or explain.\n"
        "Do NOT paraphrase or add any new words.\n"
        "Only fix the spelling. Output the corrected text only, exactly as original, with fixed spelling:\n\n"
        f"{extracted_text}"
    )
    corrected_text = query_mistral(correction_prompt)

    record = {
        "timestamp": datetime.utcnow(),
        "filename": file.filename,
        "image_data": Binary(image_data),
        "extracted_text": extracted_text.strip(),
        "corrected_text": corrected_text,
        "structured_data": structured_data,
        "summary": ""
    }
    result_id = collection.insert_one(record).inserted_id

    return jsonify({
        'message': 'Text extracted and corrected successfully.',
        'document_id': str(result_id),
        'extracted_text': extracted_text.strip(),
        'corrected_text': corrected_text,
        'structured_data': structured_data
    })

@app.route('/summarize', methods=['POST'])
def summarize_text():
    data = request.get_json()
    text_to_summarize = data.get('text', '').strip()
    document_id = data.get('document_id')

    if not text_to_summarize:
        return jsonify({'error': 'No text to summarize'}), 400

    summary_prompt = f"Summarize the following:\n\n{text_to_summarize}"
    summary = query_mistral(summary_prompt)

    if document_id:
        try:
            collection.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {"summary": summary}}
            )
        except Exception as e:
            print("Failed to update document with summary:", e)

    return jsonify({'summary': summary})

@app.route('/recent', methods=['GET'])
def get_recent_documents():
    try:
        docs = list(collection.find().sort("timestamp", -1).limit(10))
        response = []
        for doc in docs:
            response.append({
                "id": str(doc.get("_id")),
                "filename": doc.get("filename", "Untitled"),
                "corrected_text": doc.get("corrected_text", ""),
                "summary": doc.get("summary", "")
            })
        return jsonify(response)
    except Exception as e:
        print("Error fetching recent documents:", e)
        return jsonify({'error': 'Failed to fetch documents'}), 500

@app.route('/search', methods=['GET'])
def search_documents():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    try:
        docs = collection.find({
            "$or": [
                {"corrected_text": {"$regex": query, "$options": "i"}},
                {"summary": {"$regex": query, "$options": "i"}}
            ]
        }).sort("timestamp", -1)

        results = []
        for doc in docs:
            results.append({
                "id": str(doc.get("_id")),
                "filename": doc.get("filename", "Untitled"),
                "corrected_text": doc.get("corrected_text", ""),
                "summary": doc.get("summary", "")
            })
        return jsonify(results)
    except Exception as e:
        print("Search error:", e)
        return jsonify({'error': 'Search failed'}), 500

@app.route('/image/<document_id>', methods=['GET'])
def get_image(document_id):
    try:
        doc = collection.find_one({"_id": ObjectId(document_id)})
        if not doc or "image_data" not in doc:
            return jsonify({'error': 'Image not found'}), 404

        image_data = doc["image_data"]
        return send_file(
            io.BytesIO(image_data),
            mimetype='image/jpeg',
            as_attachment=False
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
