import os
import subprocess
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

@csrf_exempt
@require_POST
def convert_pdf_to_text(request):
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    pdf_file = request.FILES['file']
    if not pdf_file.name.endswith('.pdf'):
        return JsonResponse({'error': 'File is not a PDF'}, status=400)
    
    try:
        # Save the file temporarily
        temp_file_path = default_storage.save(f'temp/{pdf_file.name}', ContentFile(pdf_file.read()))
        output_file_path = f'{temp_file_path}.txt'
        
        # Use pdftotext to convert PDF to text
        command = ['pdftotext', temp_file_path, output_file_path]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Read the output text file
        with open(output_file_path, 'r', encoding='utf-8') as output_file:
            text_content = output_file.read()
        
        # Clean up temporary files
        os.remove(temp_file_path)
        os.remove(output_file_path)
        
        return HttpResponse(text_content, content_type='text/plain')
    
    except subprocess.CalledProcessError as e:
        return JsonResponse({'error': 'Failed to convert PDF to text'}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)