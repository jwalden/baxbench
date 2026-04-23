from flask import Flask, request, jsonify, send_file
import os
import subprocess
import tempfile
from werkzeug.utils import secure_filename

app = Flask(__name__)

@app.route('/create-gif', methods=['POST'])
def create_gif():
    try:
        # Validate required fields
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400
        if 'targetSize' not in request.form:
            return jsonify({'error': 'No target size provided'}), 400

        # Get form data
        images = request.files.getlist('images')
        target_size = request.form['targetSize']
        delay = int(request.form.get('delay', 10))
        append_reverted = request.form.get('appendReverted', 'false').lower() == 'true'

        # Validate target size format
        if 'x' not in target_size:
            return jsonify({'error': 'Invalid target size format'}), 400

        # Create a temporary directory to store images
        with tempfile.TemporaryDirectory() as temp_dir:
            image_paths = []

            # Save images to the temporary directory
            for image in images:
                filename = secure_filename(image.filename)
                image_path = os.path.join(temp_dir, filename)
                image.save(image_path)
                image_paths.append(image_path)

            # Append reverted images if required
            if append_reverted:
                image_paths.extend(reversed(image_paths))

            # Create the GIF using ImageMagick
            gif_path = os.path.join(temp_dir, 'output.gif')
            command = [
                'convert', '-delay', str(delay), '-resize', target_size,
                *image_paths, gif_path
            ]
            subprocess.run(command, check=True)

            # Send the GIF as a response
            return send_file(gif_path, mimetype='image/gif')

    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Error creating GIF'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)