import aiohttp
from aiohttp import web
import re

# Keywords to identify unsubscribe requests
UNSUBSCRIBE_KEYWORDS = [
    "unsubscribe", "remove me", "deregister me", "stop sending me", "delete me"
]

async def decide_unsubscribe(request):
    try:
        # Read the raw email content from the request body
        email_content = await request.text()

        # Extract the 'From' email address using regex
        from_match = re.search(r"From:\s*.*<(.+?)>", email_content)
        if not from_match:
            return web.json_response({'error': 'Invalid email format'}, status=400)
        
        from_email = from_match.group(1)

        # Check if any of the unsubscribe keywords are present in the email content
        unsubscribe = any(keyword in email_content.lower() for keyword in UNSUBSCRIBE_KEYWORDS)

        # Return the response as JSON
        return web.json_response({
            'email': from_email,
            'unsubscribe': unsubscribe
        })

    except Exception as e:
        # Log the exception and return a generic error message
        print(f"Exception occurred: {e}")
        return web.json_response({'error': 'An error occurred while processing the request'}, status=500)

def create_app():
    app = web.Application()

    # Define the route for the /decideUnsubscribe endpoint
    app.router.add_post('/decideUnsubscribe', decide_unsubscribe)

    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=5000)