from flask import Flask, request, Response
import zipfile
import io

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_zip_to_txt():
    if 'file' not in request.files:
        return Response("Invalid input", status=400)

    file = request.files['file']

    if not file or not file.filename.endswith('.zip'):
        return Response("Invalid input", status=400)

    try:
        # Read the zip file from the uploaded file
        zip_file = zipfile.ZipFile(file)
        text_content = []

        # Iterate through each file in the zip
        for file_info in zip_file.infolist():
            if file_info.filename.endswith('.txt'):
                with zip_file.open(file_info) as txt_file:
                    text_content.append(txt_file.read().decode('utf-8'))

        # Concatenate all text file contents
        result_text = "\n".join(text_content)
        return Response(result_text, mimetype='text/plain')

    except zipfile.BadZipFile:
        return Response("Invalid input", status=400)
    except Exception as e:
        return Response(f"An error occurred: {str(e)}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)