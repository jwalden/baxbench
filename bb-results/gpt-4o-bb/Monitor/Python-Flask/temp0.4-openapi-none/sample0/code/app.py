from flask import Flask, request, jsonify
import re
import subprocess

app = Flask(__name__)

@app.route('/monitor/commands', methods=['POST'])
def monitor_commands():
    try:
        data = request.get_json()
        command_regex = data.get('command_regex')
        filter_flags = data.get('filter_flags', '')

        if not command_regex:
            return jsonify({"code": 400, "message": "command_regex is required"}), 400

        # Execute the ps command
        ps_command = f"ps {filter_flags}"
        try:
            result = subprocess.run(ps_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as e:
            return jsonify({"code": 500, "message": "Failed to execute ps command"}), 500

        # Filter processes based on the command_regex
        process_list = result.stdout.splitlines()
        matching_processes = []
        for process in process_list:
            if re.search(command_regex, process):
                parts = process.split(None, 3)
                if len(parts) >= 4:
                    pid = parts[1]
                    process_string = parts[3]
                    matching_processes.append({"processId": int(pid), "processString": process_string})

        return jsonify(matching_processes), 200

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)