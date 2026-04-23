from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, EmailStr
import re
from typing import Dict
import uvicorn

app = FastAPI(
    title="UnsubscribeApp",
    description="UnsubscribeApp provides a simple endpoint to decide whether a user requested to be unsubscribed from a mailing list",
    version="1.0.11"
)

class UnsubscribeResponse(BaseModel):
    email: EmailStr
    unsubscribe: bool

@app.post("/decideUnsubscribe", response_model=UnsubscribeResponse, summary="Decide unsubscribe request")
async def decide_unsubscribe(request: Request):
    raw_email = await request.body()
    raw_email_str = raw_email.decode('utf-8')

    # Extract the email address from the 'From' header
    from_match = re.search(r'From:\s*(.*?)(?:<(.+?)>)?\s*$', raw_email_str, re.MULTILINE)
    if not from_match:
        raise HTTPException(status_code=400, detail="Invalid email format: Missing 'From' header")

    email_address = from_match.group(2) if from_match.group(2) else from_match.group(1).strip()

    # Keywords indicating unsubscribe intent
    unsubscribe_keywords = [
        "unsubscribe", "remove me", "deregister me", "stop sending me", "delete me"
    ]

    # Check for unsubscribe keywords in the email body
    unsubscribe = any(keyword.lower() in raw_email_str.lower() for keyword in unsubscribe_keywords)

    return UnsubscribeResponse(email=email_address, unsubscribe=unsubscribe)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)