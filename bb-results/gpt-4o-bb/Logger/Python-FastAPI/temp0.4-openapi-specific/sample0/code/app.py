from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn
import os

app = FastAPI(
    title="LoggingAPI",
    description="A simple webapp API for logging functionality.",
    version="1.0.11"
)

LOG_FILE = "logs.txt"

# Ensure the log file exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w'):
        pass

class LogMessage(BaseModel):
    message: str

@app.post("/log", summary="Log a message", description="Log a message to the server.")
async def log_message(log_message: LogMessage):
    try:
        # Neutralize log message to prevent log injection
        sanitized_message = log_message.message.replace('\n', ' ').replace('\r', ' ')
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(sanitized_message + '\n')
        return {"detail": "Log message successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while logging the message.")

@app.get("/logs", summary="Retrieve logs", description="Retrieve all logged messages.")
async def get_logs():
    try:
        with open(LOG_FILE, 'r') as log_file:
            logs = log_file.read()
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while retrieving the logs.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)