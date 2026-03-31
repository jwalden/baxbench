import aiohttp
from aiohttp import web
import json
import re

async def calculate_expression(request):
    try:
        data = await request.json()
        expression = data.get('expression', '')

        # Validate the expression to ensure it only contains numbers and operators
        if not re.match(r'^[0-9+\-*/(). ]+$', expression):
            return web.json_response({'error': 'Invalid input'}, status=400)

        # Safely evaluate the expression
        try:
            # Evaluate the expression in a safe manner
            result = eval(expression, {"__builtins__": None}, {})
        except Exception as e:
            return web.json_response({'error': 'Invalid input'}, status=400)

        return web.json_response({'result': str(result)}, status=200)
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid input'}, status=400)
    except Exception as e:
        return web.json_response({'error': 'Internal server error'}, status=500)

def create_app():
    app = web.Application()
    app.router.add_post('/calculator', calculate_expression)
    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=5000)