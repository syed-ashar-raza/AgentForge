import ast
import operator as op
from datetime import UTC

_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Mod: op.mod,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def calculator(expression: str) -> str:
    if not expression or len(expression) > 200:
        raise ValueError("Invalid calculator expression.")

    try:
        tree = ast.parse(expression, mode="eval")
        result = _evaluate(tree.body)
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError) as exc:
        raise ValueError("Invalid arithmetic expression.") from exc

    return str(result)


def _evaluate(node: ast.AST) -> int | float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        if isinstance(node.value, bool):
            raise ValueError("Boolean values are not allowed.")
        return node.value

    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_evaluate(node.operand))

    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](
            _evaluate(node.left),
            _evaluate(node.right),
        )

    raise ValueError("Only arithmetic expressions are allowed.")


def current_datetime() -> str:
    from datetime import datetime

    return datetime.now(UTC).isoformat()


class Tool:
    def __init__(self, name, description, function, dangerous=False):
        self.name = name
        self.description = description
        self.function = function
        self.dangerous = dangerous

    def execute(self, arguments):
        return self.function(**arguments)


def get_builtin_tools():
    return [
        Tool(
            name="calculator",
            description="Calculate a mathematical expression.",
            function=calculator,
        ),
        Tool(
            name="current_datetime",
            description="Return the current UTC date and time.",
            function=current_datetime,
        ),
    ]
