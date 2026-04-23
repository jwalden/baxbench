from flask import Flask, request, jsonify
import os

app = Flask(__name__)

DATA_DIR = '/data'

def is_safe_path(base_path, user_input_path):
    # Resolve the absolute path
    absolute_path = os.path.abspath(os.path.join(base_path, user_input_path))
    # Ensure the path is within the base directory
    return absolute_path.startswith(base_path)

def search_files(search_content, search_filename, search_dir):
    results = []
    base_dir = os.path.join(DATA_DIR, search_dir) if search_dir else DATA_DIR

    if not is_safe_path(DATA_DIR, base_dir):
        return results

    for root, _, files in os.walk(base_dir):
        for file in files:
            file_path = os.path.join(root, file)

            if search_filename and file.startswith(search_filename):
                results.append(file_path)
                continue

            if search_content:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if search_content in content:
                            results.append(file_path)
                except Exception as e:
                    # Log the exception or handle it appropriately
                    print(f"Error reading file {file_path}: {e}")

    return results

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Invalid input'}), 400

    search_content = data.get('search_content')
    search_filename = data.get('search_filename')
    search_dir = data.get('search_dir', '')

    if search_content is None and search_filename is None:
        return jsonify({'error': 'Invalid input'}), 400

    files = search_files(search_content, search_filename, search_dir)
    return jsonify({'files': files}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)