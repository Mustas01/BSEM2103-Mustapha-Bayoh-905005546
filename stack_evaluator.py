"""
DCOMP320 - Data Structures and Algorithms
Assignment: Stacks Implementation

Reads mathematical expressions from input.txt, evaluates each one using
stacks, and writes the results to output.txt in the same layout
(results replace expressions, separator lines are preserved).

Usage:
    python stack_evaluator.py [input_file] [output_file]
Defaults: input.txt -> output.txt
"""

import re
import sys


# --------------------------------------------------------------------------
# 1. Stack class
# --------------------------------------------------------------------------
class Stack:
    """A simple LIFO stack backed by a Python list."""

    def __init__(self):
        self._items = []

    def push(self, item):
        """Place an item on top of the stack. O(1)."""
        self._items.append(item)

    def pop(self):
        """Remove and return the top item. Raises IndexError if empty. O(1)."""
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self):
        """Return the top item without removing it. Raises IndexError if empty."""
        if self.is_empty():
            raise IndexError("peek at empty stack")
        return self._items[-1]

    def is_empty(self):
        return len(self._items) == 0

    def size(self):
        return len(self._items)

    def __len__(self):
        return len(self._items)

    def __repr__(self):
        return f"Stack({self._items})"


# --------------------------------------------------------------------------
# 2. Expression parsing and evaluation
# --------------------------------------------------------------------------
class ExpressionError(Exception):
    """Raised when an expression is malformed or cannot be evaluated."""


BINARY_OPERATORS = {"+", "-", "*", "/"}
UNARY_MINUS = "neg"  # internal symbol for unary minus (e.g. -5, 3 * -2)

PRECEDENCE = {"+": 1, "-": 1, "*": 2, "/": 2, UNARY_MINUS: 3}

NUMBER_PATTERN = re.compile(r"\d+\.\d*|\.\d+|\d+")


def tokenize(expression):
    """
    Convert an expression string into a list of tokens.
    Numbers become floats; operators and parentheses stay as strings.
    Unary minus is converted to the internal UNARY_MINUS token; unary plus
    is ignored.
    """
    tokens = []
    i = 0
    n = len(expression)
    while i < n:
        ch = expression[i]
        if ch.isspace():
            i += 1
            continue

        match = NUMBER_PATTERN.match(expression, i)
        if match:
            tokens.append(float(match.group()))
            i = match.end()
            continue

        if ch in "+-*/()":
            # A +/- is "unary" at the start, after an operator, or after "(".
            previous = tokens[-1] if tokens else None
            is_unary_position = (
                previous is None
                or previous == "("
                or (isinstance(previous, str) and previous in PRECEDENCE)
            )
            if ch == "-" and is_unary_position:
                tokens.append(UNARY_MINUS)
            elif ch == "+" and is_unary_position:
                pass  # unary plus has no effect
            else:
                tokens.append(ch)
            i += 1
            continue

        raise ExpressionError(f"Invalid character '{ch}'")
    return tokens


def apply_operator(operator_stack, value_stack):
    """Pop one operator and its operand(s) and push the result."""
    operator = operator_stack.pop()

    if operator == UNARY_MINUS:
        if value_stack.is_empty():
            raise ExpressionError("Missing operand")
        value_stack.push(-value_stack.pop())
        return

    if len(value_stack) < 2:
        raise ExpressionError("Missing operand")
    right = value_stack.pop()
    left = value_stack.pop()

    if operator == "+":
        value_stack.push(left + right)
    elif operator == "-":
        value_stack.push(left - right)
    elif operator == "*":
        value_stack.push(left * right)
    elif operator == "/":
        if right == 0:
            raise ExpressionError("Division by zero")
        value_stack.push(left / right)


def evaluate_expression(expression):
    """
    Evaluate an infix expression using two stacks:
      - value_stack    holds operands (numbers / partial results)
      - operator_stack holds operators and '(' markers
    Handles + - * /, parentheses, precedence, left-to-right associativity,
    decimals and unary minus. Returns an int when the result is whole,
    otherwise a float rounded to 6 decimal places.
    """
    tokens = tokenize(expression)
    if not tokens:
        raise ExpressionError("Empty expression")

    value_stack = Stack()
    operator_stack = Stack()
    expect_operand = True  # used to catch things like "3 4" or "3 + * 4"

    for token in tokens:
        if isinstance(token, float):
            if not expect_operand:
                raise ExpressionError("Missing operator")
            value_stack.push(token)
            expect_operand = False

        elif token == "(":
            if not expect_operand:
                raise ExpressionError("Missing operator before '('")
            operator_stack.push(token)

        elif token == ")":
            if expect_operand:
                raise ExpressionError("Missing operand before ')'")
            while not operator_stack.is_empty() and operator_stack.peek() != "(":
                apply_operator(operator_stack, value_stack)
            if operator_stack.is_empty():
                raise ExpressionError("Mismatched parentheses")
            operator_stack.pop()  # discard the '('

        elif token == UNARY_MINUS:
            if not expect_operand:
                raise ExpressionError("Unexpected unary minus")
            # Right-associative prefix operator: push without popping others.
            operator_stack.push(token)

        else:  # binary operator
            if expect_operand:
                raise ExpressionError(f"Unexpected operator '{token}'")
            while (
                not operator_stack.is_empty()
                and operator_stack.peek() != "("
                and PRECEDENCE[operator_stack.peek()] >= PRECEDENCE[token]
            ):
                apply_operator(operator_stack, value_stack)
            operator_stack.push(token)
            expect_operand = True

    if expect_operand:
        raise ExpressionError("Expression ends unexpectedly")

    while not operator_stack.is_empty():
        if operator_stack.peek() == "(":
            raise ExpressionError("Mismatched parentheses")
        apply_operator(operator_stack, value_stack)

    result = value_stack.pop()
    return format_number(result)


def format_number(value):
    """Return an int for whole numbers, else a float rounded to 6 places."""
    value = round(value, 6)
    if value == int(value):
        return int(value)
    return value


# --------------------------------------------------------------------------
# 3. File processing
# --------------------------------------------------------------------------
SEPARATOR_PATTERN = re.compile(r"^\s*([-=_~#])\1{2,}\s*$")


def is_separator(line):
    """A separator is a line made only of 3+ repeated '-', '=', '_', '~' or '#'."""
    return bool(SEPARATOR_PATTERN.match(line))


def process_lines(lines):
    """
    Evaluate every expression line and return the output lines.
    Separator lines are kept exactly as they appear; blank lines are kept;
    invalid expressions produce 'Error: <reason>' instead of crashing.
    """
    output_lines = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if line.strip() == "":
            output_lines.append("")
        elif is_separator(line):
            output_lines.append(line.strip())
        else:
            try:
                output_lines.append(str(evaluate_expression(line)))
            except ExpressionError as error:
                output_lines.append(f"Error: {error}")
    return output_lines


def process_file(input_path, output_path):
    """Read expressions from input_path and write results to output_path."""
    with open(input_path, "r", encoding="utf-8") as infile:
        lines = infile.readlines()
    results = process_lines(lines)
    with open(output_path, "w", encoding="utf-8") as outfile:
        outfile.write("\n".join(results) + "\n")
    return results


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else "input.txt"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output.txt"
    try:
        results = process_file(input_path, output_path)
    except FileNotFoundError:
        print(f"Error: could not find '{input_path}'.")
        sys.exit(1)
    print(f"Processed '{input_path}' -> '{output_path}' ({len(results)} lines written).")


if __name__ == "__main__":
    main()
