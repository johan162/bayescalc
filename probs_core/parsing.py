import re
from typing import List, Tuple, Optional


def strip_negation(name: str) -> str:
    name = name.strip()
    if name.startswith("Not(") and name.endswith(")"):
        return name[4:-1].strip()
    if name.startswith("~"):
        inner = name[1:].strip()
        if inner.startswith("(") and inner.endswith(")"):
            return inner[1:-1].strip()
        return inner
    return name


def parse_probability_query_text(content: str):
    """Parse inner content of P(...) into target and optional condition parts.

    Returns a tuple (is_conditional, target_text, condition_text_or_none)
    """
    if "|" in content:
        target_expr, condition_expr = [x.strip() for x in content.split("|", 1)]
        return True, target_expr, condition_expr
    else:
        return False, content.strip(), None


def match_probability_query(query: str) -> Optional[re.Match]:
    # Anchor the pattern to avoid partial matches and allow optional trailing whitespace
    return re.match(r"^P\((.*)\)\s*$", query)


def match_independence_conditional(query: str) -> Optional[re.Match]:
    # Allow optional whitespace around separators and anchor the full string
    return re.match(r"^IsCondIndep\(\s*([^,]+)\s*,\s*([^|]+)\s*\|\s*([^)]+)\s*\)\s*$", query)


def match_independence(query: str) -> Optional[re.Match]:
    # Allow optional whitespace around separators and anchor the full string
    return re.match(r"^IsIndep\(\s*([^,]+)\s*,\s*([^)]+)\s*\)\s*$", query)
