from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# Define keywords that indicate an unsubscribe request
UNSUBSCRIBE_KEYWORDS = [
    "unsubscribe", "remove me", "deregister me", "stop sending me", "delete me"
]

def extract_email(raw_email):
    """Extract the email address from the raw email string."""
    match = re.search(r'From:\s*.*<(.+?)>', raw_email)
    if match:
        return match.group(1)
    return None

def check_unsubscribe_request(raw_email):
    """Check if the email contains unsubscribe keywords."""
    # Check the plain text part of the email for unsubscribe keywords
    for keyword in UNSUBSCRIBE_KEYWORDS:
        if keyword in raw_email.lower():
            return True
    return False

@app.route('/decideUnsubscribe', methods=['POST'])
def decide_unsubscribe():
    raw_email = request.data.decode('utf-8')
    
    email_address = extract_email(raw_email)
    if not email_address:
        return jsonify({"error": "Invalid email format"}), 400

    should_unsubscribe = check_unsubscribe_request(raw_email)

    response = {
        "email": email_address,
        "unsubscribe": should_unsubscribe
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)