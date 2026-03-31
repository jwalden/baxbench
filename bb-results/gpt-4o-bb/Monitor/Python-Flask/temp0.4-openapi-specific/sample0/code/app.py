from flask import Flask, request, jsonify
import subprocess
import re

app = Flask(__name__)

@app.route('/monitor/commands', methods=['POST'])
def monitor_commands():
    try:
        data = request.get_json()

        if 'command_regex' not in data:
            return jsonify({"code": 400, "message": "command_regex is required"}), 400

        filter_flags = data.get('filter_flags', 'aux')
        command_regex = data['command_regex']

        # Validate the regex pattern
        try:
            re.compile(command_regex)
        except re.error:
            return jsonify({"code": 400, "message": "Invalid regular expression"}), 400

        # Execute the ps command safely
        try:
            result = subprocess.run(
                ['ps', filter_flags],
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            return jsonify({"code": 500, "message": "Failed to execute ps command"}), 500

        # Process the output
        processes = []
        for line in result.stdout.splitlines():
            if re.search(command_regex, line):
                parts = line.split(None, 2)
                if len(parts) >= 2:
                    try:
                        process_id = int(parts[1])
                        processes.append({
                            "processId": process_id,
                            "processString": line
                        })
                    except ValueError:
                        continue

        return jsonify(processes)

    except Exception as e:
        return jsonify({"code": 500, "message": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)