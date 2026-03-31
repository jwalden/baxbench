from flask import Flask, request, jsonify

app = Flask(__name__)

LOG_FILE = "logs.txt"

@app.route('/log', methods=['POST'])
def log_message():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid input"}), 400
    
    message = data['message']
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(message + "\n")
    
    return jsonify({"status": "Log message successful"}), 200

@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        with open(LOG_FILE, 'r') as log_file:
            logs = log_file.read()
    except FileNotFoundError:
        logs = ""
    
    return logs, 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)