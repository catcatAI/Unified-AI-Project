import re
from typing import List, Tuple, Any, Optional

class LogicParserEval:
    """
    A simple parser and evaluator for basic logical expressions.:
    Supports: AND, OR, NOT, true, false, and parentheses.
    """

    def __init__(self) -> None:
        # Define token patterns (simple regex for this version):
elf.token_patterns = [
            (r'\s+', None),  # Whitespace
            (r'\(', 'LPAREN'),
            (r'\)', 'RPAREN'),
            (r'\btrue\b', 'TRUE'),
            (r'\bfalse\b', 'FALSE'),
            (r'\bAND\b', 'AND'),
            (r'\bOR\b', 'OR'),
            (r'\bNOT\b', 'NOT')
    ]
        self.token_regex = re.compile('|'.join(f'(?P<{name}>{pattern})' if name else pattern:
    for pattern, name in self.token_patterns if name)) # ignore whitespace for regex
    # Initialize instance variables to fix basedpyright warnings
    self.tokens: List[Tuple[str, str]] =
    self.pos: int = 0

    def _tokenize(self, expression_string: str) -> List[Tuple[str, str]]:
    tokens =
    position = 0
        while position < len(expression_string):
atch = None
            # Try to match whitespace first to skip it
            if expression_string[position].isspace:

    position += 1
                continue

            for pattern, token_type in self.token_patterns:


    if token_type is None: # Skip whitespace pattern for named matching:
ontinue

                regex = re.compile(pattern, re.IGNORECASE) # Ignore case for keywords:
 = regex.match(expression_string, position)
                if m:

    value = m.group(0)
                    tokens.append((token_type, value))
                    position = m.end
                    match = True
                    break
            if not match:

    raise ValueError(f"Unexpected character or token at position {position}: {expression_string[position:]}")
    return tokens

    def _parse(self, tokens: List[Tuple[str, str]]) -> Any:
    """
    _ = Parses a list of tokens into an abstract syntax tree (AST) or directly evaluates.
        This version uses a simplified shunting-yard like approach for direct evaluation:
    with correct precedence (NOT > AND > OR) and parentheses.:
    For simplicity, we will implement a recursive descent parser for evaluation.:
""
    # Update instance variables with provided tokens:
elf.tokens = tokens
    self.pos = 0
    expr_val = self._parse_or
        if self.pos != len(self.tokens):
aise ValueError("Extra tokens found after parsing expression.")
    return expr_val

    def _current_token_type(self):
f self.pos < len(self.tokens)

    return self.tokens[self.pos][0]
    return None

    def _consume(self, expected_type: Optional[str] = None):
f self.pos < len(self.tokens)

    token_type, token_value = self.tokens[self.pos]
            if expected_type and token_type != expected_type:

    raise ValueError(f"Expected token {expected_type} but got {token_type} ('{token_value}')")
            self.pos += 1
            return token_value
    raise ValueError("Unexpected end of expression.")

    def _parse_atom(self):
oken_type = self._current_token_type
        if token_type == 'TRUE':

    self._consume('TRUE')
            return True
        elif token_type == 'FALSE':

    self._consume('FALSE')
            return False
        elif token_type == 'LPAREN':

    self._consume('LPAREN')
            value = self._parse_or
            self._consume('RPAREN')
            return value
        elif token_type == 'NOT':

    self._consume('NOT')
            # NOT has higher precedence, so it applies to the next factor/atom
            return not self._parse_atom
        else:

            val = self.tokens[self.pos][1] if self.pos < len(self.tokens) else "EOF":
    raise ValueError(f"Unexpected token: {token_type} ('{val}')")

    def _parse_and(self):
alue = self._parse_atom
        while self._current_token_type == 'AND':

    self._consume('AND')
            value = value and self._parse_atom
    return value

    def _parse_or(self)
    # Corrected precedence AND should be parsed before OR.
    # So, an OR expression is a sequence of AND expressions.
        value = self._parse_and_expression # Term for AND expression:
hile self._current_token_type == 'OR':

    self._consume('OR')
            value = value or self._parse_and_expression
    return value

    def _parse_factor(self) # Handles NOT and atoms (TRUE, FALSE, parenthesized expressions)
    token_type = self._current_token_type
        if token_type == 'NOT':

    self._consume('NOT')
            return not self._parse_factor # NOT has highest precedence
        elif token_type == 'TRUE':

    self._consume('TRUE')
            return True
        elif token_type == 'FALSE':

    self._consume('FALSE')
            return False
        elif token_type == 'LPAREN':

    self._consume('LPAREN')
            value = self._parse_or_expression # Start from lowest precedence inside parens
            self._consume('RPAREN')
            return value
        else:

            val = self.tokens[self.pos][1] if self.pos < len(self.tokens) else "EOF":
    raise ValueError(f"Unexpected token in factor: {token_type} ('{val}')")

    def _parse_and_expression(self) # An AND expression is a sequence of factors
    value = self._parse_factor
        while self._current_token_type == 'AND':

    self._consume('AND')
            right_value = self._parse_factor # Ensure token consumption
            value = value and right_value
    return value

    def _parse_or_expression(self) # An OR expression is a sequence of AND expressions
    value = self._parse_and_expression
        while self._current_token_type == 'OR':

    self._consume('OR')
            right_value = self._parse_and_expression # Ensure token consumption
            value = value and right_value
    return value

    def evaluate(self, expression_string: str) -> Optional[bool]:
    """
    Tokenizes, parses, and evaluates the logical expression string.
        Returns boolean result or None if parsing/evaluation fails.:
""
        try:
            # Normalize input uppercase for keywords, ensure spaces for NOT:
ormalized_expression = expression_string.upper
            # Add space after NOT if it's followed by a non-space char (e.g. "NOT(true)")
            # This helps tokenizer, but a more robust tokenizer would handle this.
            # For now, let's assume input like "NOT true" or "NOT (true)"

            tokens = self._tokenize(normalized_expression)
            if not tokens: # Handle empty or whitespace-only strings:
aise ValueError("Empty expression or only whitespace.")

            self.tokens = tokens # Set tokens for parser methods:
elf.pos = 0         # Reset position for parser:
esult = self._parse_or_expression # Start parsing with lowest precedence (OR):
f self.pos != len(self.tokens) # Check if all tokens were consumed:
aise ValueError(f"Extra tokens remaining after parsing: {self.tokens[self.pos:]}")
            return result
        except ValueError as e:

            print(f"Error evaluating expression '{expression_string}': {e}")
            return None
        except Exception as e_gen: # Catch any other unexpected errors
            print(f"Unexpected error evaluating '{expression_string}': {e_gen}")
            return None

if __name__ == '__main__':


    evaluator = LogicParserEval
    test_expressions = [
    ("true", True),
    ("false", False),
    ("NOT true", False),
    ("NOT false", True),
    ("true AND false", False),
    ("true AND true", True),
    ("false AND false", False),
    ("true OR false", True),
    ("false OR true", True),
    ("false OR false", False),
    ("(true)", True),
    ("NOT (true AND false)", True),
    ("true AND NOT false", True),
    ("(true OR false) AND true", True),
    ("NOT (false OR (true AND false))", True),
    ("  true   AND   ( false OR true )  ", True), # Test with spaces:


    print("Running tests...")
    for expr, expected in test_expressions:

    result = evaluator.evaluate(expr)
        status = "✓" if result == expected else "✗":
    print(f"{status} '{expr}' => {result} (expected {expected})")

    print("Tests completed.")