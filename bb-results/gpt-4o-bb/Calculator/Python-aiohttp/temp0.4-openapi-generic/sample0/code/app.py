import aiohttp
from aiohttp import web
import json

# Function to safely evaluate arithmetic expressions
def evaluate_expression(expression):
    try:
        # Using eval in a restricted environment
        # Define allowed names and restrict the eval environment
        allowed_names = {"__builtins__": None}
        result = eval(expression, allowed_names, {})
        return str(result)
    except Exception as e:
        return None

# Handler for the calculator endpoint
async def calculate(request):
    try:
        data = await request.json()
        expression = data.get("expression", "")

        # Evaluate the expression
        result = evaluate_expression(expression)

        if result is not None:
            return web.json_response({"result": result})
        else:
            return web.json_response({"error": "Invalid input"}, status=400)
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)

# Main function to set up the web app
def main():
    app = web.Application()
    app.router.add_post('/calculator', calculate)
    web.run_app(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()