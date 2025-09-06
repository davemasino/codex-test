"""Utilities for working with Informatica PowerCenter and IDMC workflows.

This module provides minimal parsing of Informatica PowerCenter workflow XML
documents and a best-effort conversion of simple mappings to ANSI SQL. The
conversion supports basic cases where a mapping contains a single source and a
single target definition with fields. Complex transformations (joins, filters,
aggregations, expressions, lookups, etc.) are not modeled and will result in a
placeholder SQL statement.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from typing import Dict, List

__all__ = [
    "__version__",
    "count_mappings",
    "convert_mappings_to_sql",
]

__version__ = "0.1.0"


def count_mappings(workflow_path: str | Path) -> int:
    """Count mappings in a workflow document (PowerCenter XML or IDMC JSON).

    Parameters
    ----------
    workflow_path:
        Path to an Informatica PowerCenter workflow XML document.

    Returns
    -------
    int
        Number of ``MAPPING`` elements found in the document.
    """

    p = Path(workflow_path)
    if _looks_like_json(p):
        try:
            data = json.loads(p.read_text())
        except Exception:
            # Fallback: treat as zero if unreadable JSON
            return 0
        return len(_iter_idmc_mappings(data))
    else:
        tree = ET.parse(p)
        return len(tree.findall(".//MAPPING"))


def _text_identifier(name: str | None) -> str:
    """Return a safe identifier for SQL output.

    Currently this performs a minimal pass-through and is intended to keep the
    output ANSI-SQL flavoured without vendor specifics. In the future this could
    quote or sanitize reserved words.
    """

    return (name or "").strip()


def _fields_from_transformation(xform: ET.Element) -> List[str]:
    return [f.get("NAME", "").strip() for f in xform.findall("FIELD") if f.get("NAME")]


def _first_child(elem: ET.Element, xpath: str) -> ET.Element | None:
    found = elem.findall(xpath)
    return found[0] if found else None


def convert_mappings_to_sql(workflow_path: str | Path) -> Dict[str, str]:
    """Convert each mapping (PowerCenter XML or IDMC JSON) to ANSI-SQL.

    The converter handles simple patterns where a mapping declares one source
    transformation (TYPE contains "Source") and one target transformation (TYPE
    contains "Target"). When fields are present under the target (preferred) or
    source, it creates an INSERT INTO ... SELECT ... statement mapping like-named
    columns. For unrecognized or underspecified mappings, a placeholder SELECT
    with a comment is produced.

    Parameters
    ----------
    workflow_path:
        Path to an Informatica PowerCenter workflow XML document.

    Returns
    -------
    dict[str, str]
        Mapping name to generated SQL text.
    """

    p = Path(workflow_path)
    sql_by_mapping: Dict[str, str] = {}

    if _looks_like_json(p):
        try:
            data = json.loads(p.read_text())
        except Exception:
            return {}
        for m_name, src_name, tgt_name, cols in _idmc_mapping_details(data):
            sql_by_mapping[m_name] = _emit_insert_select(m_name, tgt_name, src_name, cols)
        return sql_by_mapping

    # PowerCenter XML path (legacy support)
    tree = ET.parse(p)
    root = tree.getroot()

    for m in root.findall(".//MAPPING"):
        m_name = m.get("NAME") or "UNKNOWN_MAPPING"
        # Find source/target transformations inside the mapping
        xforms = list(m.findall("TRANSFORMATION"))
        srcs = [x for x in xforms if (x.get("TYPE") or "").lower().startswith("source")]
        tgts = [x for x in xforms if (x.get("TYPE") or "").lower().startswith("target")]

        src = srcs[0] if len(srcs) == 1 else None
        tgt = tgts[0] if len(tgts) == 1 else None

        if src is not None and tgt is not None:
            src_name = _text_identifier(src.get("NAME")) or "SOURCE"
            tgt_name = _text_identifier(tgt.get("NAME")) or "TARGET"

            tgt_fields = [f for f in _fields_from_transformation(tgt) if f]
            src_fields = [f for f in _fields_from_transformation(src) if f]

            # Prefer intersection of target and source fields, maintain target order
            if tgt_fields and src_fields:
                src_set = {f.lower() for f in src_fields}
                cols = [c for c in tgt_fields if c.lower() in src_set]
            else:
                # Fall back to whichever side has fields; if neither, use '*'
                cols = tgt_fields or src_fields

            sql = _emit_insert_select(m_name, tgt_name, src_name, cols)
        else:
            # Could not infer source/target; emit a placeholder
            sql = (
                f"-- Mapping: {m_name} (unsupported or underspecified)\n"
                f"-- No clear single source/target; manual conversion required.\n"
                f"SELECT /* mapping {m_name} */ *;\n"
            )

        sql_by_mapping[m_name] = sql

    return sql_by_mapping


def _emit_insert_select(m_name: str, tgt_name: str, src_name: str, cols: list[str]) -> str:
    if cols:
        cols_csv = ", ".join(cols)
        return (
            f"-- Mapping: {m_name}\n"
            f"INSERT INTO {tgt_name} ({cols_csv})\n"
            f"SELECT {cols_csv} FROM {src_name};\n"
        )
    return (
        f"-- Mapping: {m_name} (no fields found)\n"
        f"-- Unable to infer columns; emitting broad SELECT.\n"
        f"INSERT INTO {tgt_name}\n"
        f"SELECT * FROM {src_name};\n"
    )


def _looks_like_json(path: Path) -> bool:
    if path.suffix.lower() == ".json":
        return True
    # Peek first non-whitespace char
    try:
        for ch in path.read_text(encoding="utf-8"):
            if not ch.isspace():
                return ch in "[{"  # JSON object/array
    except Exception:
        return False
    return False


def _iter_idmc_mappings(data: dict) -> List[dict]:
    # Primary expected structure: { "mappings": [ {"name":..., "source":..., "target":...} ] }
    if isinstance(data, dict):
        if isinstance(data.get("mappings"), list):
            return [m for m in data["mappings"] if isinstance(m, dict)]
        # Alternate: { "objects": [ {"type":"mapping", ...} ] }
        if isinstance(data.get("objects"), list):
            return [m for m in data["objects"] if isinstance(m, dict) and (m.get("type") or "").lower() == "mapping"]
    return []


def _normalize_field_list(fields: object) -> List[str]:
    cols: List[str] = []
    if isinstance(fields, list):
        for f in fields:
            if isinstance(f, str):
                nm = f.strip()
                if nm:
                    cols.append(nm)
            elif isinstance(f, dict):
                nm = str(f.get("name") or f.get("NAME") or "").strip()
                if nm:
                    cols.append(nm)
    return cols


def _idmc_mapping_details(data: dict):
    """Yield tuples of (mapping_name, source_name, target_name, columns)."""
    for m in _iter_idmc_mappings(data):
        m_name = str(m.get("name") or m.get("NAME") or "UNKNOWN_MAPPING").strip() or "UNKNOWN_MAPPING"

        src = m.get("source") or {}
        tgt = m.get("target") or {}

        # Some structures may have arrays of sources/targets; pick the first
        if isinstance(src, list) and src:
            src = src[0]
        if isinstance(tgt, list) and tgt:
            tgt = tgt[0]

        src_name = _text_identifier(str((src or {}).get("name") or (src or {}).get("NAME") or "SOURCE")) or "SOURCE"
        tgt_name = _text_identifier(str((tgt or {}).get("name") or (tgt or {}).get("NAME") or "TARGET")) or "TARGET"

        # Columns: prefer target fields' order, intersect with source if present
        tgt_fields = _normalize_field_list((tgt or {}).get("fields"))
        src_fields = _normalize_field_list((src or {}).get("fields"))

        if tgt_fields and src_fields:
            src_set = {c.lower() for c in src_fields}
            cols = [c for c in tgt_fields if c.lower() in src_set]
        else:
            cols = tgt_fields or src_fields

        yield m_name, src_name, tgt_name, cols
