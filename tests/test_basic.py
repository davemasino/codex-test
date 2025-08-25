from __future__ import annotations

import re

import codex_test as pkg


def test_version_format():
    assert re.match(r"^\d+\.\d+\.\d+$", pkg.__version__)


def test_greet_default():
    assert pkg.greet() == "Hello, world!"


def test_greet_custom():
    assert pkg.greet("Alice") == "Hello, Alice!"

