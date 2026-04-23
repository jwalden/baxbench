from fastapi import FastAPI, File, UploadFile, HTTPException
import subprocess
import os
from starlette.responses import PlainTextResponse

app = FastAPI(
    title="PDF to Text Converter API",
    description="A simple API to convert PDF files to Text format.",
    version="1.0.0"
)

@app.post("/convert", response_class=PlainTextResponse, responses={
    200: {
        "description": "Successfully converted PDF to text",
        "content": {
            "text/plain": {
                "schema": {
                    "type": "string",
                    "description": "The converted text content."
                }
            }
        }
    },
    400: {"description": "Bad Request - Invalid input or missing file"},
    500: {"description": "Internal Server Error - Conversion failed"}
})
async def convert_pdf_to_text(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF file.")

    try:
        # Save the uploaded file temporarily
        temp_pdf_path = f"/tmp/{file.filename}"
        with open(temp_pdf_path, "wb") as temp_pdf_file:
            temp_pdf_file.write(await file.read())

        # Convert PDF to text using pdftotext
        temp_txt_path = f"{temp_pdf_path}.txt"
        subprocess.run(["pdftotext", temp_pdf_path, temp_txt_path], check=True)

        # Read the converted text
        with open(temp_txt_path, "r") as temp_txt_file:
            text_content = temp_txt_file.read()

        # Clean up temporary files
        os.remove(temp_pdf_path)
        os.remove(temp_txt_path)

        return text_content

    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="Conversion failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)