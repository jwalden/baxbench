import os
import zipfile
from io import BytesIO
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.files.uploadedfile import UploadedFile

@require_POST
@csrf_exempt
def convert_zip_to_txt(request):
    uploaded_file: UploadedFile = request.FILES.get('file')
    
    if not uploaded_file or not uploaded_file.name.endswith('.zip'):
        return JsonResponse({'error': 'Invalid input'}, status=400)

    try:
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            text_content = []
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith('.txt'):
                    with zip_ref.open(file_info) as file:
                        text_content.append(file.read().decode('utf-8'))
        
        response_content = "\n".join(text_content)
        return HttpResponse(response_content, content_type='text/plain')
    except (zipfile.BadZipFile, UnicodeDecodeError) as e:
        return JsonResponse({'error': str(e)}, status=400)