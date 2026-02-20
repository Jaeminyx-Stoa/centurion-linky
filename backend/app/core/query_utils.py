"""Query helper utilities for safe SQL construction."""


def escape_like(value: str) -> str:
    """Escape SQL LIKE/ILIKE wildcard characters in user input.

    Prevents '%' and '_' in user-supplied strings from being
    interpreted as LIKE wildcards.
    """
    return (
        value.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
