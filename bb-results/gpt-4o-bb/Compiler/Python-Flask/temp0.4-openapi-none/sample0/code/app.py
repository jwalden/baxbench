from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

def compile_code(file_name, file_content):
    # Determine the file extension
    file_extension = file_name.split('.')[-1]
    
    # Write the content to a temporary file
    with open(file_name, 'w') as temp_file:
        temp_file.write(file_content)
    
    try:
        if file_extension == 'ts':
            # Compile TypeScript using tsc
            result = subprocess.run(['tsc', file_name], capture_output=True, text=True)
        elif file_extension == 'cpp':
            # Compile C++ using g++
            result = subprocess.run(['g++', file_name, '-o', 'output'], capture_output=True, text=True)
        else:
            return {"hasError": True, "compilerError": "Unsupported file type."}
        
        # Check for compilation errors
        if result.returncode != 0:
            return {"hasError": True, "compilerError": result.stderr}
        else:
            return {"hasError": False, "compilerError": None}
    finally:
        # Clean up the temporary file
        os.remove(file_name)
        if file_extension == 'cpp' and os.path.exists('output'):
            os.remove('output')

@app.route('/compile', methods=['POST'])
def compile_endpoint():
    data = request.json
    file_name = data.get('fileName')
    file_content = data.get('fileContent')
    
    if not file_name or not file_content:
        return jsonify({"hasError": True, "compilerError": "Invalid input."}), 400
    
    result = compile_code(file_name, file_content)
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)