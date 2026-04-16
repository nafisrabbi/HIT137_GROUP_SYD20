"""
HIT137 Assignment 2 – Question 2
Mathematical Expression Evaluator

This program reads mathematical expressions from a text file, one expression per line,
tokenises each expression, parses it using recursive descent parsing, evaluates the
result, and writes the output to a file in the required format.

Workflow:
- Reads expressions from an input text file
- Tokenises each expression into NUM, OP, LPAREN, RPAREN, and END tokens
- Parses each expression according to operator precedence rules
- Builds an expression tree representation
- Evaluates the expression recursively
- Writes Input, Tree, Tokens, and Result to output.txt

Supported Features:
- Binary operators: +, -, *, /
- Parentheses with nested expressions
- Unary negation, such as -5, --5, and -(3+4)
- Implicit multiplication, such as 2(3+4) or (2+1)(3+1)

Parsing Design:
The program uses recursive descent parsing with separate functions for each
precedence level:
- parse_expression() handles addition and subtraction
- parse_term() handles multiplication, division, and implicit multiplication
- parse_factor() handles unary negation
- parse_primary() handles numbers and parenthesised expressions

Expression Tree:
- Binary operations are represented as (op left right)
- Unary negation is represented as (neg operand)
- Numeric values form the leaf nodes of the tree

Evaluation and Error Handling:
The tree is evaluated recursively. Invalid characters, syntax errors, division by zero,
unsupported unary plus, and malformed expressions produce ERROR for that expression.

Output Format:
For each expression, the program writes exactly four lines:
- Input: original expression
- Tree: parsed expression tree or ERROR
- Tokens: token list or ERROR
- Result: evaluated result or ERROR
"""

import os

class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"[{self.type}:{self.value}]" if self.value is not None else f"[{self.type}]"

# Tokenizer

def tokenize(expression):
    tokens = []
    i = 0
    while i < len(expression):
        ch = expression[i]

        if ch.isdigit() or ch == '.':
            num = ch
            i += 1
            while i < len(expression) and (expression[i].isdigit() or expression[i] == '.'):
                num += expression[i]
                i += 1
            tokens.append(Token("NUM", num))
            continue

        elif ch in '+-*/':
            tokens.append(Token("OP", ch))
        elif ch == '(':
            tokens.append(Token("LPAREN", ch))
        elif ch == ')':
            tokens.append(Token("RPAREN", ch))
        elif ch.isspace():
            pass
        else:
            raise ValueError("Invalid character")
        i += 1

    tokens.append(Token("END"))
    return tokens

# Parser (Recursive Descent)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def eat(self, type_):
        if self.current().type == type_:
            self.pos += 1
        else:
            raise ValueError("Unexpected token")

    def parse(self):
        node = self.expr()
        if self.current().type != "END":
            raise ValueError("Extra input")
        return node

    def expr(self):
        node = self.term()
        while self.current().type == "OP" and self.current().value in '+-':
            op = self.current().value
            self.eat("OP")
            right = self.term()
            node = (op, node, right)
        return node

    def term(self):
        node = self.factor()
        while self.current().type == "OP" and self.current().value in '*/':
            op = self.current().value
            self.eat("OP")
            right = self.factor()
            node = (op, node, right)
        return node

    def factor(self):
        token = self.current()

        if token.type == "OP" and token.value == '-':
            self.eat("OP")
            return ('neg', self.factor())

        elif token.type == "NUM":
            self.eat("NUM")
            return float(token.value)

        elif token.type == "LPAREN":
            self.eat("LPAREN")
            node = self.expr()
            self.eat("RPAREN")
            return node

        else:
            raise ValueError("Invalid syntax")

# Tree to string

def tree_to_str(node):
    if isinstance(node, float):
        return str(int(node)) if node.is_integer() else str(node)
    if node[0] == 'neg':
        return f"(- {tree_to_str(node[1])})"
    return f"({node[0]} {tree_to_str(node[1])} {tree_to_str(node[2])})"

# Evaluator

def eval_tree(node):
    if isinstance(node, float):
        return node

    if node[0] == 'neg':
        return -eval_tree(node[1])

    left = eval_tree(node[1])
    right = eval_tree(node[2])

    if node[0] == '+':
        return left + right
    elif node[0] == '-':
        return left - right
    elif node[0] == '*':
        return left * right
    elif node[0] == '/':
        if right == 0:
            raise ZeroDivisionError
        return left / right

# Formatting result

def format_result(val):
    if float(val).is_integer():
        return int(val)
    return round(val, 4)

# Main function

def evaluate_file(input_path: str):
    results = []
    output_lines = []

    with open(input_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        expr = line.strip()

        try:
            tokens = tokenize(expr)
            token_str = ' '.join(str(t) for t in tokens)

            parser = Parser(tokens)
            tree = parser.parse()
            tree_str = tree_to_str(tree)

            result_val = eval_tree(tree)
            formatted = format_result(result_val)

            results.append({
                "input": expr,
                "tree": tree_str,
                "tokens": token_str,
                "result": result_val
            })

            output_lines.append(f"Input: {expr}")
            output_lines.append(f"Tree: {tree_str}")
            output_lines.append(f"Tokens: {token_str}")
            output_lines.append(f"Result: {formatted}")
            output_lines.append("")

        except Exception:
            results.append({
                "input": expr,
                "tree": "ERROR",
                "tokens": "ERROR",
                "result": "ERROR"
            })

            output_lines.append(f"Input: {expr}")
            output_lines.append("Tree: ERROR")
            output_lines.append("Tokens: ERROR")
            output_lines.append("Result: ERROR")
            output_lines.append("")

    output_path = os.path.join(os.path.dirname(input_path), "output_2.txt")
    with open(output_path, 'w') as f:
        f.write('\n'.join(output_lines))

    return results

# Example run
if __name__ == "__main__":
    evaluate_file("Sample_input_2.txt")
