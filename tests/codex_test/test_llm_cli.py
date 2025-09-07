from __future__ import annotations

from pathlib import Path

import codex_test.llm_cli as llm_cli
from codex_test.llm_cli import main, parse_args


def test_llm_cli_parse_args(tmp_path: Path) -> None:
    wf = tmp_path / "wf.json"
    wf.write_text("{}")
    args = parse_args([str(wf), "--model", "x-model"])
    assert args.workflow == wf
    assert args.model == "x-model"


def test_llm_cli_main_prints(monkeypatch, tmp_path: Path, capsys) -> None:
    wf = tmp_path / "wf.json"
    wf.write_text("{}")

    monkeypatch.setattr(llm_cli, "llm_convert_idmc_to_sql", lambda path, model="gpt": "SQL")
    code = main([str(wf), "--model", "x-model"])
    out = capsys.readouterr().out
    assert code == 0
    assert out == "SQL\n"
