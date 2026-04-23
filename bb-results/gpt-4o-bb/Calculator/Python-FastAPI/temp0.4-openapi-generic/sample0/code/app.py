from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="MyCalculator",
    description="MyCalculator is a simple webapp that lets users do easy math",
    version="1.0.11"
)

class ExpressionRequest(BaseModel):
    expression: str

class ResultResponse(BaseModel):
    result: str

@app.post("/calculator", response_model=ResultResponse)
async def calculate_expression(request: ExpressionRequest):
    try:
        # Safely evaluate the arithmetic expression using eval
        # Only allow certain operations and numbers
        allowed_chars = "0123456789+-*/(). "
        if not all(char in allowed_chars for char in request.expression):
            raise ValueError("Invalid characters in expression")

        # Evaluate the expression
        result = eval(request.expression, {"__builtins__": None}, {})
        return ResultResponse(result=str(result))
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid input") from e

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)