from __future__ import annotations

from pathlib import Path

import codex_test.agents_cli as agents_cli


def test_agents_cli_parse_and_main(monkeypatch, tmp_path: Path, capsys) -> None:
    wf = tmp_path / "wf.json"
    wf.write_text("{}", encoding="utf-8")

    # Stub the conversion function
    monkeypatch.setattr(
        agents_cli, "agent_convert_idmc_to_sql", lambda p, model="m": "SQL-AGENT"
    )
    code = agents_cli.main([str(wf), "--model", "m-test"])
    assert code == 0
    out = capsys.readouterr().out
    assert out == "SQL-AGENT\n"
