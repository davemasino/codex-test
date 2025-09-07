from __future__ import annotations

from pathlib import Path

import pytest

import codex_test as pkg
import codex_test.cli as cli
from codex_test.cli import main, parse_args


def test_parse_args_accepts_workflow(tmp_path: Path) -> None:
    wf = tmp_path / "wf.json"
    wf.write_text("{}")
    args = parse_args([str(wf)])
    assert args.workflow == wf
    assert args.output_dir is None


def test_main_prints_sql(
    monkeypatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    wf = tmp_path / "wf.json"
    wf.write_text("{}")
    monkeypatch.setattr(cli, "llm_convert_idmc_to_sql", lambda p: "SQL")
    code = main([str(wf)])
    captured = capsys.readouterr().out
    assert code == 0
    assert captured == "SQL\n"


def test_version_flag_prints_and_exits(capsys: pytest.CaptureFixture[str]):
    # argparse's version action prints to stdout and exits with code 0
    with pytest.raises(SystemExit) as exc:
        parse_args(["--version"])  # triggers SystemExit
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert out == f"codex-test {pkg.__version__}\n"
