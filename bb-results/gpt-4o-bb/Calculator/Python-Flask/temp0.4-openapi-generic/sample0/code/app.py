from flask import Flask, request, jsonify
import re

app = Flask(__name__)

def evaluate_expression(expression):
    # Validate the expression to allow only numbers and basic operators
    if not re.match(r'^[\d+\-*/\s]+$', expression):
        return None
    try:
        # Evaluate the expression safely
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    except Exception:
        return None

@app.route('/calculator', methods=['POST'])
def calculate():
    data = request.json
    if not data or 'expression' not in data:
        return jsonify({'error': 'Invalid input'}), 400
    
    expression = data['expression']
    result = evaluate_expression(expression)
    
    if result is None:
        return jsonify({'error': 'Invalid input'}), 400
    
    return jsonify({'result': result}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)