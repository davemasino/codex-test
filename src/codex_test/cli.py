from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, convert_mappings_to_sql


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="codex-test",
        description=(
            "Convert Informatica mappings to ANSI SQL (IDMC JSON or PowerCenter XML)"
        ),
    )
    parser.add_argument("workflow", type=Path, help="Path to workflow XML document")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory to write one <mapping>.sql per mapping",
    )
    parser.add_argument(
        "--version", action="version", version=f"codex-test {__version__}"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    sql_map = convert_mappings_to_sql(args.workflow)

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, sql in sql_map.items():
            out = args.output_dir / f"{name}.sql"
            out.write_text(sql)
    else:
        # Print to stdout, separated by blank lines in a stable order
        for idx, name in enumerate(sorted(sql_map)):
            if idx:
                print()
            print(sql_map[name], end="")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
