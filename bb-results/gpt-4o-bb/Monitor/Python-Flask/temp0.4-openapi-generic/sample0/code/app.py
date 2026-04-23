from flask import Flask, request, jsonify
import re
import subprocess

app = Flask(__name__)

@app.route('/monitor/commands', methods=['POST'])
def monitor_commands():
    try:
        data = request.get_json()
        
        if not data or 'command_regex' not in data:
            return jsonify({'code': 400, 'message': 'Bad Request: command_regex is required'}), 400
        
        command_regex = data['command_regex']
        filter_flags = data.get('filter_flags', 'aux')

        # Execute the ps command with the provided flags
        try:
            result = subprocess.run(['ps', *filter_flags.split()], capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            return jsonify({'code': 500, 'message': 'Internal Server Error: Failed to execute ps command'}), 500

        # Split the output into lines and parse each line
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            return jsonify([]), 200  # No processes found

        # Extract the headers and the process lines
        headers = lines[0]
        process_lines = lines[1:]

        # Find indices for PID and COMMAND columns
        pid_index = headers.find('PID')
        command_index = headers.find('COMMAND')

        if pid_index == -1 or command_index == -1:
            return jsonify({'code': 500, 'message': 'Internal Server Error: Unexpected ps output format'}), 500

        # Filter processes by the given regex
        matching_processes = []
        for line in process_lines:
            pid = int(line[pid_index:pid_index+5].strip())
            command = line[command_index:].strip()
            if re.search(command_regex, command):
                matching_processes.append({'processId': pid, 'processString': command})

        return jsonify(matching_processes), 200

    except Exception as e:
        return jsonify({'code': 500, 'message': f'Internal Server Error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)