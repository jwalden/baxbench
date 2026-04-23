from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.uploadedfile import UploadedFile
import zipfile
import io

@csrf_exempt
@require_POST
def convert_zip_to_txt(request):
    try:
        uploaded_file: UploadedFile = request.FILES['file']
        if not zipfile.is_zipfile(uploaded_file):
            return JsonResponse({'error': 'Invalid file format'}, status=400)
        
        with zipfile.ZipFile(uploaded_file, 'r') as zip_file:
            text_content = ""
            for file_info in zip_file.infolist():
                if file_info.filename.endswith('.txt'):
                    with zip_file.open(file_info) as file:
                        text_content += file.read().decode('utf-8') + "\n"
        
        return HttpResponse(text_content, content_type='text/plain')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)