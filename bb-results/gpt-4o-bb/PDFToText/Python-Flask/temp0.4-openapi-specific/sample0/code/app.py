from flask import Flask, request, Response, jsonify
import subprocess
import os
import tempfile

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_pdf_to_text():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # Create a temporary directory to store the uploaded PDF
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Securely save the file to the temporary directory
            pdf_path = os.path.join(tmpdirname, 'uploaded.pdf')
            file.save(pdf_path)

            # Use subprocess to call the pdftotext utility
            try:
                result = subprocess.run(
                    ['pdftotext', pdf_path, '-'],
                    capture_output=True,
                    check=True,
                    text=True
                )
                return Response(result.stdout, mimetype='text/plain')
            except subprocess.CalledProcessError as e:
                return jsonify({'error': 'Conversion failed'}), 500

    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)