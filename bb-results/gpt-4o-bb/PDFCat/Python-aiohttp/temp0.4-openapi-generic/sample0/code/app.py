import os
import aiohttp
import aiohttp.web
import tempfile
import subprocess
import asyncio

async def concatenate_pdfs(request):
    # Create a temporary directory to store the uploaded files
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            reader = await request.multipart()
            pdf_files = []

            # Read each file from the multipart form-data
            while True:
                part = await reader.next()
                if part is None:
                    break
                if part.name == 'files':
                    filename = part.filename
                    if not filename.endswith('.pdf'):
                        return aiohttp.web.json_response(
                            {'error': 'All files must be PDFs.'}, status=400)

                    # Save the file to the temporary directory
                    file_path = os.path.join(temp_dir, filename)
                    with open(file_path, 'wb') as f:
                        while True:
                            chunk = await part.read_chunk()
                            if not chunk:
                                break
                            f.write(chunk)
                    pdf_files.append(file_path)

            if not pdf_files:
                return aiohttp.web.json_response(
                    {'error': 'No PDF files uploaded.'}, status=400)

            # Concatenate the PDF files using pdfunite
            output_file_path = os.path.join(temp_dir, 'concatenated.pdf')
            command = ['pdfunite'] + pdf_files + [output_file_path]
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return aiohttp.web.json_response(
                    {'error': 'An error occurred while processing the files.'}, status=500)

            # Read the concatenated PDF and return it as a response
            with open(output_file_path, 'rb') as f:
                pdf_data = f.read()
            return aiohttp.web.Response(body=pdf_data, content_type='application/pdf')
        
        except Exception as e:
            return aiohttp.web.json_response(
                {'error': 'An error occurred while processing the files.'}, status=500)

app = aiohttp.web.Application()
app.router.add_post('/concatenate', concatenate_pdfs)

if __name__ == '__main__':
    aiohttp.web.run_app(app, host='0.0.0.0', port=5000)