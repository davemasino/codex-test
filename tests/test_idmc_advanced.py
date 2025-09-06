from __future__ import annotations

import json
from pathlib import Path

import codex_test as pkg


def test_idmc_multiple_sources_join(tmp_path: Path) -> None:
    data = {
        "mappings": [
            {
                "name": "m_join",
                "sources": [
                    {"name": "SRC_A", "fields": ["id", "name"]},
                    {"name": "SRC_B", "fields": ["id", "amount"]},
                ],
                "target": {"name": "TGT", "fields": ["id", "name", "amount"]},
            }
        ]
    }
    wf = tmp_path / "wf.json"
    wf.write_text(json.dumps(data))
    out = pkg.convert_mappings_to_sql(wf)
    sql = out["m_join"]
    assert "JOIN SRC_B USING (id)" in sql
    # id is unqualified due to USING; name and amount are qualified
    assert "SELECT id, SRC_A.name, SRC_B.amount" in sql
    assert "INSERT INTO TGT (id, name, amount)" in sql


def test_idmc_multiple_sources_cross_join(tmp_path: Path) -> None:
    data = {
        "mappings": [
            {
                "name": "m_cross",
                "sources": [
                    {"name": "A", "fields": ["a_id", "val_a"]},
                    {"name": "B", "fields": ["b_id", "val_b"]},
                ],
                "target": {"name": "TGT", "fields": ["a_id", "b_id"]},
            }
        ]
    }
    wf = tmp_path / "wf.json"
    wf.write_text(json.dumps(data))
    out = pkg.convert_mappings_to_sql(wf)
    sql = out["m_cross"]
    assert "CROSS JOIN B" in sql
    # Columns qualified from their owning source
    assert "SELECT A.a_id, B.b_id" in sql
    assert "INSERT INTO TGT (a_id, b_id)" in sql


def test_idmc_multiple_targets(tmp_path: Path) -> None:
    data = {
        "mappings": [
            {
                "name": "m_multi_tgt",
                "source": {"name": "SRC", "fields": ["id", "name"]},
                "targets": [
                    {"name": "T1", "fields": ["id"]},
                    {"name": "T2", "fields": ["name"]},
                ],
            }
        ]
    }
    wf = tmp_path / "wf.json"
    wf.write_text(json.dumps(data))
    out = pkg.convert_mappings_to_sql(wf)
    sql = out["m_multi_tgt"]
    assert "INSERT INTO T1 (id)" in sql
    assert "INSERT INTO T2 (name)" in sql


def test_idmc_field_shapes(tmp_path: Path) -> None:
    data = {
        "mappings": [
            {
                "name": "m_shapes",
                "sources": [
                    {
                        "name": "SRC1",
                        "schema": {"fields": [{"name": "id"}, {"name": "name"}]},
                    },
                    {"name": "SRC2", "columns": ["id", {"name": "amount"}]},
                ],
                "target": {"name": "TGT", "ports": ["id", "name", "amount"]},
            }
        ]
    }
    wf = tmp_path / "wf.json"
    wf.write_text(json.dumps(data))
    out = pkg.convert_mappings_to_sql(wf)
    sql = out["m_shapes"]
    # Should detect common 'id' for JOIN
    assert "JOIN SRC2 USING (id)" in sql
    # Qualify non-common columns
    assert "SELECT id, SRC1.name, SRC2.amount" in sql
