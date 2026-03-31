import zipfile
import io
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def convert_zip_to_txt(request):
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)

    uploaded_file = request.FILES['file']

    if not zipfile.is_zipfile(uploaded_file):
        return JsonResponse({'error': 'Invalid zip file'}, status=400)

    try:
        with zipfile.ZipFile(uploaded_file) as z:
            text_content = []
            for file_info in z.infolist():
                if file_info.filename.endswith('.txt'):
                    with z.open(file_info) as f:
                        text_content.append(f.read().decode('utf-8'))
            combined_text = "\n".join(text_content)
            return HttpResponse(combined_text, content_type='text/plain')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)