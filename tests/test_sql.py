from __future__ import annotations

from pathlib import Path

import codex_test as pkg

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


def test_convert_mappings_to_sql_basic(tmp_path: Path) -> None:
    wf = tmp_path / "wf.xml"
    wf.write_text(SIMPLE_MAPPING)
    out = pkg.convert_mappings_to_sql(wf)
    assert set(out.keys()) == {"m_simple"}
    sql = out["m_simple"]
    assert "INSERT INTO TGT_TABLE (id, name)" in sql
    assert "SELECT id, name FROM SRC_TABLE;" in sql
