from flask import Flask, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename
import os
import uuid

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_id = str(uuid.uuid4())
        unique_filename = f"{unique_id}.{file_extension}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        return jsonify({'id': unique_id}), 200
    else:
        return jsonify({'error': 'File type not allowed'}), 400

@app.route('/images/<imageId>', methods=['GET'])
def get_image(imageId):
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        for file in files:
            if file.startswith(imageId):
                return send_file(os.path.join(app.config['UPLOAD_FOLDER'], file), mimetype='image/*')
        return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)