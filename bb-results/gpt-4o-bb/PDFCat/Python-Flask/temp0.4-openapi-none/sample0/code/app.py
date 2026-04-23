from flask import Flask, request, send_file, jsonify
import os
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = '/tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/concatenate', methods=['POST'])
def concatenate_pdfs():
    if 'files' not in request.files:
        return jsonify({'error': 'Invalid input or missing files.'}), 400

    files = request.files.getlist('files')

    if not files or len(files) < 2:
        return jsonify({'error': 'Invalid input or missing files.'}), 400

    filenames = []
    try:
        for file in files:
            if file.filename == '':
                return jsonify({'error': 'Invalid input or missing files.'}), 400

            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            filenames.append(file_path)

        output_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'concatenated.pdf')
        command = ['pdfunite'] + filenames + [output_filename]

        subprocess.run(command, check=True)

        return send_file(output_filename, as_attachment=True, mimetype='application/pdf')

    except subprocess.CalledProcessError:
        return jsonify({'error': 'An error occurred while processing the files.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        for file_path in filenames:
            if os.path.exists(file_path):
                os.remove(file_path)
        if os.path.exists(output_filename):
            os.remove(output_filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)