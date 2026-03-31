from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import subprocess
import re

app = FastAPI(
    title="Monitor Service",
    description="A service that accepts a filter criterion and returns a list of matching process IDs.",
    version="1.0.0"
)

class ProcessFilter(BaseModel):
    filter_flags: str = Field(default="aux", description="Flags to filter and sort processes, matching the flags of the 'ps' command")
    command_regex: str = Field(..., description="The regular expression of the commands to search for on the server")

class ProcessInfo(BaseModel):
    processId: int
    processString: str

@app.post("/monitor/commands", response_model=list[ProcessInfo])
async def get_matching_processes(filter: ProcessFilter):
    try:
        # Run the 'ps' command with the provided flags
        result = subprocess.run(
            ["ps", filter.filter_flags],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error executing 'ps' command: {str(e)}")

    # Compile the regex pattern
    try:
        pattern = re.compile(filter.command_regex)
    except re.error as e:
        raise HTTPException(status_code=400, detail=f"Invalid regular expression: {str(e)}")

    # Parse the output and filter with regex
    processes = []
    for line in result.stdout.splitlines():
        if pattern.search(line):
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                continue
            try:
                pid = int(parts[0])
                processes.append(ProcessInfo(processId=pid, processString=line))
            except ValueError:
                continue

    return processes

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)