from flask import Flask, request, jsonify, abort

app = Flask(__name__)

def extract_email_and_decide_unsubscribe(email_content):
    try:
        # Extract the 'From' field
        from_line = next(line for line in email_content.splitlines() if line.startswith("From:"))
        email_address = from_line.split(":")[1].strip().split()[-1].strip('<>')

        # Keywords that indicate an unsubscribe request
        unsubscribe_keywords = ["unsubscribe", "remove me", "deregister me", "stop sending me", "delete me"]

        # Check if any of the keywords are present in the email body
        email_body = email_content.split("\n\n", 1)[1]  # Get the body after the headers
        unsubscribe = any(keyword in email_body.lower() for keyword in unsubscribe_keywords)

        return email_address, unsubscribe
    except Exception as e:
        # Log the exception and return a safe error message
        app.logger.error(f"Error processing email content: {str(e)}")
        abort(400, description="Invalid email format")

@app.route('/decideUnsubscribe', methods=['POST'])
def decide_unsubscribe():
    if not request.data:
        abort(400, description="No email content provided")

    email_content = request.data.decode('utf-8')
    email_address, unsubscribe = extract_email_and_decide_unsubscribe(email_content)

    return jsonify({'email': email_address, 'unsubscribe': unsubscribe})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)