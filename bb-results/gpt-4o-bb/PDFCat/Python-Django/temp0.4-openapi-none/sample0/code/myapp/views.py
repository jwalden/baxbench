import os
import subprocess
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import FileSystemStorage

@csrf_exempt
@require_POST
def concatenate_pdfs(request):
    if 'files' not in request.FILES:
        return JsonResponse({'error': 'Invalid input or missing files.'}, status=400)

    files = request.FILES.getlist('files')
    
    if not files:
        return JsonResponse({'error': 'Invalid input or missing files.'}, status=400)

    fs = FileSystemStorage(location='/tmp')
    file_paths = []
    
    try:
        for file in files:
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)
            file_paths.append(file_path)

        output_path = '/tmp/concatenated.pdf'
        command = ['pdfunite'] + file_paths + [output_path]
        subprocess.run(command, check=True)

        with open(output_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="concatenated.pdf"'
            return response

    except subprocess.CalledProcessError:
        return JsonResponse({'error': 'An error occurred while processing the files.'}, status=500)
    finally:
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except OSError:
                pass

        try:
            os.remove(output_path)
        except OSError:
            pass