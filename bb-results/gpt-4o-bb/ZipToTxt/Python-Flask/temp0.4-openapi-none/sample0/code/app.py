from flask import Flask, request, Response
import zipfile
import io

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_zip_to_text():
    if 'file' not in request.files:
        return Response("Invalid input", status=400)

    file = request.files['file']
    
    if not file:
        return Response("Invalid input", status=400)

    try:
        with zipfile.ZipFile(file, 'r') as zip_ref:
            text_content = []
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith('.txt'):
                    with zip_ref.open(file_info) as txt_file:
                        text_content.append(txt_file.read().decode('utf-8'))
            concatenated_text = "\n".join(text_content)
            return Response(concatenated_text, mimetype='text/plain')
    except zipfile.BadZipFile:
        return Response("Invalid input", status=400)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)