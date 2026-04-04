

"""
HIT137 Assignment 2 - Question 2

HOW THE PROGRAM FLOWS:
  1) LEXER     — scan the string into tokens (numbers, + - * /, brackets, END).
  2) PARSER    — build a small tree (AST) using recursive descent. * and / bind
                 tighter than + and - . unary - and implicit multiply are handled here.
  3) EVALUATOR — walk the tree and compute a float (or None if divide by zero).
  4) OUTPUT    — turn tokens + tree + number into the four lines per expression.

Writes output.txt next to the input file. Result formatting is basic.
"""

from __future__ import annotations

import os
import sys
from typing import Any, List, Optional, Tuple

# Data shapes we use everywhere (no classes, just tuples)
# Token example: ("NUM", "42") or ("OP", "+") or ("LPAREN", "(") ...
# The value is always a string; even END uses ("END", "").
Token = Tuple[str, str]

# AST = abstract syntax tree, also plain tuples:
#   ("num", "3") a number literal (text as read from input)
#   ("neg", child) unary minus; child is another AST node
#   ("bin", op, left, right) binary op is "+", "-", "*", or "/"; left/right are AST nodes
Ast = Tuple[Any, ...]


# LEXER — turn one line of text into a list of tokens



def _read_number(line: str, i: int) -> Optional[Tuple[str, int]]:
    """
    Try to read one numeric literal starting at position i in line.

    Supports:
      - 123, 3.14
      - .5   (leading dot, digits after)

    Returns (string_of_number, index_after_number), or None if there is no number here.
    The underscore name means "internal helper" — only tokenize_line is supposed to call it.
    """
    n = len(line)
    if i >= n:
        return None
    start = i

    # Branch 1: number starts with "."  --  we need at least one digit after the dot
    if line[i] == ".":
        i += 1
        if i >= n or not line[i].isdigit():
            return None
        while i < n and line[i].isdigit():
            i += 1
        return line[start:i], i

    # Branch 2: normal case — starts with a digit, optional fractional part
    if not line[i].isdigit():
        return None

    while i < n and line[i].isdigit():
        i += 1
    if i < n and line[i] == ".":
        i += 1
        while i < n and line[i].isdigit():
            i += 1

    return line[start:i], i


def tokenize_line(line: str) -> Optional[List[Token]]:
    """
    Walk the whole expression left-to-right and collect tokens.

    Spaces/tabs are skipped (they are not tokens).
    If we hit any character that is not part of a valid token, return None
    → the caller will treat the whole line as ERROR (e.g. 3 @ 5).
    """
    s = line.rstrip("\r\n")  # strip newline only keep spaces inside the expression
    tokens: List[Token] = []
    i = 0

    while i < len(s):
        ch = s[i]

        # Whitespace separates tokens but is not stored
        if ch in " \t":
            i += 1
            continue

        # Try to read a number starting at i (handles 3, 3.5, .5, ...)
        num = _read_number(s, i)
        if num is not None:
            txt, i = num
            if txt == ".":
                return None  # lone dot is invalid
            tokens.append(("NUM", txt))
            continue

        # Single-character operators
        if ch in "+-*/":
            tokens.append(("OP", ch))
            i += 1
            continue

        if ch == "(":
            tokens.append(("LPAREN", "("))
            i += 1
            continue

        if ch == ")":
            tokens.append(("RPAREN", ")"))
            i += 1
            continue

        # Anything else (@, letters, etc.) is illegal for this assignment
        return None

    # Sentinel so the parser knows it reached the end of the line
    tokens.append(("END", ""))
    return tokens


def tokens_to_string(tokens: Optional[List[Token]]) -> str:
    """
    Build the assignment's "Tokens: ..." line, e.g.
    [NUM:3] [OP:+] [NUM:5] [END]
    """
    if tokens is None:
        return "ERROR"
    parts: List[str] = []
    for kind, val in tokens:
        if kind == "NUM":
            parts.append(f"[NUM:{val}]")
        elif kind == "OP":
            parts.append(f"[OP:{val}]")
        elif kind == "LPAREN":
            parts.append("[LPAREN:(]")
        elif kind == "RPAREN":
            parts.append("[RPAREN:)]")
        elif kind == "END":
            parts.append("[END]")
        else:
            parts.append(f"[{kind}:{val}]")
    return " ".join(parts)


def tree_to_string(node: Ast) -> str:
    """
    Turn an AST node into the assignment's tree format, e.g.
      (+ 3 5)     or    (neg (+ 3 4))

    This calls itself on children — that is normal for trees (recursive).
    """
    if node[0] == "num":
        return str(node[1])
    if node[0] == "neg":
        return f"(neg {tree_to_string(node[1])})"
    if node[0] == "bin":
        _, op, left, right = node
        return f"({op} {tree_to_string(left)} {tree_to_string(right)})"
    return "ERROR"


# PARSER — recursive descent
# Precedence (what gets grouped first):
#   LOWEST  +  -
#   HIGHER  *  /
#   unary - binds to the thing right after it (e.g. -5, --5, -(3+4))
# We also treat "2(3)" as multiply in the TREE only — tokens stay [NUM:2] [LPAREN:...


def parse_expr(tokens: List[Token], pos: int) -> Optional[Tuple[Ast, int]]:
    """
    Grammar:  expr → term (('+'|'-') term)*

    So we read a term, then while the next token is + or - we consume it and another term.
    Example: 1 - 2 + 3  →  ((1 - 2) + 3)  left-associative.
    """
    got = parse_term(tokens, pos)
    if got is None:
        return None
    node, pos = got
    while pos < len(tokens) and tokens[pos][0] == "OP" and tokens[pos][1] in "+-":
        op = tokens[pos][1]
        pos += 1
        got2 = parse_term(tokens, pos)
        if got2 is None:
            return None
        right, pos = got2
        node = ("bin", op, node, right)
    return node, pos


def parse_term(tokens: List[Token], pos: int) -> Optional[Tuple[Ast, int]]:
    """
    Grammar:  term → factor (('*'|'/') factor)*

    * and / sit here so they bind tighter than + and - in parse_expr above.
    """
    got = parse_factor(tokens, pos)
    if got is None:
        return None
    node, pos = got
    while pos < len(tokens) and tokens[pos][0] == "OP" and tokens[pos][1] in "*/":
        op = tokens[pos][1]
        pos += 1
        got2 = parse_factor(tokens, pos)
        if got2 is None:
            return None
        right, pos = got2
        node = ("bin", op, node, right)
    return node, pos


def parse_factor(tokens: List[Token], pos: int) -> Optional[Tuple[Ast, int]]:
    """
    Grammar idea:
      factor → '-' factor          (unary minus, chains: --5)
             | primary (implicit '*' primary)*

    Unary '+' at this position is illegal (assignment says so) → we return None.

    Implicit multiply: after we finish one primary, if the next token starts another
    primary ( '(' or a number ) without an explicit * in between, we build (* left right)
    in the tree. Example: 2(3+4)  →  (* 2 (+ 3 4)).
    """
    if pos >= len(tokens):
        return None

    kind, val = tokens[pos]

    # Unary + where a factor must start -- parse error
    if kind == "OP" and val == "+":
        return None

    # Unary minus: eat '-', parse another factor (recursion handles --5)
    if kind == "OP" and val == "-":
        pos += 1
        got = parse_factor(tokens, pos)
        if got is None:
            return None
        child, pos = got
        return ("neg", child), pos

    # Normal start: number or '(' expression ')'
    got = parse_primary(tokens, pos)
    if got is None:
        return None
    node, pos = got

    # Implicit multiplication loop
    while pos < len(tokens):
        nk = tokens[pos][0]
        if nk == "LPAREN" or nk == "NUM":
            got2 = parse_primary(tokens, pos)
            if got2 is None:
                return None
            rhs, pos = got2
            node = ("bin", "*", node, rhs)
        else:
            break

    return node, pos


def parse_primary(tokens: List[Token], pos: int) -> Optional[Tuple[Ast, int]]:
    """
    Grammar:  primary → NUM | '(' expr ')'

    The '(' case calls parse_expr again — that is the "recursion" in recursive descent:
    parenthesised sub-expression is parsed with the same rules as the whole line.
    """
    if pos >= len(tokens):
        return None
    kind, val = tokens[pos]

    if kind == "NUM":
        return ("num", val), pos + 1

    if kind == "LPAREN":
        pos += 1
        got = parse_expr(tokens, pos)  # back to top level rule for the inside
        if got is None:
            return None
        inner, pos = got
        if pos >= len(tokens) or tokens[pos][0] != "RPAREN":
            return None  # missing closing bracket
        pos += 1
        return inner, pos

    return None


def parse_tokens(tokens: Optional[List[Token]]) -> Optional[Ast]:
    """
    Entry point for parsing: whole line must become one expr, then END.

    If anything failed inside parse_expr, or there is junk after a valid expr, return None.
    """
    if tokens is None:
        return None
    got = parse_expr(tokens, 0)
    if got is None:
        return None
    node, pos = got
    if pos >= len(tokens) or tokens[pos][0] != "END":
        return None
    return node



# EVALUATOR — compute the numeric value from the AST (post-order / recursive)


def eval_ast(node: Ast) -> Optional[float]:
    """
    Walk the tree. Returns None on divide by zero (caller prints Result: ERROR).

    Structure matches parse_* : same cases as tree node types.
    """
    if node[0] == "num":
        return float(node[1])

    if node[0] == "neg":
        v = eval_ast(node[1])
        if v is None:
            return None
        return -v

    if node[0] == "bin":
        _, op, left, right = node
        a = eval_ast(left)
        b = eval_ast(right)
        if a is None or b is None:
            return None
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            if b == 0.0:
                return None
            return a / b

    return None


def format_result_v1(value: Optional[float]) -> str:
    """
    Version 1: good enough for whole numbers + ERROR.
    Fractions print with lots of digits — version 2 fixes that (4 decimal places).
    """
    if value is None:
        return "ERROR"
    r = round(value, 10)
    if abs(r - round(r)) < 1e-9:
        return str(int(round(r)))
    return str(value)



# MAIN — everything together for each line and write output.txt


def main() -> None:
    # Input file: from command line, or default sample next to this script
    if len(sys.argv) >= 2:
        input_path = sys.argv[1]
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        input_path = os.path.join(here, "sample_input.txt")

    input_path = os.path.abspath(input_path)
    folder = os.path.dirname(input_path)
    out_path = os.path.join(folder, "output.txt")

    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    blocks: List[str] = []
    first_block = True

    for line in lines:
        # Skip empty lines in the input file (nothing to evaluate)
        if line.strip() == "":
            continue

        display = line.rstrip("\r\n")

        # Blank line between expression blocks in the output (assignment format)
        if not first_block:
            blocks.append("")
        first_block = False

        # Path A: lexer failed (bad character) - everything ERROR
        tokens = tokenize_line(line)
        if tokens is None:
            blocks.append(f"Input: {display}")
            blocks.append("Tree: ERROR")
            blocks.append("Tokens: ERROR")
            blocks.append("Result: ERROR")
            continue

        #Path B: lexer OK, parser failed -- tree ERROR, tokens still printed
        tree = parse_tokens(tokens)
        tok_s = tokens_to_string(tokens)
        if tree is None:
            blocks.append(f"Input: {display}")
            blocks.append("Tree: ERROR")
            blocks.append(f"Tokens: {tok_s}")
            blocks.append("Result: ERROR")
            continue

        #Path C: parse OK -- maybe divide by zero still gives Result ERROR
        tree_s = tree_to_string(tree)
        val = eval_ast(tree)
        res_line = format_result_v1(val)

        blocks.append(f"Input: {display}")
        blocks.append(f"Tree: {tree_s}")
        blocks.append(f"Tokens: {tok_s}")
        blocks.append(f"Result: {res_line}")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(blocks))
        if blocks:
            f.write("\n")

    print(f"Wrote output.txt next to: {input_path}")


# Only run main when this file is executed directly (not when imported)
if __name__ == "__main__":
    main()
