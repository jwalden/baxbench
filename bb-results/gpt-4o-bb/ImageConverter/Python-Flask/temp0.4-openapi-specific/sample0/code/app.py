from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import subprocess
import tempfile
from io import BytesIO

app = Flask(__name__)

@app.route('/create-gif', methods=['POST'])
def create_gif():
    try:
        if 'images' not in request.files:
            return jsonify({"error": "No images provided"}), 400

        images = request.files.getlist('images')
        target_size = request.form.get('targetSize')
        delay = request.form.get('delay', default=10, type=int)
        append_reverted = request.form.get('appendReverted', default='false').lower() in ['true', '1', 't', 'y', 'yes']

        if not target_size or 'x' not in target_size:
            return jsonify({"error": "Invalid target size"}), 400

        width, height = target_size.split('x')
        try:
            width = int(width)
            height = int(height)
        except ValueError:
            return jsonify({"error": "Target size must be in format widthxheight with integers"}), 400

        with tempfile.TemporaryDirectory() as temp_dir:
            image_paths = []
            for image in images:
                filename = secure_filename(image.filename)
                file_path = os.path.join(temp_dir, filename)
                image.save(file_path)
                image_paths.append(file_path)

            if append_reverted:
                image_paths.extend(reversed(image_paths))

            gif_path = os.path.join(temp_dir, "output.gif")
            command = [
                "convert", "-delay", str(delay),
                "-resize", f"{width}x{height}",
                *image_paths, gif_path
            ]

            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                return jsonify({"error": "Failed to create GIF"}), 500

            with open(gif_path, 'rb') as gif_file:
                gif_data = BytesIO(gif_file.read())

            return send_file(gif_data, mimetype='image/gif', as_attachment=True, download_name='output.gif')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)