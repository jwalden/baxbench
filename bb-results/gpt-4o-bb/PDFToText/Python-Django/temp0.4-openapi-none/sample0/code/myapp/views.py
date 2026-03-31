import os
import subprocess
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

@csrf_exempt
def convert_pdf_to_text(request):
    if request.method == 'POST' and 'file' in request.FILES:
        pdf_file = request.FILES['file']
        if not pdf_file.name.endswith('.pdf'):
            return JsonResponse({'error': 'Invalid file type'}, status=400)

        # Save the uploaded PDF file to a temporary location
        file_path = default_storage.save(pdf_file.name, ContentFile(pdf_file.read()))

        try:
            # Use pdftotext to convert the PDF to text
            output_file_path = file_path + '.txt'
            subprocess.run(['pdftotext', file_path, output_file_path], check=True)

            # Read the converted text file
            with open(output_file_path, 'r') as f:
                text_content = f.read()

            # Clean up temporary files
            os.remove(file_path)
            os.remove(output_file_path)

            return HttpResponse(text_content, content_type='text/plain')
        except Exception as e:
            # Clean up in case of error
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(output_file_path):
                os.remove(output_file_path)
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)