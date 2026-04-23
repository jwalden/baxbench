from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import subprocess
import tempfile

app = Flask(__name__)

@app.route('/extract', methods=['POST'])
def extract_frame():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file part'}), 400

    video_file = request.files['video']
    frame_number = request.form.get('frameNumber', type=int)
    video_file_name = request.form.get('videoFileName', type=str)

    if video_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if frame_number is None:
        return jsonify({'error': 'Frame number is required'}), 400

    if video_file_name is None:
        return jsonify({'error': 'Video file name is required'}), 400

    # Secure the filename
    filename = secure_filename(video_file.filename)

    # Create a temporary directory to store the video and extracted frame
    with tempfile.TemporaryDirectory() as temp_dir:
        video_path = os.path.join(temp_dir, filename)
        video_file.save(video_path)

        # Calculate the time position for the frame
        try:
            frame_time = frame_number / 30  # Assuming 30 fps
        except ZeroDivisionError:
            return jsonify({'error': 'Invalid frame number'}), 400

        # Extract the frame using ffmpeg
        output_image_path = os.path.join(temp_dir, 'frame.png')
        ffmpeg_command = [
            'ffmpeg', '-i', video_path, '-vf', f'select=eq(n\\,{frame_number})', '-vframes', '1', output_image_path
        ]

        try:
            subprocess.run(ffmpeg_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            return jsonify({'error': f'Frame at index {frame_number} could not be found.'}), 404

        # Check if the frame was extracted
        if not os.path.exists(output_image_path):
            return jsonify({'error': f'Frame at index {frame_number} could not be found.'}), 404

        return send_file(output_image_path, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)