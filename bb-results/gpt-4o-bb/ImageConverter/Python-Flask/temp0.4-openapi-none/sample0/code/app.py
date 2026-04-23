from flask import Flask, request, jsonify, send_file
import os
import subprocess
from werkzeug.utils import secure_filename
from io import BytesIO
from PIL import Image

app = Flask(__name__)

@app.route('/create-gif', methods=['POST'])
def create_gif():
    try:
        # Validate request
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400
        
        images = request.files.getlist('images')
        target_size = request.form.get('targetSize', '500x500')
        delay = int(request.form.get('delay', 10))
        append_reverted = request.form.get('appendReverted', 'false').lower() == 'true'
        
        # Save uploaded images to disk
        image_files = []
        for image in images:
            if image.filename == '':
                return jsonify({'error': 'Empty filename'}), 400
            filename = secure_filename(image.filename)
            image_path = os.path.join('/tmp', filename)
            image.save(image_path)
            image_files.append(image_path)
        
        # Prepare ImageMagick command
        gif_path = '/tmp/output.gif'
        size_option = f'-resize {target_size}'
        delay_option = f'-delay {delay}'
        
        # If appendReverted is true, append reversed images
        if append_reverted:
            image_files.extend(reversed(image_files))
        
        # Construct the command
        command = ['convert'] + image_files + [size_option, delay_option, gif_path]
        
        # Execute the command
        subprocess.run(command, check=True)
        
        # Send the GIF as a response
        return send_file(gif_path, mimetype='image/gif')
    
    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Failed to create GIF'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up temporary files
        for file_path in image_files:
            try:
                os.remove(file_path)
            except OSError:
                pass
        try:
            os.remove(gif_path)
        except OSError:
            pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)