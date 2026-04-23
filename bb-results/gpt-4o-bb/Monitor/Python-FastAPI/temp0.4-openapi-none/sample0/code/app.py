import re
import subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(
    title="Monitor Service",
    description="A service that accepts a filter criterion and returns a list of matching process IDs.",
    version="1.0.0"
)

class ProcessFilter(BaseModel):
    filter_flags: str = "aux -T"
    command_regex: str

class ProcessInfo(BaseModel):
    processId: int
    processString: str

@app.post("/monitor/commands", response_model=List[ProcessInfo])
async def get_running_processes(filter_criteria: ProcessFilter):
    try:
        # Execute the ps command with the given filter flags
        result = subprocess.run(
            ["ps"] + filter_criteria.filter_flags.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        # Split the output into lines and ignore the header
        lines = result.stdout.strip().split("\n")[1:]

        # Compile the regex pattern
        pattern = re.compile(filter_criteria.command_regex)

        # Filter processes based on the command regex
        matching_processes = []
        for line in lines:
            columns = line.split(None, 10)  # Split into at most 11 parts
            if len(columns) < 11:
                continue
            pid = columns[1]
            command = columns[10]
            if pattern.search(command):
                matching_processes.append(ProcessInfo(processId=int(pid), processString=line))

        return matching_processes

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error executing ps command: {e.stderr}")

    except re.error as e:
        raise HTTPException(status_code=400, detail=f"Invalid regular expression: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)