from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

def compile_code(file_name, file_content):
    # Determine the compiler and command based on file extension
    if file_name.endswith('.ts'):
        compiler = 'tsc'
        command = [compiler, '--noEmit', file_name]
    elif file_name.endswith('.cpp'):
        compiler = 'g++'
        command = [compiler, '-fsyntax-only', file_name]
    else:
        return {'hasError': True, 'compilerError': 'Unsupported file type'}

    # Write the file content to a temporary file
    with open(file_name, 'w') as f:
        f.write(file_content)

    try:
        # Run the compiler command
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return {'hasError': False, 'compilerError': None}
    except subprocess.CalledProcessError as e:
        return {'hasError': True, 'compilerError': e.stderr}
    finally:
        # Clean up the temporary file
        if os.path.exists(file_name):
            os.remove(file_name)

@app.route('/compile', methods=['POST'])
def compile_endpoint():
    data = request.get_json()
    file_name = data.get('fileName')
    file_content = data.get('fileContent')

    if not file_name or not file_content:
        return jsonify({'hasError': True, 'compilerError': 'Invalid input'}), 400

    result = compile_code(file_name, file_content)
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)