from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Keywords to identify unsubscribe requests
UNSUBSCRIBE_KEYWORDS = [
    "unsubscribe",
    "remove me",
    "deregister me",
    "stop sending me",
    "delete me"
]

def extract_email(raw_email):
    """Extract the email address from the 'From' field."""
    match = re.search(r'From:.*<(.+?)>', raw_email)
    return match.group(1) if match else None

def check_unsubscribe_request(raw_email):
    """Check if the email contains unsubscribe keywords."""
    for keyword in UNSUBSCRIBE_KEYWORDS:
        if keyword.lower() in raw_email.lower():
            return True
    return False

@app.route('/decideUnsubscribe', methods=['POST'])
def decide_unsubscribe():
    raw_email = request.data.decode('utf-8')
    email_address = extract_email(raw_email)
    unsubscribe = check_unsubscribe_request(raw_email)
    
    if email_address:
        return jsonify({
            "email": email_address,
            "unsubscribe": unsubscribe
        }), 200
    else:
        return jsonify({
            "error": "Invalid email format"
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)