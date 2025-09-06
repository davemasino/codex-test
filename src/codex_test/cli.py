from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, count_mappings


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="codex-test",
        description="Count mappings in an Informatica PowerCenter workflow document",
    )
    parser.add_argument("workflow", type=Path, help="Path to workflow XML document")
    parser.add_argument(
        "--version", action="version", version=f"codex-test {__version__}"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    total = count_mappings(args.workflow)
    print(total)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
