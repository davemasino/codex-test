from __future__ import annotations

import argparse
import sys

from . import __version__, greet


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="codex-test", description="Example CLI")
    parser.add_argument("name", nargs="?", default="world", help="Name to greet")
    parser.add_argument(
        "--version", action="version", version=f"codex-test {__version__}"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(greet(args.name))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

