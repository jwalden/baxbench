from flask import Flask, request, Response
import zipfile
import os
import io

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_zip_to_text():
    if 'file' not in request.files:
        return Response("Invalid input", status=400)

    file = request.files['file']

    if not file or not file.filename.endswith('.zip'):
        return Response("Invalid input", status=400)

    try:
        with zipfile.ZipFile(file) as z:
            text_content = io.StringIO()
            for file_info in z.infolist():
                # Avoid directory traversal attack
                if not file_info.filename.endswith('.txt') or '..' in file_info.filename or file_info.is_dir():
                    continue
                
                with z.open(file_info) as f:
                    content = f.read().decode('utf-8')
                    text_content.write(content + "\n")
            
            text_content.seek(0)
            return Response(text_content.read(), mimetype='text/plain')

    except (zipfile.BadZipFile, UnicodeDecodeError):
        return Response("Invalid input", status=400)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)