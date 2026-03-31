import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def decide_unsubscribe(request):
    email_content = request.body.decode('utf-8')

    # Extract the email address from the "From" header
    from_match = re.search(r'From:\s*([^<]+)<([^>]+)>', email_content)
    if not from_match:
        return JsonResponse({'error': 'Invalid email format'}, status=400)

    email_address = from_match.group(2).strip()

    # Define keywords that indicate an unsubscribe request
    unsubscribe_keywords = [
        "unsubscribe", "remove me", "deregister me", "stop sending me", "delete me"
    ]

    # Check if any of the keywords are present in the email content
    unsubscribe = any(keyword.lower() in email_content.lower() for keyword in unsubscribe_keywords)

    return JsonResponse({'email': email_address, 'unsubscribe': unsubscribe})