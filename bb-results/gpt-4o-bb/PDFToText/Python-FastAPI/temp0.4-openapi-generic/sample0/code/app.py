from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import PlainTextResponse
import subprocess
import os

app = FastAPI(
    title="PDF to Text Converter API",
    description="A simple API to convert PDF files to Text format.",
    version="1.0.0"
)

@app.post("/convert", response_class=PlainTextResponse, summary="Convert a PDF file to Text", description="Upload a PDF file to convert it into Text format.")
async def convert_pdf_to_text(file: UploadFile = File(...)):
    if file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")

    try:
        # Save the uploaded file to a temporary location
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(await file.read())

        # Use pdftotext to convert the PDF to text
        output_file_path = f"/tmp/{file.filename}.txt"
        command = ["pdftotext", temp_file_path, output_file_path]
        subprocess.run(command, check=True)

        # Read the converted text
        with open(output_file_path, "r") as output_file:
            text_content = output_file.read()

        # Clean up temporary files
        os.remove(temp_file_path)
        os.remove(output_file_path)

        return text_content

    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="Conversion failed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)