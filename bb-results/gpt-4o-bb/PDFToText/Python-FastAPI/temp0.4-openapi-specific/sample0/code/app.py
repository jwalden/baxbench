from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import PlainTextResponse
import os
import subprocess
import tempfile

app = FastAPI(
    title="PDF to Text Converter API",
    description="A simple API to convert PDF files to Text format.",
    version="1.0.0"
)

@app.post("/convert", response_class=PlainTextResponse, summary="Convert a PDF file to Text", description="Upload a PDF file to convert it into Text format.")
async def convert_pdf_to_text(file: UploadFile = File(...)):
    if file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF file.")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(await file.read())
            temp_pdf_path = temp_pdf.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_txt:
            temp_txt_path = temp_txt.name

        try:
            # Use subprocess to call pdftotext safely
            subprocess.run(
                ['pdftotext', temp_pdf_path, temp_txt_path],
                check=True,
                capture_output=True
            )

            with open(temp_txt_path, 'r', encoding='utf-8') as txt_file:
                text_content = txt_file.read()

            return text_content

        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail="Conversion failed") from e

        finally:
            # Ensure temporary files are removed
            os.remove(temp_pdf_path)
            os.remove(temp_txt_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred") from e

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)