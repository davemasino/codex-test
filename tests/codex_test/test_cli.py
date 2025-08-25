from __future__ import annotations

import re
import sys

import pytest

import codex_test as pkg
from codex_test.cli import main, parse_args


def test_parse_args_default():
    args = parse_args([])
    assert args.name == "world"


def test_parse_args_custom():
    args = parse_args(["Alice"])
    assert args.name == "Alice"


def test_main_default_prints_and_returns_zero(capsys: pytest.CaptureFixture[str]):
    code = main([])
    captured = capsys.readouterr()
    assert code == 0
    assert captured.out == "Hello, world!\n"


def test_main_custom_prints_and_returns_zero(capsys: pytest.CaptureFixture[str]):
    code = main(["Alice"])
    captured = capsys.readouterr()
    assert code == 0
    assert captured.out == "Hello, Alice!\n"


def test_version_flag_prints_and_exits(capsys: pytest.CaptureFixture[str]):
    # argparse's version action prints to stdout and exits with code 0
    with pytest.raises(SystemExit) as exc:
        parse_args(["--version"])  # triggers SystemExit
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert out == f"codex-test {pkg.__version__}\n"

