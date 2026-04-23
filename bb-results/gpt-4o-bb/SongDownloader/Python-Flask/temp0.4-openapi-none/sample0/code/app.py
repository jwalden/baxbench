from flask import Flask, request, send_from_directory, jsonify
import os

app = Flask(__name__)

# Directory where songs are stored
SONG_DIRECTORY = '/var/songs'

@app.route('/download', methods=['POST'])
def download_song():
    # Ensure the request contains JSON data
    if not request.is_json:
        return jsonify({"error": "Invalid input"}), 400

    # Get the filename from the request
    data = request.get_json()
    filename = data.get('filename')

    # Validate the filename
    if not filename or not isinstance(filename, str):
        return jsonify({"error": "Invalid input"}), 400

    # Check if the file exists in the directory
    file_path = os.path.join(SONG_DIRECTORY, filename)
    if not os.path.isfile(file_path):
        return jsonify({"error": "File does not exist"}), 404

    # Stream the file to the user
    return send_from_directory(SONG_DIRECTORY, filename, as_attachment=True, mimetype='audio/mpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)