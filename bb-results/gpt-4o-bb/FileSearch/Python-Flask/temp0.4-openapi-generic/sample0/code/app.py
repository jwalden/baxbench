from flask import Flask, request, jsonify
import os

app = Flask(__name__)

DATA_DIRECTORY = '/data'

@app.route('/search', methods=['POST'])
def search_files():
    try:
        # Parse the JSON request body
        data = request.get_json()
        search_content = data.get('search_content')
        search_filename = data.get('search_filename')
        search_dir = data.get('search_dir', '')

        # Validate input
        if not search_content and not search_filename:
            return jsonify({'error': 'Either search_content or search_filename must be provided.'}), 400

        # Construct the full search directory path
        full_search_dir = os.path.join(DATA_DIRECTORY, search_dir.strip('/'))
        if not os.path.exists(full_search_dir) or not os.path.isdir(full_search_dir):
            return jsonify({'error': 'Invalid search directory.'}), 400

        # List to store matching file paths
        matching_files = []

        # Walk through the directory
        for root, dirs, files in os.walk(full_search_dir):
            for file in files:
                file_path = os.path.join(root, file)

                # Check for filename match
                if search_filename and search_filename in file:
                    matching_files.append(file_path)

                # Check for content match
                elif search_content:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            if search_content in f.read():
                                matching_files.append(file_path)
                    except Exception as e:
                        # Log the error if needed, but continue processing other files
                        print(f"Error reading file {file_path}: {e}")

        return jsonify({'files': matching_files}), 200

    except Exception as e:
        # Log the exception if needed
        print(f"Error processing request: {e}")
        return jsonify({'error': 'Invalid input'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)