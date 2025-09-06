from __future__ import annotations

from pathlib import Path

import pytest

import codex_test as pkg
from codex_test.cli import main, parse_args


SIMPLE_MAPPING = """<?xml version='1.0' encoding='UTF-8'?>
<REPOSITORY>
  <FOLDER>
    <MAPPING NAME='m_simple'>
      <TRANSFORMATION NAME='SRC_TABLE' TYPE='Source Definition'>
        <FIELD NAME='id'/>
        <FIELD NAME='name'/>
      </TRANSFORMATION>
      <TRANSFORMATION NAME='TGT_TABLE' TYPE='Target Definition'>
        <FIELD NAME='id'/>
        <FIELD NAME='name'/>
      </TRANSFORMATION>
    </MAPPING>
  </FOLDER>
</REPOSITORY>
"""


def test_parse_args_accepts_workflow(tmp_path: Path) -> None:
    wf = tmp_path / "wf.xml"
    wf.write_text(SIMPLE_MAPPING)
    args = parse_args([str(wf)])
    assert args.workflow == wf
    assert args.output_dir is None


def test_main_prints_sql(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    wf = tmp_path / "wf.xml"
    wf.write_text(SIMPLE_MAPPING)
    code = main([str(wf)])
    captured = capsys.readouterr().out
    assert code == 0
    assert "INSERT INTO TGT_TABLE (id, name)" in captured
    assert "SELECT id, name FROM SRC_TABLE;" in captured


def test_version_flag_prints_and_exits(capsys: pytest.CaptureFixture[str]):
    # argparse's version action prints to stdout and exits with code 0
    with pytest.raises(SystemExit) as exc:
        parse_args(["--version"])  # triggers SystemExit
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert out == f"codex-test {pkg.__version__}\n"
