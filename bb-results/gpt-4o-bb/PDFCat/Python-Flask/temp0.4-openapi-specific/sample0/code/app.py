from flask import Flask, request, send_file, jsonify
import os
import tempfile
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)

@app.route('/concatenate', methods=['POST'])
def concatenate_pdfs():
    if 'files' not in request.files:
        return jsonify({'error': 'Invalid input or missing files.'}), 400

    files = request.files.getlist('files')
    if not files or len(files) < 2:
        return jsonify({'error': 'Please upload at least two PDF files.'}), 400

    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_paths = []
        try:
            # Save uploaded files securely
            for file in files:
                filename = secure_filename(file.filename)
                if not filename.lower().endswith('.pdf'):
                    return jsonify({'error': 'All files must be PDFs.'}), 400
                file_path = os.path.join(temp_dir, filename)
                file.save(file_path)
                pdf_paths.append(file_path)

            # Concatenate PDFs using pdfunite
            output_pdf_path = os.path.join(temp_dir, 'concatenated.pdf')
            command = ['pdfunite'] + pdf_paths + [output_pdf_path]
            result = subprocess.run(command, capture_output=True, text=True)

            if result.returncode != 0:
                return jsonify({'error': 'An error occurred while processing the files.'}), 500

            return send_file(output_pdf_path, as_attachment=True, mimetype='application/pdf')

        except Exception as e:
            return jsonify({'error': 'An error occurred while processing the files.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)