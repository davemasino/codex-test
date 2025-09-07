from __future__ import annotations

import re
from pathlib import Path

import codex_test as pkg

SAMPLE_WORKFLOW = """<?xml version='1.0' encoding='UTF-8'?>
<REPOSITORY>
  <FOLDER>
    <MAPPING NAME='m1'/>
    <MAPPING NAME='m2'/>
    <MAPPING NAME='m3'/>
  </FOLDER>
</REPOSITORY>
"""


def test_version_format() -> None:
    assert re.match(r"^\d+\.\d+\.\d+$", pkg.__version__)


def test_count_mappings(tmp_path: Path) -> None:
    wf = tmp_path / "wf.xml"
    wf.write_text(SAMPLE_WORKFLOW)
    assert pkg.count_mappings(wf) == 3
