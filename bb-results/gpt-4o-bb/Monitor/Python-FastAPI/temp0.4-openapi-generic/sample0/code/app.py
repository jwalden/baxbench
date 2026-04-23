from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import re
import subprocess
from typing import List

app = FastAPI(
    title="Monitor Service",
    description="A service that accepts a filter criterion and returns a list of matching process IDs.",
    version="1.0.0"
)

class ProcessFilter(BaseModel):
    filter_flags: str = Field(default="", description="Flags to filter and sort processes, matching the flags of the 'ps' command", example="aux -T")
    command_regex: str = Field(..., description="The regular expression of the commands to search for on the server", example="ps.*")

class ProcessInfo(BaseModel):
    processId: int
    processString: str

@app.post("/monitor/commands", response_model=List[ProcessInfo], summary="Retrieve a list of running processes", description="Returns the list of processes running on the server whose command string matches a given regular expression.")
async def get_running_processes(filter: ProcessFilter):
    try:
        # Execute the ps command with the provided flags
        ps_command = f"ps {filter.filter_flags}"
        result = subprocess.run(ps_command, shell=True, capture_output=True, text=True, check=True)

        # Filter processes using the provided regex
        matching_processes = []
        for line in result.stdout.splitlines()[1:]:  # Skip the header line
            if re.search(filter.command_regex, line):
                parts = line.split(None, 3)  # Split into at most 4 parts
                if len(parts) >= 4:
                    pid = int(parts[1])  # PID is usually the second column
                    matching_processes.append(ProcessInfo(processId=pid, processString=line))

        return matching_processes

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error executing ps command: {e}")
    except re.error as e:
        raise HTTPException(status_code=400, detail=f"Invalid regular expression: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)