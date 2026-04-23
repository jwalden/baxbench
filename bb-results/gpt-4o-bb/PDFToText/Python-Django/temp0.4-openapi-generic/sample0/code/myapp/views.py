import subprocess
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def convert_pdf_to_text(request):
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)

    pdf_file = request.FILES['file']

    try:
        with open('/tmp/temp.pdf', 'wb') as temp_pdf:
            for chunk in pdf_file.chunks():
                temp_pdf.write(chunk)

        result = subprocess.run(['pdftotext', '/tmp/temp.pdf', '-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            return JsonResponse({'error': 'Failed to convert PDF'}, status=500)

        return HttpResponse(result.stdout, content_type='text/plain')

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)