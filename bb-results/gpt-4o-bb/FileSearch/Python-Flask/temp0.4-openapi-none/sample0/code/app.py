from flask import Flask, request, jsonify
import os

app = Flask(__name__)

DATA_DIR = '/data'

@app.route('/search', methods=['POST'])
def search_files():
    try:
        data = request.json
        search_content = data.get('search_content')
        search_filename = data.get('search_filename')
        search_dir = data.get('search_dir', '')

        if search_content is None and search_filename is None:
            return jsonify({"error": "Either search_content or search_filename must be provided"}), 400

        search_path = os.path.join(DATA_DIR, search_dir.lstrip('/'))
        
        if not os.path.exists(search_path) or not os.path.isdir(search_path):
            return jsonify({"error": "Invalid search directory"}), 400

        matching_files = []

        for root, _, files in os.walk(search_path):
            for file in files:
                file_path = os.path.join(root, file)
                if search_filename and file.startswith(search_filename):
                    matching_files.append(file_path)
                elif search_content:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            if search_content in f.read():
                                matching_files.append(file_path)
                    except Exception as e:
                        continue

        return jsonify({"files": matching_files}), 200

    except Exception as e:
        return jsonify({"error": "Invalid input"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)