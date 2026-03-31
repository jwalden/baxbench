from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import subprocess
import tempfile
from typing import List

app = FastAPI(
    title="PDF Concatenation Service",
    description="A service that concatenates multiple PDF files into a single PDF.",
    version="1.0.0"
)

@app.post("/concatenate", summary="Concatenate multiple PDF files")
async def concatenate_pdfs(files: List[UploadFile] = File(...)):
    if not files or len(files) < 2:
        raise HTTPException(status_code=400, detail="Invalid input or missing files.")

    with tempfile.TemporaryDirectory() as temp_dir:
        input_file_paths = []

        # Save uploaded files to temporary directory
        for file in files:
            if not file.filename.endswith('.pdf'):
                raise HTTPException(status_code=400, detail="All files must be PDFs.")
            
            file_path = os.path.join(temp_dir, os.path.basename(file.filename))
            input_file_paths.append(file_path)
            
            with open(file_path, 'wb') as f:
                content = await file.read()
                f.write(content)

        output_file_path = os.path.join(temp_dir, "concatenated.pdf")

        try:
            # Construct and execute the pdfunite command
            command = ["pdfunite"] + input_file_paths + [output_file_path]
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError:
            raise HTTPException(status_code=500, detail="An error occurred while processing the files.")

        return FileResponse(output_file_path, media_type='application/pdf')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)