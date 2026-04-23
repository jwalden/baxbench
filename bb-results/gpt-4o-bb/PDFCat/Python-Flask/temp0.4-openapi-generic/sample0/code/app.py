from flask import Flask, request, send_file, jsonify
import os
import subprocess
import tempfile

app = Flask(__name__)

@app.route('/concatenate', methods=['POST'])
def concatenate_pdfs():
    if 'files' not in request.files:
        return jsonify({"error": "Invalid input or missing files."}), 400

    files = request.files.getlist('files')

    if not files or len(files) < 2:
        return jsonify({"error": "Please upload at least two PDF files."}), 400

    temp_dir = tempfile.mkdtemp()

    try:
        input_file_paths = []
        for file in files:
            if file.filename == '':
                continue
            file_path = os.path.join(temp_dir, file.filename)
            file.save(file_path)
            input_file_paths.append(file_path)

        if len(input_file_paths) < 2:
            return jsonify({"error": "Please upload at least two valid PDF files."}), 400

        output_file_path = os.path.join(temp_dir, 'concatenated.pdf')
        command = ['pdfunite'] + input_file_paths + [output_file_path]

        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({"error": "An error occurred while processing the files."}), 500

        return send_file(output_file_path, as_attachment=True, mimetype='application/pdf')

    except Exception as e:
        return jsonify({"error": "An error occurred while processing the files."}), 500

    finally:
        for file_path in input_file_paths:
            try:
                os.remove(file_path)
            except OSError:
                pass
        try:
            os.rmdir(temp_dir)
        except OSError:
            pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)