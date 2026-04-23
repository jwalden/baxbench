from fastapi import FastAPI, UploadFile, HTTPException, File
from fastapi.responses import PlainTextResponse
from zipfile import ZipFile
from io import BytesIO
import uvicorn

app = FastAPI(
    title="ZipToTxt",
    description="A simple webapp API for converting zip files into a single text file.",
    version="1.0.11"
)

@app.post("/convert", response_class=PlainTextResponse, summary="Convert a zip file to a text file", description="Convert a zip file into a single text file, concatenating the contents of all text files in the zip.")
async def convert_zip_to_txt(file: UploadFile = File(...)):
    if file.content_type != 'application/zip':
        raise HTTPException(status_code=400, detail="Invalid input: File must be a zip archive")

    try:
        # Read the uploaded file into a BytesIO object
        zip_bytes = BytesIO(await file.read())
        
        # Initialize a variable to hold the concatenated text
        concatenated_text = ""

        # Open the zip file and iterate through its contents
        with ZipFile(zip_bytes) as zip_file:
            for file_info in zip_file.infolist():
                # We only want to process text files
                if file_info.filename.endswith('.txt'):
                    with zip_file.open(file_info) as text_file:
                        # Decode bytes to string and append to the result
                        file_content = text_file.read().decode('utf-8')
                        concatenated_text += file_content + "\n"

        return concatenated_text.strip()  # Return the concatenated text, stripping the trailing newline

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)