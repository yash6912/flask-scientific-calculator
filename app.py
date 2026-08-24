from flask import Flask, render_template, request, jsonify
import math
import ast
import operator
import re

app = Flask(__name__)


# ============================================================
# TRIGONOMETRIC FUNCTIONS
# ============================================================

def sin_function(x, mode):
    if mode == "DEG":
        x = math.radians(x)

    return math.sin(x)


def cos_function(x, mode):
    if mode == "DEG":
        x = math.radians(x)

    return math.cos(x)


def tan_function(x, mode):
    if mode == "DEG":
        x = math.radians(x)

    return math.tan(x)


def asin_function(x, mode):
    result = math.asin(x)

    if mode == "DEG":
        return math.degrees(result)

    return result


def acos_function(x, mode):
    result = math.acos(x)

    if mode == "DEG":
        return math.degrees(result)

    return result


def atan_function(x, mode):
    result = math.atan(x)

    if mode == "DEG":
        return math.degrees(result)

    return result


# ============================================================
# AVAILABLE FUNCTIONS
# ============================================================

def get_functions(mode):

    return {

        "sin": lambda x: sin_function(x, mode),

        "cos": lambda x: cos_function(x, mode),

        "tan": lambda x: tan_function(x, mode),

        "asin": lambda x: asin_function(x, mode),

        "acos": lambda x: acos_function(x, mode),

        "atan": lambda x: atan_function(x, mode),

        "sqrt": math.sqrt,

        "log": math.log10,

        "ln": math.log,

        "exp": math.exp,

        "abs": abs,

        "floor": math.floor,

        "ceil": math.ceil,

        "factorial": lambda x: math.factorial(int(x)),

        "pi": math.pi,

        "e": math.e
    }


# ============================================================
# SAFE CALCULATOR
# ============================================================

class Calculator:

    allowed_operators = {

        ast.Add: operator.add,

        ast.Sub: operator.sub,

        ast.Mult: operator.mul,

        ast.Div: operator.truediv,

        ast.Pow: operator.pow,

        ast.Mod: operator.mod,

        ast.USub: operator.neg,

        ast.UAdd: operator.pos
    }


    def __init__(self, mode="DEG"):

        self.mode = mode

        self.functions = get_functions(mode)


    def evaluate(self, expression):

        tree = ast.parse(
            expression,
            mode="eval"
        )

        return self._evaluate_node(
            tree.body
        )


    def _evaluate_node(self, node):

        # Numbers

        if isinstance(
            node,
            ast.Constant
        ):

            if isinstance(
                node.value,
                (int, float)
            ):

                return node.value

            raise ValueError(
                "Invalid number"
            )


        # Binary operations

        if isinstance(
            node,
            ast.BinOp
        ):

            operator_type = type(
                node.op
            )

            if operator_type not in self.allowed_operators:

                raise ValueError(
                    "Operator not allowed"
                )

            left = self._evaluate_node(
                node.left
            )

            right = self._evaluate_node(
                node.right
            )

            return self.allowed_operators[
                operator_type
            ](
                left,
                right
            )


        # Unary operations

        if isinstance(
            node,
            ast.UnaryOp
        ):

            operator_type = type(
                node.op
            )

            if operator_type not in self.allowed_operators:

                raise ValueError(
                    "Operator not allowed"
                )

            operand = self._evaluate_node(
                node.operand
            )

            return self.allowed_operators[
                operator_type
            ](
                operand
            )


        # Functions

        if isinstance(
            node,
            ast.Call
        ):

            if not isinstance(
                node.func,
                ast.Name
            ):

                raise ValueError(
                    "Invalid function"
                )

            function_name = node.func.id

            if function_name not in self.functions:

                raise ValueError(
                    "Function not allowed"
                )

            arguments = [

                self._evaluate_node(
                    argument
                )

                for argument in node.args

            ]

            return self.functions[
                function_name
            ](
                *arguments
            )


        # Constants

        if isinstance(
            node,
            ast.Name
        ):

            if node.id in self.functions:

                value = self.functions[
                    node.id
                ]

                if isinstance(
                    value,
                    (int, float)
                ):

                    return value

                raise ValueError(
                    "Function requires arguments"
                )

            raise ValueError(
                "Unknown value"
            )


        raise ValueError(
            "Invalid expression"
        )


# ============================================================
# PREPARE EXPRESSION
# ============================================================

def prepare_expression(expression):

    expression = expression.strip()

    expression = expression.replace(
        " ",
        ""
    )

    # Multiplication

    expression = expression.replace(
        "×",
        "*"
    )

    # Division

    expression = expression.replace(
        "÷",
        "/"
    )

    # Power

    expression = expression.replace(
        "^",
        "**"
    )

    # Pi

    expression = expression.replace(
        "π",
        "pi"
    )

    # Percentage

    expression = re.sub(
        r'(\d+(?:\.\d+)?)%',
        r'(\1/100)',
        expression
    )

    # Factorial

    expression = re.sub(
        r'(\d+(?:\.\d+)?)!',
        r'factorial(\1)',
        expression
    )

    # Square root

    expression = expression.replace(
        "√",
        "sqrt"
    )

    # Number followed by pi/e

    expression = re.sub(
        r'(\d)(pi|e)',
        r'\1*\2',
        expression
    )

    # Parentheses multiplication

    expression = expression.replace(
        ")(",
        ")*("
    )

    expression = re.sub(
        r'(\d)\(',
        r'\1*(',
        expression
    )

    return expression


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ============================================================
# CALCULATE
# ============================================================

@app.route(
    "/calculate",
    methods=["POST"]
)
def calculate():

    data = request.get_json()

    if not data:

        return jsonify({

            "success": False,

            "error": "No data received"

        }), 400


    expression = data.get(
        "expression",
        ""
    )

    mode = data.get(
        "mode",
        "DEG"
    )


    if not expression:

        return jsonify({

            "success": False,

            "error": "Please enter an expression"

        })


    try:

        # Prepare expression

        prepared = prepare_expression(
            expression
        )


        # Create calculator

        calculator = Calculator(
            mode
        )


        # Calculate

        result = calculator.evaluate(
            prepared
        )


        # Remove .0

        if (
            isinstance(result, float)
            and result.is_integer()
        ):

            result = int(result)


        return jsonify({

            "success": True,

            "expression": expression,

            "result": result,

            "mode": mode

        })


    except ZeroDivisionError:

        return jsonify({

            "success": False,

            "error": "Cannot divide by zero"

        })


    except ValueError as error:

        return jsonify({

            "success": False,

            "error": str(error)

        })


    except Exception:

        return jsonify({

            "success": False,

            "error": "Invalid expression"

        })


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )