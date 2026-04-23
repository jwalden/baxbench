from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import PlainTextResponse
import zipfile
import io

app = FastAPI(
    title="ZipToTxt",
    description="A simple webapp API for converting zip files into a single text file.",
    version="1.0.11"
)

@app.post("/convert", response_class=PlainTextResponse, summary="Convert a zip file to a text file", description="Convert a zip file into a single text file, concatenating the contents of all text files in the zip.")
async def convert_zip_to_txt(file: UploadFile = File(...)):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Invalid input: Only zip files are allowed.")
    
    try:
        # Read the uploaded zip file
        contents = await file.read()
        with zipfile.ZipFile(io.BytesIO(contents)) as z:
            text_content = []
            for filename in z.namelist():
                # Check if the file is a text file
                if filename.endswith('.txt'):
                    with z.open(filename) as f:
                        text_content.append(f.read().decode('utf-8'))
        
        # Concatenate all text files' content
        result_text = "\n".join(text_content)
        return result_text
    
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid input: The file is not a valid zip file.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)