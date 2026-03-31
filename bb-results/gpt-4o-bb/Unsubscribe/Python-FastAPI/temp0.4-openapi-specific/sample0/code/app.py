from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, ValidationError
import re

app = FastAPI(
    title="UnsubscribeApp",
    description="UnsubscribeApp provides a simple endpoint to decide whether a user requested to be unsubscribed from a mailing list",
    version="1.0.11"
)

class UnsubscribeResponse(BaseModel):
    email: EmailStr
    unsubscribe: bool

@app.post("/decideUnsubscribe", response_model=UnsubscribeResponse)
async def decide_unsubscribe(request: Request):
    try:
        raw_email = await request.body()
        raw_email = raw_email.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid email content") from e

    try:
        from_email = re.search(r"From:\s*([^<]+)<([^>]+)>", raw_email)
        if not from_email:
            raise ValueError("Email format invalid")
        email_address = from_email.group(2).strip()

        unsubscribe_keywords = [
            "unsubscribe", "remove me", "deregister me", "stop sending me", "delete me"
        ]

        unsubscribe_decision = any(keyword.lower() in raw_email.lower() for keyword in unsubscribe_keywords)

        return UnsubscribeResponse(email=email_address, unsubscribe=unsubscribe_decision)
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)