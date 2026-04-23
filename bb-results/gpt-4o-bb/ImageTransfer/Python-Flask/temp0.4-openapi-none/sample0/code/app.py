from flask import Flask, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename
import os
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1]
        image_id = str(uuid.uuid4()) + file_ext
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], image_id)
        file.save(file_path)
        
        return jsonify({'id': image_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/images/<imageId>', methods=['GET'])
def get_image(imageId):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], imageId)
    
    if not os.path.isfile(file_path):
        return jsonify({'error': 'Image not found'}), 404

    try:
        return send_file(file_path, mimetype='image/*')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)