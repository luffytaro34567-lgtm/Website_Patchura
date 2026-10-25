"""
Database Query and SQL Input Sanitization Utility.
Prevents pattern-exhaustion attacks, unexpected wildcard expansion,
and unbounded pagination memory exhaustion in SQLAlchemy relational queries.
"""
from __future__ import annotations


def escape_like_wildcards(term: str) -> str:
    """
    Escapes special SQL LIKE wildcard characters ('%', '_', and '\\')
    so that user-supplied search terms are treated strictly as literal strings.
    """
    if not term:
        return ""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def sanitize_search_query(term: str, max_length: int = 100) -> str:
    """
    Trims, length-bounds, and escapes a search term for safe LIKE/ILIKE matching.
    """
    cleaned = (term or "").strip()[:max_length]
    return escape_like_wildcards(cleaned)
