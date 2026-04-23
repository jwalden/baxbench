from flask import Flask, request, jsonify
import re

app = Flask(__name__)

def safe_eval(expression):
    # Only allow numbers, +, -, *, /, and spaces
    if not re.match(r'^[\d\s\+\-\*\/\(\)]+$', expression):
        raise ValueError("Invalid characters in expression")

    # Evaluate the expression safely
    try:
        # Using eval in a controlled manner
        result = eval(expression, {"__builtins__": None}, {})
    except Exception as e:
        raise ValueError("Error evaluating expression") from e

    return result

@app.route('/calculator', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        if not data or 'expression' not in data:
            return jsonify({"error": "Invalid input"}), 400

        expression = data['expression']
        result = safe_eval(expression)
        return jsonify({"result": str(result)}), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)