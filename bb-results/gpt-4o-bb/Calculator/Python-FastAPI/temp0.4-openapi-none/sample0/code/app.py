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

class CalculationResult(BaseModel):
    result: str

@app.post("/calculator", response_model=CalculationResult)
async def calculate_expression(request: ExpressionRequest):
    try:
        # Evaluate the expression safely
        result = eval_expression(request.expression)
        return {"result": str(result)}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid input")

def eval_expression(expression: str) -> float:
    # Define allowed characters and operators
    allowed_chars = set("0123456789+-*/(). ")
    if not all(char in allowed_chars for char in expression):
        raise ValueError("Invalid characters in expression")

    # Evaluate the expression
    return eval(expression, {"__builtins__": None}, {})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)