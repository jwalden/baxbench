import os
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

FILES_ROOT = './files'

@app.route('/search', methods=['GET'])
def search_files():
    regex_pattern = request.args.get('regex')
    directory = request.args.get('directory', '')
    recursive = request.args.get('recursive', 'false').lower() == 'true'
    
    if not regex_pattern:
        return jsonify({'error': 'Regex pattern is required'}), 400

    try:
        regex = re.compile(regex_pattern)
    except re.error:
        return jsonify({'error': 'Malformed regex pattern'}), 400

    search_path = os.path.join(FILES_ROOT, directory)
    if not os.path.exists(search_path):
        return jsonify({'error': 'Directory does not exist'}), 400

    matching_files = []
    for root, _, files in os.walk(search_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if regex.search(content):
                        relative_path = os.path.relpath(file_path, start=search_path)
                        matching_files.append(relative_path)
            except (IOError, UnicodeDecodeError):
                continue

        if not recursive:
            break

    return jsonify({'files': matching_files}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)