import subprocess
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def compile_code(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            file_name = data.get('fileName')
            file_content = data.get('fileContent')
            
            if not file_name or not file_content:
                return JsonResponse({'hasError': True, 'compilerError': 'Invalid input.'})
            
            # Write the content to a temporary file
            with open(file_name, 'w') as f:
                f.write(file_content)
            
            if file_name.endswith('.ts'):
                # Compile TypeScript file
                result = subprocess.run(['tsc', file_name], capture_output=True, text=True)
            elif file_name.endswith('.cpp'):
                # Compile C++ file
                result = subprocess.run(['g++', file_name, '-o', 'output'], capture_output=True, text=True)
            else:
                return JsonResponse({'hasError': True, 'compilerError': 'Unsupported file type.'})

            if result.returncode != 0:
                return JsonResponse({'hasError': True, 'compilerError': result.stderr})
            else:
                return JsonResponse({'hasError': False, 'compilerError': None})
        except Exception as e:
            return JsonResponse({'hasError': True, 'compilerError': str(e)})
    else:
        return JsonResponse({'hasError': True, 'compilerError': 'Invalid request method.'})