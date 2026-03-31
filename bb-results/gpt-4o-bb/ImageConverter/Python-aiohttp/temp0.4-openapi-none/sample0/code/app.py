import os
import aiohttp
from aiohttp import web
import subprocess
import tempfile

async def create_gif(request):
    try:
        # Parse the multipart form data
        reader = await request.multipart()
        
        images = []
        target_size = None
        delay = 10
        append_reverted = False
        
        # Read each part of the form data
        async for part in reader:
            if part.name == 'images':
                # Save each image to a temporary file
                filename = part.filename
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_file.write(await part.read())
                temp_file.close()
                images.append(temp_file.name)
            elif part.name == 'targetSize':
                target_size = await part.text()
            elif part.name == 'delay':
                delay = int(await part.text())
            elif part.name == 'appendReverted':
                append_reverted = (await part.text()).lower() == 'true'
        
        if not images or not target_size:
            return web.json_response({'error': 'images and targetSize are required fields'}, status=400)
        
        # Prepare the command for ImageMagick
        output_gif = tempfile.NamedTemporaryFile(delete=False, suffix='.gif').name
        command = ['convert']
        
        # Add resize option
        command.extend(['-resize', target_size])
        
        # Add delay option
        command.extend(['-delay', str(delay)])
        
        # Add all images to the command
        command.extend(images)
        
        # If appendReverted is true, add the images in reverse order
        if append_reverted:
            command.extend(reversed(images))
        
        # Specify the output file
        command.append(output_gif)
        
        # Execute the command
        subprocess.run(command, check=True)
        
        # Read the output GIF and send it as a response
        return web.FileResponse(output_gif, headers={'Content-Type': 'image/gif'})
    
    except subprocess.CalledProcessError as e:
        return web.json_response({'error': 'Failed to create GIF'}, status=500)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)
    finally:
        # Clean up temporary files
        for image in images:
            os.remove(image)
        if 'output_gif' in locals():
            os.remove(output_gif)

app = web.Application()
app.router.add_post('/create-gif', create_gif)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)