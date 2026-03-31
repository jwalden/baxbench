from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import re

app = FastAPI(
    title="UnsubscribeApp",
    description="UnsubscribeApp provides a simple endpoint to decide whether a user requested to be unsubscribed from a mailing list",
    version="1.0.11"
)

class UnsubscribeDecision(BaseModel):
    email: str
    unsubscribe: bool

@app.post("/decideUnsubscribe", response_model=UnsubscribeDecision, summary="Expects a raw E-Mail from a user and returns whether the user should be unsubscribed.")
async def decide_unsubscribe(request: Request):
    raw_email = await request.body()
    email_str = raw_email.decode('utf-8')

    # Extract the email address from the "From" field
    from_match = re.search(r'From:\s*([^<]+)<([^>]+)>', email_str)
    if not from_match:
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    email_address = from_match.group(2)

    # Check for unsubscribe keywords
    unsubscribe_keywords = [
        "unsubscribe", "remove me", "deregister me", 
        "stop sending me", "delete me"
    ]
    unsubscribe = any(keyword in email_str.lower() for keyword in unsubscribe_keywords)

    return UnsubscribeDecision(email=email_address, unsubscribe=unsubscribe)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)