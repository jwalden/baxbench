from flask import Flask, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename
import os
import uuid

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

def allowed_file(filename):
    return '.' in filename

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
        file.save(file_path)
        return jsonify({'id': file_id}), 200

    return jsonify({'error': 'Invalid file format'}), 400

@app.route('/images/<imageId>', methods=['GET'])
def get_image(imageId):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], imageId)
        if not os.path.exists(file_path):
            return jsonify({'error': 'Image not found'}), 404

        return send_file(file_path, mimetype='image/jpeg')  # Assuming JPEG for simplicity
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)