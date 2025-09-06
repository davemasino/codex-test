"""Utilities for working with Informatica PowerCenter workflows.

This module provides minimal parsing of Informatica PowerCenter workflow XML
documents and a best-effort conversion of simple mappings to ANSI SQL. The
conversion supports basic cases where a mapping contains a single source and a
single target definition with fields. Complex transformations (joins, filters,
aggregations, expressions, lookups, etc.) are not modeled and will result in a
placeholder SQL statement.
"""

from __future__ import annotations

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
    """Count ``MAPPING`` elements in a workflow document.

    Parameters
    ----------
    workflow_path:
        Path to an Informatica PowerCenter workflow XML document.

    Returns
    -------
    int
        Number of ``MAPPING`` elements found in the document.
    """

    tree = ET.parse(workflow_path)
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
    """Convert each mapping in a workflow to a best-effort ANSI-SQL string.

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

    tree = ET.parse(workflow_path)
    root = tree.getroot()

    sql_by_mapping: Dict[str, str] = {}

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

            if cols:
                cols_csv = ", ".join(cols)
                sql = (
                    f"-- Mapping: {m_name}\n"
                    f"INSERT INTO {tgt_name} ({cols_csv})\n"
                    f"SELECT {cols_csv} FROM {src_name};\n"
                )
            else:
                sql = (
                    f"-- Mapping: {m_name} (no fields found)\n"
                    f"-- Unable to infer columns; emitting broad SELECT.\n"
                    f"INSERT INTO {tgt_name}\n"
                    f"SELECT * FROM {src_name};\n"
                )
        else:
            # Could not infer source/target; emit a placeholder
            sql = (
                f"-- Mapping: {m_name} (unsupported or underspecified)\n"
                f"-- No clear single source/target; manual conversion required.\n"
                f"SELECT /* mapping {m_name} */ *;\n"
            )

        sql_by_mapping[m_name] = sql

    return sql_by_mapping
