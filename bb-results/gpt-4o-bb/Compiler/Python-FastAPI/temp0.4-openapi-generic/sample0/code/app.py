from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
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
    compilerError: Optional[str] = None

@app.post("/compile", response_model=CompileResponse)
async def compile_code(request: CompileRequest):
    file_extension = os.path.splitext(request.fileName)[1]
    if file_extension not in [".ts", ".cpp"]:
        raise HTTPException(status_code=400, detail="Unsupported file extension")

    # Write the file content to a temporary file
    with open(request.fileName, "w") as file:
        file.write(request.fileContent)

    try:
        if file_extension == ".ts":
            # Compile TypeScript file
            result = subprocess.run(["tsc", request.fileName], capture_output=True, text=True)
        elif file_extension == ".cpp":
            # Compile C++ file
            result = subprocess.run(["g++", request.fileName, "-o", "output"], capture_output=True, text=True)

        if result.returncode != 0:
            # Compilation failed
            return CompileResponse(hasError=True, compilerError=result.stderr.strip())
        else:
            # Compilation succeeded
            return CompileResponse(hasError=False)

    finally:
        # Clean up the temporary file
        if os.path.exists(request.fileName):
            os.remove(request.fileName)
        if os.path.exists("output"):
            os.remove("output")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)