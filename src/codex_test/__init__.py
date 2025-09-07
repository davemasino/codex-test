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


def _fields_from_transformation(xform: ET.Element) -> list[str]:
    return [f.get("NAME", "").strip() for f in xform.findall("FIELD") if f.get("NAME")]


def _first_child(elem: ET.Element, xpath: str) -> ET.Element | None:
    found = elem.findall(xpath)
    return found[0] if found else None


def convert_mappings_to_sql(workflow_path: str | Path) -> dict[str, str]:
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
    sql_by_mapping: dict[str, str] = {}

    if _looks_like_json(p):
        try:
            data = json.loads(p.read_text())
        except Exception:
            return {}
        # Build SQL for each mapping, supporting multiple sources/targets.
        for plan in _idmc_mapping_plans(data):
            m_name = plan["name"]
            sources = plan["sources"]  # list[(name, fields)]
            targets = plan["targets"]  # list[(name, fields)]

            if not sources or not targets:
                sql_by_mapping[m_name] = (
                    f"-- Mapping: {m_name} (unsupported or underspecified)\n"
                    f"-- Requires at least one source and one target.\n"
                    f"SELECT /* mapping {m_name} */ *;\n"
                )
                continue

            sel_list, from_sql, note = _build_select_from_sources(sources, None)

            # For each target, generate an INSERT using target's field order
            statements: list[str] = []
            for tgt_name, tgt_fields in targets:
                cols = tgt_fields or []
                # If specific target columns provided, narrow the select list order
                if cols:
                    # Recompute select list in target order with qualification as needed
                    sel_list_target, _, _ = _build_select_from_sources(sources, cols)
                    final_sel = sel_list_target
                    cols_csv = ", ".join(cols)
                else:
                    final_sel = sel_list
                    cols_csv = (
                        ", ".join(_union_fields(sources)) if final_sel != "*" else ""
                    )

                head = f"-- Mapping: {m_name} -> {tgt_name}\n"
                if note:
                    head += f"-- {note}\n"

                if cols_csv:
                    stmt = (
                        head
                        + f"INSERT INTO {tgt_name} ({cols_csv})\n"
                        + f"SELECT {final_sel}\n"
                        + f"{from_sql};\n"
                    )
                else:
                    stmt = (
                        head
                        + f"INSERT INTO {tgt_name}\nSELECT {final_sel}\n{from_sql};\n"
                    )
                statements.append(stmt)

            sql_by_mapping[m_name] = "\n".join(statements)

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


def _emit_insert_select(
    m_name: str, tgt_name: str, src_name: str, cols: list[str]
) -> str:
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


def _iter_idmc_mappings(data: dict) -> list[dict]:
    # Primary expected structure:
    # {"mappings": [{"name": ..., "source": ..., "target": ...}]}
    if isinstance(data, dict):
        if isinstance(data.get("mappings"), list):
            return [m for m in data["mappings"] if isinstance(m, dict)]
        # Alternate: { "objects": [ {"type":"mapping", ...} ] }
        if isinstance(data.get("objects"), list):
            return [
                m
                for m in data["objects"]
                if isinstance(m, dict) and (m.get("type") or "").lower() == "mapping"
            ]
    return []


def _normalize_field_list(fields: object) -> list[str]:
    """Extract a flat list of column names from varied shapes.

    Supported inputs:
    - list[str]
    - list[dict] with keys: name/NAME
    - dicts containing 'fields'/'columns'/'ports'/'children' recursively
    - dict with 'schema': { 'fields': [...] }
    - dict with 'items': [...]
    """
    cols: list[str] = []

    def add_name(n: object) -> None:
        if isinstance(n, str):
            nm = n.strip()
        else:
            nm = str(n or "").strip()
        if nm:
            cols.append(nm)

    def walk(node: object) -> None:
        if node is None:
            return
        if isinstance(node, list):
            for it in node:
                walk(it)
            return
        if isinstance(node, dict):
            # direct name
            if any(k in node for k in ("name", "NAME")):
                add_name(node.get("name") or node.get("NAME"))
            # nested collections
            for k in ("fields", "columns", "ports", "children", "items"):
                if k in node:
                    walk(node[k])
            if "schema" in node and isinstance(node["schema"], dict):
                if "fields" in node["schema"]:
                    walk(node["schema"]["fields"])
            return
        # leaf scalar
        add_name(node)

    walk(fields)
    # Preserve order but deduplicate case-insensitively
    seen: set[str] = set()
    unique: list[str] = []
    for c in cols:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def _idmc_mapping_plans(data: dict) -> list[dict]:
    """Return normalized mapping plans with sources and targets.

    A plan is: {"name": str, "sources": list[(name, fields)],
    "targets": list[(name, fields)]}
    Accepts both singular and plural keys (source/sources, target/targets).
    """
    plans: list[dict] = []
    for m in _iter_idmc_mappings(data):
        m_name = (
            str(m.get("name") or m.get("NAME") or "UNKNOWN_MAPPING").strip()
            or "UNKNOWN_MAPPING"
        )

        sources_obj = m.get("sources") if "sources" in m else m.get("source")
        targets_obj = m.get("targets") if "targets" in m else m.get("target")

        sources = _coerce_endpoints(sources_obj, default_name="SOURCE")
        targets = _coerce_endpoints(targets_obj, default_name="TARGET")

        plans.append({"name": m_name, "sources": sources, "targets": targets})
    return plans


def _coerce_endpoints(obj: object, default_name: str) -> list[tuple[str, list[str]]]:
    """Normalize endpoint(s) to a list of (name, fields).

    Supports singular dict, list of dicts, or list of names/field dicts.
    Recognizes fields under keys: fields, columns, ports, schema.fields, items.
    """
    items: list[object] = []
    if obj is None:
        return []
    if isinstance(obj, list):
        items = obj
    else:
        items = [obj]

    results: list[tuple[str, list[str]]] = []
    for it in items:
        name = default_name
        f_list: list[str] = []
        if isinstance(it, str):
            name = _text_identifier(it) or default_name
        elif isinstance(it, dict):
            name = (
                _text_identifier(str(it.get("name") or it.get("NAME") or default_name))
                or default_name
            )
            # fields under various keys
            for k in ("fields", "columns", "ports", "schema", "items"):
                if k in it:
                    f_list.extend(_normalize_field_list(it[k]))
        # Deduplicate while preserving order
        seen: set[str] = set()
        uniq_fields: list[str] = []
        for c in f_list:
            key = c.lower()
            if key not in seen:
                seen.add(key)
                uniq_fields.append(c)
        results.append((name, uniq_fields))
    return results


def _union_fields(sources: list[tuple[str, list[str]]]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for _, fields in sources:
        for c in fields:
            k = c.lower()
            if k not in seen:
                seen.add(k)
                out.append(c)
    return out


def _common_fields(sources: list[tuple[str, list[str]]]) -> list[str]:
    if not sources:
        return []
    common = {c.lower() for c in sources[0][1]}
    for _, fields in sources[1:]:
        common &= {c.lower() for c in fields}
    # return original-case using first source ordering
    return [c for c in sources[0][1] if c.lower() in common]


def _build_select_from_sources(
    sources: list[tuple[str, list[str]]], target_cols: list[str] | None
) -> tuple[str, str, str | None]:
    """Return (select_list, from_sql, note).

    - If multiple sources share columns, JOIN ... USING(common_cols).
    - If no common columns, CROSS JOIN with a note.
    - Select list uses target_cols order if provided; otherwise union of source fields.
    - Qualify columns when needed to disambiguate.
    """
    if len(sources) == 1:
        src_name, fields = sources[0]
        # If target columns are specified, ensure each exists; otherwise project NULL
        if target_cols:
            src_set = {c.lower() for c in (fields or [])}
            single_select_exprs = [
                (c if c.lower() in src_set else f"NULL AS {c}")
                for c in target_cols
                if c
            ]
            sel = ", ".join(single_select_exprs) if single_select_exprs else "*"
        else:
            cols = fields or ["*"]
            sel = ", ".join(cols) if cols != ["*"] else "*"
        return sel, f"FROM {src_name}", None

    commons = _common_fields(sources)
    if commons:
        using_csv = ", ".join(commons)
        # Build chained INNER JOINs with USING
        from_parts = [f"FROM {sources[0][0]}"]
        for src_name, _ in sources[1:]:
            from_parts.append(f"JOIN {src_name} USING ({using_csv})")
        from_sql = "\n".join(from_parts)
        note = None
    else:
        # CROSS JOIN if no shared fields
        from_sql = "\n".join(
            [f"FROM {sources[0][0]}"] + [f"CROSS JOIN {s[0]}" for s in sources[1:]]
        )
        note = "No common columns across sources; used CROSS JOIN"

    # Determine select list
    if target_cols:
        wanted = [c for c in target_cols if c]
    else:
        wanted = _union_fields(sources)

    # If commons are used, columns in commons can be unqualified
    commons_lc = {c.lower() for c in commons}

    # Map to which source contains a column
    def owner(col: str) -> str | None:
        cl = col.lower()
        for src_name, fields in sources:
            if any(f.lower() == cl for f in fields):
                return src_name
        return None

    select_exprs: list[str] = []
    for c in wanted:
        if c.lower() in commons_lc:
            select_exprs.append(c)
        else:
            src = owner(c)
            if src:
                select_exprs.append(f"{src}.{c}")
            else:
                # Column not present; project NULL as placeholder
                select_exprs.append(f"NULL AS {c}")

    sel = ", ".join(select_exprs) if select_exprs else "*"
    return sel, from_sql, note
