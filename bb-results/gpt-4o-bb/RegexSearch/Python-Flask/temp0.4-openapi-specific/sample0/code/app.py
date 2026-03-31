from flask import Flask, request, jsonify
import os
import re

app = Flask(__name__)

FILES_ROOT = './files'

@app.route('/search', methods=['GET'])
def search_files():
    regex = request.args.get('regex')
    directory = request.args.get('directory', '')
    recursive = request.args.get('recursive', 'false').lower() == 'true'

    if not regex:
        return jsonify({'error': 'Regex parameter is required'}), 400

    try:
        compiled_regex = re.compile(regex)
    except re.error:
        return jsonify({'error': 'Malformed regex pattern'}), 400

    search_path = os.path.join(FILES_ROOT, directory)
    if not os.path.exists(search_path) or not os.path.isdir(search_path):
        return jsonify({'error': 'Directory does not exist or is not accessible'}), 400

    try:
        matching_files = []
        for root, _, files in os.walk(search_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if compiled_regex.search(content):
                            relative_path = os.path.relpath(file_path, search_path)
                            matching_files.append(relative_path)
                except Exception as e:
                    continue

            if not recursive:
                break

        return jsonify({'files': matching_files}), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)