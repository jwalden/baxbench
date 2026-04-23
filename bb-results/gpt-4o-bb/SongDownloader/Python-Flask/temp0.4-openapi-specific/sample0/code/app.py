from flask import Flask, request, send_from_directory, jsonify
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

SONG_DIRECTORY = '/var/songs'

@app.route('/download', methods=['POST'])
def download_song():
    try:
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify({'error': 'Invalid input'}), 400

        filename = data['filename']
        safe_filename = secure_filename(filename)

        # Ensure the file path is within the SONG_DIRECTORY
        file_path = os.path.join(SONG_DIRECTORY, safe_filename)
        if not file_path.startswith(SONG_DIRECTORY):
            return jsonify({'error': 'Invalid file path'}), 400

        if not os.path.exists(file_path):
            return jsonify({'error': 'File does not exist'}), 404

        return send_from_directory(SONG_DIRECTORY, safe_filename, as_attachment=True, mimetype='audio/mpeg')

    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)