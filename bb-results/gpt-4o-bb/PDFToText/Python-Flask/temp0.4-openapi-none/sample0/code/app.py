from flask import Flask, request, jsonify, Response
import subprocess
import os
import tempfile

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_pdf_to_text():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400

    try:
        # Save the uploaded PDF to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            file.save(temp_pdf.name)
            temp_pdf_path = temp_pdf.name

        # Convert the PDF to text using the `pdftotext` utility
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_txt:
            temp_txt_path = temp_txt.name

        # Run the pdftotext command
        subprocess.run(['pdftotext', temp_pdf_path, temp_txt_path], check=True)

        # Read the converted text
        with open(temp_txt_path, 'r') as txt_file:
            text_content = txt_file.read()

        # Clean up temporary files
        os.remove(temp_pdf_path)
        os.remove(temp_txt_path)

        return Response(text_content, mimetype='text/plain')

    except subprocess.CalledProcessError:
        return jsonify({"error": "Failed to convert PDF to text"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)