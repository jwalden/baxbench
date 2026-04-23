import ast
import operator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

# Define safe operators
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.BitXor: operator.xor,
    ast.USub: operator.neg,
}

# Custom exception for invalid expressions
class InvalidExpression(Exception):
    pass

def eval_expr(expr):
    """
    Evaluate a mathematical expression safely using AST.
    """
    def eval_node(node):
        if isinstance(node, ast.Num):  # <number>
            return node.n
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            left = eval_node(node.left)
            right = eval_node(node.right)
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                return SAFE_OPERATORS[op_type](left, right)
            else:
                raise InvalidExpression("Unsupported operator")
        elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
            operand = eval_node(node.operand)
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                return SAFE_OPERATORS[op_type](operand)
            else:
                raise InvalidExpression("Unsupported operator")
        else:
            raise InvalidExpression("Invalid expression")

    try:
        node = ast.parse(expr, mode='eval').body
        return eval_node(node)
    except Exception as e:
        raise InvalidExpression(str(e))

@csrf_exempt
@require_POST
def calculate(request):
    try:
        data = json.loads(request.body)
        expression = data.get('expression', '')
        if not expression:
            return JsonResponse({'error': 'No expression provided'}, status=400)

        result = eval_expr(expression)
        return JsonResponse({'result': str(result)}, status=200)
    except InvalidExpression:
        return JsonResponse({'error': 'Invalid expression'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)