"""Unit tests for stack_evaluator.py  (run: python -m unittest -v)"""
import os
import tempfile
import unittest

from stack_evaluator import (
    Stack, ExpressionError, evaluate_expression, process_lines, process_file,
)


class TestStack(unittest.TestCase):
    def test_push_pop_order_is_lifo(self):
        s = Stack()
        for x in (1, 2, 3):
            s.push(x)
        self.assertEqual([s.pop(), s.pop(), s.pop()], [3, 2, 1])

    def test_peek_does_not_remove(self):
        s = Stack()
        s.push("a")
        self.assertEqual(s.peek(), "a")
        self.assertEqual(s.size(), 1)

    def test_pop_empty_raises(self):
        with self.assertRaises(IndexError):
            Stack().pop()

    def test_peek_empty_raises(self):
        with self.assertRaises(IndexError):
            Stack().peek()

    def test_is_empty(self):
        s = Stack()
        self.assertTrue(s.is_empty())
        s.push(1)
        self.assertFalse(s.is_empty())


class TestEvaluation(unittest.TestCase):
    def check(self, expr, expected):
        self.assertEqual(evaluate_expression(expr), expected)

    def test_assignment_examples(self):
        self.check("3 + 5 * 2", 13)
        self.check("(8 / 4) + 7 * 2", 16)
        self.check("10 - (2 + 3) * 4", -10)

    def test_precedence(self):
        self.check("2 + 3 * 4", 14)
        self.check("2 * 3 + 4", 10)

    def test_left_associativity(self):
        self.check("10 - 4 - 3", 3)
        self.check("100 / 10 / 5", 2)

    def test_parentheses_and_nesting(self):
        self.check("(2 + 3) * 4", 20)
        self.check("((1 + 2) * (3 + 4))", 21)
        self.check("2 * (3 + (4 - 1))", 12)

    def test_decimals_and_float_result(self):
        self.check("7 / 2", 3.5)
        self.check("1.5 + 2.5", 4)
        self.check("0.1 + 0.2", 0.3)

    def test_unary_minus(self):
        self.check("-5 + 3", -2)
        self.check("3 * -2", -6)
        self.check("-(2 + 3)", -5)
        self.check("2 - -3", 5)

    def test_no_spaces(self):
        self.check("3+5*2", 13)

    def test_single_number(self):
        self.check("42", 42)

    def test_division_by_zero(self):
        with self.assertRaises(ExpressionError):
            evaluate_expression("5 / 0")

    def test_malformed_expressions(self):
        for bad in ["", "3 +", "* 3", "(3 + 4", "3 + 4)", "3 4", "()", "3 + * 4", "2 $ 3", "3 (4)"]:
            with self.subTest(expr=bad):
                with self.assertRaises(ExpressionError):
                    evaluate_expression(bad)


class TestFileProcessing(unittest.TestCase):
    def test_format_preserved(self):
        lines = ["3 + 5 * 2\n", "-----\n", "(8 / 4) + 7 * 2\n", "-----\n", "10 - (2 + 3) * 4\n"]
        self.assertEqual(process_lines(lines), ["13", "-----", "16", "-----", "-10"])

    def test_error_line_does_not_stop_processing(self):
        out = process_lines(["1 / 0\n", "-----\n", "2 + 2\n"])
        self.assertEqual(out, ["Error: Division by zero", "-----", "4"])

    def test_end_to_end_files(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = os.path.join(d, "in.txt"), os.path.join(d, "out.txt")
            with open(src, "w") as f:
                f.write("3 + 5 * 2\n-----\n10 - (2 + 3) * 4\n")
            process_file(src, dst)
            with open(dst) as f:
                self.assertEqual(f.read(), "13\n-----\n-10\n")


if __name__ == "__main__":
    unittest.main()

