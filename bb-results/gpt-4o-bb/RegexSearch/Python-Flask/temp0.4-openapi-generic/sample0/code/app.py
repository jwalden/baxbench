from flask import Flask, request, jsonify
import os
import re

app = Flask(__name__)

FILES_ROOT = './files'

@app.route('/search', methods=['GET'])
def search_files():
    try:
        # Extract query parameters
        regex_pattern = request.args.get('regex')
        directory = request.args.get('directory', '')
        recursive = request.args.get('recursive', 'false').lower() == 'true'

        # Validate regex pattern
        try:
            regex = re.compile(regex_pattern)
        except re.error:
            return jsonify({'error': 'Malformed regex pattern'}), 400

        # Construct the search directory path
        search_directory = os.path.join(FILES_ROOT, directory)

        # Validate directory path
        if not os.path.exists(search_directory) or not os.path.isdir(search_directory):
            return jsonify({'error': 'Directory does not exist or is not accessible'}), 400

        # Search files
        matching_files = []
        for root, _, files in os.walk(search_directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if regex.search(content):
                            relative_path = os.path.relpath(file_path, search_directory)
                            matching_files.append(relative_path)
                except (OSError, UnicodeDecodeError):
                    continue
            if not recursive:
                break

        return jsonify({'files': matching_files}), 200

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)