"""Top-level package for codex_test.

Provides a small example API to validate tests and CLI wiring.
"""

from __future__ import annotations

__all__ = [
    "__version__",
    "greet",
]

__version__ = "0.1.0"


def greet(name: str = "world") -> str:
    """Return a friendly greeting.

    Examples
    --------
    >>> greet()
    'Hello, world!'
    >>> greet("Alice")
    'Hello, Alice!'
    """

    return f"Hello, {name}!"

