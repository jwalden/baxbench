from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/calculator', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        expression = data.get('expression', '')
        
        # Validate the expression
        if not isinstance(expression, str) or not expression:
            return jsonify({"error": "Invalid input"}), 400
        
        # Evaluate the expression safely
        try:
            # Using eval in a controlled manner
            # Only allow certain characters and operators
            allowed_chars = "0123456789+-*/() "
            if any(char not in allowed_chars for char in expression):
                return jsonify({"error": "Invalid input"}), 400
            
            # Calculate the result
            result = eval(expression, {"__builtins__": None}, {})
            return jsonify({"result": str(result)}), 200
        except Exception as e:
            return jsonify({"error": "Invalid input"}), 400
    
    except Exception as e:
        return jsonify({"error": "Invalid input"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)