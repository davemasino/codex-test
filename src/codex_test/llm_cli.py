from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .llm import llm_convert_idmc_to_sql


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="codex-llm",
        description=(
            "Generate ANSI SQL from an Informatica IDMC workflow JSON using OpenAI"
        ),
    )
    p.add_argument("workflow", type=Path, help="Path to IDMC workflow JSON file")
    # Default model from env var if set, else fallback
    default_model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    p.add_argument(
        "--model",
        default=default_model,
        help=f"OpenAI model (default: {default_model}; override with OPENAI_MODEL)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    sql = llm_convert_idmc_to_sql(args.workflow, model=args.model)
    print(sql)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
