from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import subprocess
from typing import List

app = FastAPI(
    title="PDF Concatenation Service",
    description="A service that concatenates multiple PDF files into a single PDF.",
    version="1.0.0"
)

@app.post("/concatenate", summary="Concatenate multiple PDF files", description="Accepts multiple PDF files and returns a single concatenated PDF.")
async def concatenate_pdfs(files: List[UploadFile] = File(...)):
    if not files or len(files) < 2:
        raise HTTPException(status_code=400, detail="Invalid input or missing files. At least two PDF files are required.")

    input_file_paths = []
    try:
        # Save uploaded files to disk
        for file in files:
            if file.content_type != "application/pdf":
                raise HTTPException(status_code=400, detail="All files must be in PDF format.")
            file_path = f"/tmp/{file.filename}"
            with open(file_path, "wb") as f:
                f.write(await file.read())
            input_file_paths.append(file_path)

        # Define the output file path
        output_file_path = "/tmp/concatenated.pdf"

        # Use pdfunite to concatenate the PDF files
        subprocess.run(["pdfunite", *input_file_paths, output_file_path], check=True)

        # Return the concatenated PDF file
        return FileResponse(output_file_path, media_type="application/pdf", filename="concatenated.pdf")

    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="An error occurred while processing the files.")
    finally:
        # Clean up temporary files
        for file_path in input_file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)
        if os.path.exists(output_file_path):
            os.remove(output_file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)