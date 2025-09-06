from __future__ import annotations

from pathlib import Path

import codex_test as pkg


SIMPLE_IDMC = {
    "mappings": [
        {
            "name": "m_simple",
            "source": {"name": "SRC_TABLE", "fields": ["id", "name"]},
            "target": {"name": "TGT_TABLE", "fields": ["id", "name"]},
        }
    ]
}


def test_count_mappings_idmc(tmp_path: Path) -> None:
    wf = tmp_path / "wf.json"
    wf.write_text(__import__("json").dumps(SIMPLE_IDMC))
    assert pkg.count_mappings(wf) == 1


def test_convert_mappings_to_sql_idmc(tmp_path: Path) -> None:
    wf = tmp_path / "wf.json"
    wf.write_text(__import__("json").dumps(SIMPLE_IDMC))
    out = pkg.convert_mappings_to_sql(wf)
    assert set(out.keys()) == {"m_simple"}
    sql = out["m_simple"]
    assert "INSERT INTO TGT_TABLE (id, name)" in sql
    assert "SELECT id, name FROM SRC_TABLE;" in sql

