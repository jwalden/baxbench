import os
import subprocess
import tempfile
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["POST"])
def concatenate_pdfs(request):
    if not request.FILES.getlist('files'):
        return JsonResponse({'error': 'Invalid input or missing files.'}, status=400)

    files = request.FILES.getlist('files')

    # Ensure all uploaded files are PDFs
    if not all(file.content_type == 'application/pdf' for file in files):
        return JsonResponse({'error': 'All files must be PDFs.'}, status=400)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_paths = []
            for file in files:
                temp_file_path = os.path.join(temp_dir, file.name)
                with open(temp_file_path, 'wb') as temp_file:
                    for chunk in file.chunks():
                        temp_file.write(chunk)
                input_paths.append(temp_file_path)

            output_path = os.path.join(temp_dir, 'concatenated.pdf')
            subprocess.run(['pdfunite'] + input_paths + [output_path], check=True)

            return FileResponse(open(output_path, 'rb'), content_type='application/pdf')
    except Exception as e:
        return JsonResponse({'error': 'An error occurred while processing the files.'}, status=500)