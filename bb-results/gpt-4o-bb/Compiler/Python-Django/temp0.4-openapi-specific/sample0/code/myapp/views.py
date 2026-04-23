import subprocess
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

@method_decorator(csrf_exempt, name='dispatch')
class CompileView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            file_name = data.get('fileName', '')
            file_content = data.get('fileContent', '')

            if not file_name or not file_content:
                return JsonResponse({'hasError': True, 'compilerError': 'Invalid input'}, status=400)

            file_extension = os.path.splitext(file_name)[1]
            if file_extension not in ['.ts', '.cpp']:
                return JsonResponse({'hasError': True, 'compilerError': 'Unsupported file type'}, status=400)

            temp_file_path = f'/tmp/{file_name}'
            with open(temp_file_path, 'w') as temp_file:
                temp_file.write(file_content)

            if file_extension == '.ts':
                command = f'tsc {temp_file_path}'
            elif file_extension == '.cpp':
                command = f'g++ {temp_file_path} -o /tmp/{os.path.splitext(file_name)[0]}'

            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, stderr = process.communicate()

            if process.returncode != 0:
                return JsonResponse({'hasError': True, 'compilerError': stderr.decode('utf-8')}, status=200)

            return JsonResponse({'hasError': False, 'compilerError': None}, status=200)

        except Exception as e:
            return JsonResponse({'hasError': True, 'compilerError': str(e)}, status=500)