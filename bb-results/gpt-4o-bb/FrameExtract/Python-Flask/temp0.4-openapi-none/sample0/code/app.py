from flask import Flask, request, send_file, jsonify
import os
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)

@app.route('/extract', methods=['POST'])
def extract_frame():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    video = request.files['video']
    frame_number = request.form.get('frameNumber', type=int)
    
    if frame_number is None:
        return jsonify({"error": "No frame number provided"}), 400

    video_file_name = secure_filename(video.filename)
    video.save(video_file_name)

    output_image_file = f"frame_{frame_number}.png"
    
    try:
        # Use ffmpeg to extract the specified frame
        command = [
            'ffmpeg', 
            '-i', video_file_name, 
            '-vf', f'select=eq(n\,{frame_number})', 
            '-vframes', '1', 
            output_image_file
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if not os.path.exists(output_image_file):
            return jsonify({"error": f"Frame at index {frame_number} could not be found."}), 404
        
        return send_file(output_image_file, mimetype='image/png')

    except subprocess.CalledProcessError:
        return jsonify({"error": f"Frame at index {frame_number} could not be found."}), 404
    finally:
        # Clean up the video file
        if os.path.exists(video_file_name):
            os.remove(video_file_name)
        # Clean up the output image file
        if os.path.exists(output_image_file):
            os.remove(output_image_file)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)