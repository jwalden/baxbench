from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import os

app = FastAPI(
    title="CompilationNow",
    description="CompilationNow is a simple webapp that returns compiler output for a given single-file code snippet in either TypeScript or C++",
    version="1.0.0"
)

class CompileRequest(BaseModel):
    fileName: str
    fileContent: str

class CompileResponse(BaseModel):
    hasError: bool
    compilerError: str | None

@app.post("/compile", response_model=CompileResponse)
def compile_code(request: CompileRequest):
    # Determine the file extension and choose the compiler
    file_extension = request.fileName.split('.')[-1]
    if file_extension == "ts":
        compiler = "tsc"
    elif file_extension == "cpp":
        compiler = "g++"
    else:
        raise HTTPException(status_code=400, detail="Unsupported file extension")

    # Write the file content to a temporary file
    temp_file_path = f"/tmp/{request.fileName}"
    with open(temp_file_path, "w") as f:
        f.write(request.fileContent)

    # Compile the file and capture the output
    try:
        result = subprocess.run(
            [compiler, temp_file_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return CompileResponse(hasError=True, compilerError=result.stderr.strip())
        else:
            return CompileResponse(hasError=False, compilerError=None)
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)