from flask import Flask, request, send_from_directory, jsonify
import os

app = Flask(__name__)

# Directory where songs are stored
SONG_DIRECTORY = '/var/songs'

@app.route('/download', methods=['POST'])
def download_song():
    if not request.is_json:
        return jsonify({'error': 'Invalid input'}), 400

    data = request.get_json()
    filename = data.get('filename')

    if not filename or not isinstance(filename, str):
        return jsonify({'error': 'Invalid input'}), 400

    # Ensure the filename is safe and does not contain path traversal characters
    if '..' in filename or filename.startswith('/'):
        return jsonify({'error': 'Invalid input'}), 400

    file_path = os.path.join(SONG_DIRECTORY, filename)

    if not os.path.isfile(file_path):
        return jsonify({'error': 'File does not exist'}), 404

    try:
        return send_from_directory(SONG_DIRECTORY, filename, as_attachment=True, mimetype='audio/mpeg')
    except Exception as e:
        return jsonify({'error': 'An error occurred while streaming the file'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)