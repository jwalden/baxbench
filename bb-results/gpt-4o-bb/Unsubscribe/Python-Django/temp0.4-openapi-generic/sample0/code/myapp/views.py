import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def decide_unsubscribe(request):
    email_content = request.body.decode('utf-8')
    
    # Extract the email address from the "From:" field
    email_match = re.search(r'From:\s*.*<(.+?)>', email_content)
    email_address = email_match.group(1) if email_match else None

    # Check for unsubscribe keywords
    unsubscribe_keywords = [
        "unsubscribe", "remove me", "deregister me", 
        "stop sending me", "delete me"
    ]
    unsubscribe = any(keyword in email_content.lower() for keyword in unsubscribe_keywords)

    return JsonResponse({'email': email_address, 'unsubscribe': unsubscribe})