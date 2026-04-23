import json
import os
import subprocess
from aiohttp import web

async def compile_code(request):
    try:
        data = await request.json()
        file_name = data.get('fileName')
        file_content = data.get('fileContent')

        if not file_name or not file_content:
            return web.json_response({'hasError': True, 'compilerError': 'Invalid input'}, status=400)

        # Determine the language based on file extension
        if file_name.endswith('.ts'):
            compile_command = ['tsc', '--noEmit', file_name]
        elif file_name.endswith('.cpp'):
            compile_command = ['g++', '-o', '/dev/null', file_name]
        else:
            return web.json_response({'hasError': True, 'compilerError': 'Unsupported file type'}, status=400)

        # Write the file content to a temporary file
        with open(file_name, 'w') as code_file:
            code_file.write(file_content)

        # Run the compiler
        process = subprocess.run(compile_command, capture_output=True, text=True)

        # Clean up the temporary file
        os.remove(file_name)

        # Check for compilation errors
        if process.returncode != 0:
            return web.json_response({'hasError': True, 'compilerError': process.stderr.strip()})
        else:
            return web.json_response({'hasError': False, 'compilerError': None})

    except Exception as e:
        return web.json_response({'hasError': True, 'compilerError': str(e)}, status=500)

app = web.Application()
app.router.add_post('/compile', compile_code)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)