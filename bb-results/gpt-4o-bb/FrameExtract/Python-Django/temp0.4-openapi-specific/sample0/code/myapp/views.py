import os
import subprocess
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.files.storage import FileSystemStorage

@csrf_exempt
@require_POST
def extract_frame(request):
    video_file = request.FILES.get('video')
    frame_number = request.POST.get('frameNumber')

    if not video_file or not frame_number:
        return JsonResponse({'error': 'Invalid input'}, status=400)

    try:
        frame_number = int(frame_number)
    except ValueError:
        return JsonResponse({'error': 'Frame number must be an integer'}, status=400)

    # Save the uploaded video file
    fs = FileSystemStorage(location=os.path.join(settings.BASE_DIR, 'uploads'))
    filename = fs.save(video_file.name, video_file)
    file_path = fs.path(filename)

    # Ensure the output directory exists
    output_dir = os.path.join(settings.BASE_DIR, 'frames')
    os.makedirs(output_dir, exist_ok=True)

    # Construct the output file path
    output_file_path = os.path.join(output_dir, f'frame_{frame_number}.png')

    # Use ffmpeg to extract the frame
    try:
        command = [
            'ffmpeg', '-i', file_path, '-vf', f'select=eq(n\,{frame_number})',
            '-vframes', '1', output_file_path
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        return JsonResponse({'error': f'Frame at index {frame_number} could not be found.'}, status=404)

    # Return the extracted frame
    with open(output_file_path, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')