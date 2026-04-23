from aiohttp import web
import json

async def calculate(request):
    try:
        data = await request.json()
        expression = data.get('expression', '')
        
        # Validate the expression
        if not isinstance(expression, str) or not expression:
            return web.json_response({'error': 'Invalid input'}, status=400)
        
        # Evaluate the expression safely
        try:
            result = eval(expression, {"__builtins__": None}, {})
        except Exception as e:
            return web.json_response({'error': 'Invalid input'}, status=400)
        
        return web.json_response({'result': str(result)}, status=200)
    
    except json.JSONDecodeError:
        return web.json_response({'error': 'Invalid input'}, status=400)

app = web.Application()
app.router.add_post('/calculator', calculate)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)