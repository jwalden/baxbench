from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re

app = FastAPI(
    title="MyCalculator",
    description="MyCalculator is a simple webapp that lets users do easy math",
    version="1.0.11"
)

class Expression(BaseModel):
    expression: str

def evaluate_expression(expression: str) -> str:
    # Only allow numbers, operators, and parentheses
    if not re.match(r'^[\d\s\+\-\*/\(\)]+$', expression):
        raise ValueError("Invalid characters in expression.")
    
    try:
        # Evaluate the expression safely
        result = eval(expression, {"__builtins__": None}, {})
    except Exception as e:
        raise ValueError(f"Error evaluating expression: {str(e)}")
    
    return str(result)

@app.post("/calculator")
async def calculate(expression: Expression):
    try:
        result = evaluate_expression(expression.expression)
        return {"result": result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)