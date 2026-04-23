import subprocess
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def compile_code(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            file_name = data.get('fileName', '')
            file_content = data.get('fileContent', '')

            if not file_name or not file_content:
                return JsonResponse({'hasError': True, 'compilerError': 'Invalid input'}, status=400)

            # Determine the language
            if file_name.endswith('.ts'):
                # Write the TypeScript code to a file
                with open(file_name, 'w') as f:
                    f.write(file_content)

                # Compile TypeScript
                result = subprocess.run(['tsc', file_name], capture_output=True, text=True)
                has_error = result.returncode != 0
                compiler_error = result.stderr if has_error else None

            elif file_name.endswith('.cpp'):
                # Write the C++ code to a file
                with open(file_name, 'w') as f:
                    f.write(file_content)

                # Compile C++
                result = subprocess.run(['g++', file_name, '-o', 'output'], capture_output=True, text=True)
                has_error = result.returncode != 0
                compiler_error = result.stderr if has_error else None

            else:
                return JsonResponse({'hasError': True, 'compilerError': 'Unsupported file type'}, status=400)

            return JsonResponse({'hasError': has_error, 'compilerError': compiler_error})

        except json.JSONDecodeError:
            return JsonResponse({'hasError': True, 'compilerError': 'Invalid JSON'}, status=400)

    return JsonResponse({'hasError': True, 'compilerError': 'Invalid request method'}, status=405)