from flask import Flask, request, send_file, jsonify
import os
import subprocess
import tempfile

app = Flask(__name__)

@app.route('/extract', methods=['POST'])
def extract_frame():
    try:
        # Ensure the request has the necessary parts
        if 'video' not in request.files or 'frameNumber' not in request.form:
            return jsonify({"error": "Missing video file or frame number"}), 400
        
        video_file = request.files['video']
        frame_number = request.form['frameNumber']

        # Validate frame_number is an integer
        try:
            frame_number = int(frame_number)
        except ValueError:
            return jsonify({"error": "Invalid frame number"}), 400
        
        # Use a temporary directory to store the video and extracted frame
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, "uploaded_video.mp4")
            video_file.save(video_path)

            # Prepare the output frame path
            output_frame_path = os.path.join(temp_dir, "extracted_frame.png")

            # Use ffmpeg to extract the frame
            ffmpeg_command = [
                'ffmpeg', 
                '-i', video_path,
                '-vf', f'select=eq(n\,{frame_number})',
                '-vframes', '1',
                output_frame_path
            ]

            # Execute the ffmpeg command
            result = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Check if the frame was successfully extracted
            if result.returncode != 0 or not os.path.exists(output_frame_path):
                return jsonify({"error": f"Frame at index {frame_number} could not be found."}), 404

            # Send the extracted frame as a response
            return send_file(output_frame_path, mimetype='image/png')
    
    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)