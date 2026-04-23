from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
@require_POST
def calculate(request):
    try:
        data = json.loads(request.body)
        expression = data.get('expression', '')
        
        # Evaluate the expression safely
        try:
            # Limit the scope of eval to prevent security issues
            result = eval(expression, {"__builtins__": None}, {})
        except Exception:
            return JsonResponse({'error': 'Invalid input'}, status=400)

        return JsonResponse({'result': str(result)}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)