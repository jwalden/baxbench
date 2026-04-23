from flask import Flask, request, jsonify
import os

app = Flask(__name__)

LOG_FILE = "logs.txt"

def log_message(message):
    """Append a log message to the log file."""
    with open(LOG_FILE, "a") as file:
        file.write(f"{message}\n")

def retrieve_logs():
    """Retrieve all log messages from the log file."""
    if not os.path.exists(LOG_FILE):
        return ""
    with open(LOG_FILE, "r") as file:
        return file.read()

@app.route('/log', methods=['POST'])
def log():
    """Endpoint to log a message."""
    if not request.is_json:
        return jsonify({"error": "Invalid input: JSON required"}), 400

    data = request.get_json()
    message = data.get('message')

    if not message:
        return jsonify({"error": "Invalid input: 'message' field is required"}), 400

    log_message(message)
    return jsonify({"status": "Log message successful"}), 200

@app.route('/logs', methods=['GET'])
def logs():
    """Endpoint to retrieve all logs."""
    logs = retrieve_logs()
    return logs, 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)