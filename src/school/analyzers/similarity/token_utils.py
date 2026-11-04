from __future__ import annotations

import tokenize
import io
from typing import Iterator

EXCLUDED_TOKEN_TYPES = {
    tokenize.COMMENT,
    tokenize.NEWLINE,
    tokenize.NL,
    tokenize.INDENT,
    tokenize.DEDENT,
    tokenize.ENDMARKER,
    tokenize.ENCODING,
}

def extract_tokens(code: str) -> list[str]:
    if not code or not code.strip():
        return []
    
    tokens = []
    try:
        for tok_type, tok_string, _, _, _ in tokenize.generate_tokens(io.StringIO(code).readline):
            if tok_type in EXCLUDED_TOKEN_TYPES:
                continue
  
            if not tok_string.strip():
                continue
            tokens.append(tok_string)
    except tokenize.TokenError:
        return []
    
    return tokens

def ngrams(tokens: list[str], n: int = 3) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return set(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))

def jaccard_similarity(set_a: set, set_b: set) -> float | None:
    if not set_a and not set_b:
        return None
    
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    
    if union == 0:
        return None
    
    return intersection / union

def extract_template_tokens(template_code: str) -> set[str]:
    return set(extract_tokens(template_code))
