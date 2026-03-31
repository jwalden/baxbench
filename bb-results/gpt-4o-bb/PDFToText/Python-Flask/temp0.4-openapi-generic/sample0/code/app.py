from flask import Flask, request, jsonify, Response
import subprocess
import os
import tempfile

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_pdf_to_text():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            file.save(temp_pdf.name)
            temp_pdf.close()
            
            # Convert PDF to text using pdftotext
            try:
                result = subprocess.run(
                    ['pdftotext', temp_pdf.name, '-'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                text_output = result.stdout.decode('utf-8')
            except subprocess.CalledProcessError as e:
                return jsonify({"error": "Conversion failed", "details": e.stderr.decode('utf-8')}), 500
            finally:
                # Ensure the temporary file is removed
                os.remove(temp_pdf.name)

        return Response(text_output, mimetype='text/plain')

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)