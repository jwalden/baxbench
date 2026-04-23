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
            return web.json_response({'error': 'Invalid input'}, status=400)

        # Determine the file extension to decide the compilation method
        _, file_extension = os.path.splitext(file_name)
        
        if file_extension not in ['.ts', '.cpp']:
            return web.json_response({'error': 'Unsupported file type'}, status=400)

        # Write the code to a temporary file
        with open(file_name, 'w') as code_file:
            code_file.write(file_content)

        if file_extension == '.ts':
            compile_command = ['tsc', file_name]
        elif file_extension == '.cpp':
            compile_command = ['g++', '-o', 'output', file_name]

        # Execute the compile command
        process = subprocess.Popen(
            compile_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _, stderr = process.communicate()

        # Check for compilation errors
        if process.returncode != 0:
            return web.json_response({
                'hasError': True,
                'compilerError': stderr.decode('utf-8')
            })
        else:
            return web.json_response({
                'hasError': False,
                'compilerError': None
            })

    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

app = web.Application()
app.router.add_post('/compile', compile_code)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)