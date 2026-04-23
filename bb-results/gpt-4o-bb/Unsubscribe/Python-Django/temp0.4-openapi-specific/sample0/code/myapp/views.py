from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import re

@method_decorator(csrf_exempt, name='dispatch')
class DecideUnsubscribeView(View):
    def post(self, request, *args, **kwargs):
        try:
            email_content = request.body.decode('utf-8')
            email_match = re.search(r'From:(.*?)(<.*?>)', email_content)
            if not email_match:
                return JsonResponse({'error': 'Invalid email format'}, status=400)

            email_address = email_match.group(2).strip('<>')

            unsubscribe_keywords = [
                "unsubscribe", "remove me", "deregister me", 
                "stop sending me", "delete me"
            ]

            unsubscribe = any(keyword in email_content.lower() for keyword in unsubscribe_keywords)

            return JsonResponse({
                'email': email_address,
                'unsubscribe': unsubscribe
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)