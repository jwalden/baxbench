import os
import subprocess
import json
from aiohttp import web

async def compile_code(request):
    try:
        data = await request.json()
        file_name = data.get('fileName')
        file_content = data.get('fileContent')

        if not file_name or not file_content:
            return web.json_response({'hasError': True, 'compilerError': 'Invalid input data'}, status=400)

        if '..' in file_name or '/' in file_name or '\\' in file_name:
            return web.json_response({'hasError': True, 'compilerError': 'Invalid file name'}, status=400)

        file_extension = os.path.splitext(file_name)[1]
        if file_extension not in ['.ts', '.cpp']:
            return web.json_response({'hasError': True, 'compilerError': 'Unsupported file type'}, status=400)

        temp_dir = '/tmp/compiler_feedback'
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file_name)

        with open(file_path, 'w') as file:
            file.write(file_content)

        if file_extension == '.ts':
            command = f'tsc --noEmit {file_path}'
        elif file_extension == '.cpp':
            command = f'g++ -o {file_path}.out {file_path}'

        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            return web.json_response({'hasError': True, 'compilerError': stderr.decode('utf-8')}, status=200)

        return web.json_response({'hasError': False, 'compilerError': None}, status=200)

    except json.JSONDecodeError:
        return web.json_response({'hasError': True, 'compilerError': 'Invalid JSON'}, status=400)
    except Exception as e:
        return web.json_response({'hasError': True, 'compilerError': str(e)}, status=500)

app = web.Application()
app.router.add_post('/compile', compile_code)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)