import os
import tempfile
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

    # Create a temporary directory to store the uploaded files
    with tempfile.TemporaryDirectory() as temp_dir:
        file_paths = []
        for file in files:
            # Use a secure way to save files
            fs = FileSystemStorage(location=temp_dir)
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)
            file_paths.append(file_path)

        # Define the output file path
        output_file_path = os.path.join(temp_dir, 'concatenated.pdf')

        try:
            # Construct the pdfunite command
            command = ['pdfunite'] + file_paths + [output_file_path]
            # Execute the command
            subprocess.run(command, check=True)

            # Read the output file and send it as a response
            with open(output_file_path, 'rb') as output_file:
                response = HttpResponse(output_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="concatenated.pdf"'
                return response
        except subprocess.CalledProcessError:
            return JsonResponse({'error': 'An error occurred while processing the files.'}, status=500)