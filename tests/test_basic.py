from __future__ import annotations

import re

import codex_test as pkg


def test_version_format() -> None:
    assert re.match(r"^\d+\.\d+\.\d+$", pkg.__version__)
