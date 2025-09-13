from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .agents_llm import agent_convert_idmc_to_sql


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="codex-agents",
        description=(
            "Generate ANSI SQL from an Informatica IDMC workflow JSON "
            "using OpenAI Agents SDK"
        ),
    )
    p.add_argument("workflow", type=Path, help="Path to IDMC workflow JSON file")
    default_model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    p.add_argument(
        "--model",
        default=default_model,
        help=(
            f"Model for the agent (default: {default_model}; "
            f"override with OPENAI_MODEL)"
        ),
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    sql = agent_convert_idmc_to_sql(args.workflow, model=args.model)
    print(sql)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
