from aiohttp import web
import re

async def decide_unsubscribe(request):
    email_content = await request.text()
    from_email = re.search(r'From:\s*([^<]+<[^>]+>)', email_content)
    unsubscribe_keywords = [
        "unsubscribe", "remove me", "deregister me", 
        "stop sending me", "delete me"
    ]
    
    unsubscribe = any(keyword in email_content.lower() for keyword in unsubscribe_keywords)
    
    response_data = {
        "email": from_email.group(1) if from_email else "unknown",
        "unsubscribe": unsubscribe
    }
    
    return web.json_response(response_data)

app = web.Application()
app.router.add_post('/decideUnsubscribe', decide_unsubscribe)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=5000)