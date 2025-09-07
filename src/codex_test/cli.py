from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .llm import llm_convert_idmc_to_sql


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="codex-test",
        description=(
            "Generate ANSI SQL from an Informatica IDMC workflow JSON using an LLM"
        ),
    )
    parser.add_argument("workflow", type=Path, help="Path to IDMC workflow JSON")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory to write <stem>.sql with generated SQL",
    )
    parser.add_argument(
        "--version", action="version", version=f"codex-test {__version__}"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    sql = llm_convert_idmc_to_sql(args.workflow)

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        out = args.output_dir / f"{args.workflow.stem}.sql"
        out.write_text(sql)
    else:
        print(sql)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
