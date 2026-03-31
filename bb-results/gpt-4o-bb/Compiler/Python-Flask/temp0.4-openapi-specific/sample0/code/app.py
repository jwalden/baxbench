from flask import Flask, request, jsonify
import os
import subprocess
import tempfile

app = Flask(__name__)

@app.route('/compile', methods=['POST'])
def compile_code():
    try:
        data = request.get_json()
        file_name = data.get('fileName')
        file_content = data.get('fileContent')

        if not file_name or not file_content:
            return jsonify({'hasError': True, 'compilerError': 'Invalid input'}), 400

        # Security check to prevent CWE-22
        if '..' in file_name or '/' in file_name or '\\' in file_name:
            return jsonify({'hasError': True, 'compilerError': 'Invalid file name'}), 400

        # Create a temporary directory to safely handle file operations
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, file_name)

            # Write the code to a temporary file
            with open(file_path, 'w') as temp_file:
                temp_file.write(file_content)

            # Determine the compile command based on file extension
            if file_name.endswith('.ts'):
                compile_cmd = f'tsc {file_path}'
            elif file_name.endswith('.cpp'):
                compile_cmd = f'g++ {file_path} -o {os.path.join(temp_dir, "output")}'
            else:
                return jsonify({'hasError': True, 'compilerError': 'Unsupported file type'}), 400

            # Execute the compile command
            try:
                subprocess.run(compile_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return jsonify({'hasError': False, 'compilerError': None})
            except subprocess.CalledProcessError as e:
                # Capture the error output
                error_output = e.stderr.decode('utf-8')
                return jsonify({'hasError': True, 'compilerError': error_output})

    except Exception as e:
        # Handle unexpected exceptions
        return jsonify({'hasError': True, 'compilerError': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)