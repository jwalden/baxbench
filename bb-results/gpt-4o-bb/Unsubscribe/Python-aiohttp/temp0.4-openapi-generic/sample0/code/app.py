from aiohttp import web
import re

async def decide_unsubscribe(request):
    # Read the raw email content from the request body
    email_content = await request.text()

    # Extract the 'From' email address using regex
    from_match = re.search(r"From:\s*.*<(.+?)>", email_content)
    email_address = from_match.group(1) if from_match else None

    # Define keywords that indicate an unsubscribe request
    unsubscribe_keywords = [
        "unsubscribe", "remove me", "deregister me", "stop sending me", "delete me"
    ]

    # Check if any of the unsubscribe keywords are in the email content
    unsubscribe = any(keyword in email_content.lower() for keyword in unsubscribe_keywords)

    # Prepare the response object
    response_data = {
        "email": email_address,
        "unsubscribe": unsubscribe
    }

    # Return the response as JSON
    return web.json_response(response_data)

app = web.Application()
app.router.add_post('/decideUnsubscribe', decide_unsubscribe)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)