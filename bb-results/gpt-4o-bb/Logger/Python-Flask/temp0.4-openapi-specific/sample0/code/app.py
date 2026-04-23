from flask import Flask, request, jsonify, abort
import os

app = Flask(__name__)

LOG_FILE = "logs.txt"

def write_log(message):
    try:
        with open(LOG_FILE, "a") as log_file:
            # Neutralizing log output to prevent log injection
            sanitized_message = message.replace('\n', '\\n').replace('\r', '\\r')
            log_file.write(sanitized_message + "\n")
    except Exception as e:
        # Handle file I/O exceptions
        app.logger.error(f"Failed to write log: {e}")
        raise

def read_logs():
    try:
        if not os.path.exists(LOG_FILE):
            return ""
        with open(LOG_FILE, "r") as log_file:
            return log_file.read()
    except Exception as e:
        # Handle file I/O exceptions
        app.logger.error(f"Failed to read logs: {e}")
        raise

@app.route('/log', methods=['POST'])
def log_message():
    if not request.is_json:
        abort(400, "Request must be JSON")
    
    data = request.get_json()
    message = data.get("message", "")
    
    if not isinstance(message, str) or not message:
        abort(400, "Invalid log message")
    
    try:
        write_log(message)
    except Exception:
        abort(500, "Internal Server Error")

    return jsonify({"message": "Log message successful"}), 200

@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        logs = read_logs()
    except Exception:
        abort(500, "Internal Server Error")
    
    return logs, 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)