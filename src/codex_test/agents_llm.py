from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from .llm import _maybe_load_dotenv


def _require_api_key() -> None:
    """Ensure `OPENAI_API_KEY` is present for the Agents SDK."""

    _maybe_load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY not set. Provide it via env or a .env file."
        )


def agent_convert_idmc_to_sql(path: Path, model: str | None = None) -> str:
    """Convert an IDMC workflow JSON to ANSI SQL using the OpenAI Agents SDK.

    This provides an agentic implementation parallel to the existing
    chat-completions variant, keeping the public API of the package stable.
    """

    _require_api_key()

    try:
        # OpenAI Agents SDK
        from agents import Agent, Runner, function_tool
    except Exception as exc:  # pragma: no cover - import-time failure path
        raise RuntimeError(
            "The 'openai-agents' package is required. Install it in your environment."
        ) from exc

    resolved_model = model or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

    @function_tool
    def read_workflow_json(file_path: str) -> dict[str, Any]:
        """Load and return the IDMC workflow JSON from `file_path`."""

        p = Path(file_path)
        data = p.read_text(encoding="utf-8")
        import json as _json
        from typing import cast

        return cast(dict[str, Any], _json.loads(data))

    instructions = (
        "You are a precise data engineer. Convert Informatica IDMC mappings to "
        "deterministic ANSI SQL. Use the read_workflow_json tool to load the "
        "workflow at the provided path.\n\n"
        "Guidelines:\n"
        "- For each mapping, emit: INSERT INTO <target>(cols) SELECT ... FROM ...;\n"
        "- Use JOIN ... USING(...) where sources share columns; else CROSS JOIN.\n"
        "- If a target column is missing, project NULL AS <col>.\n"
        "- Separate multiple mappings with a blank line.\n"
        "- If uncertain, include a SQL comment with a TODO rather than guessing."
    )

    agent = Agent(
        name="IDMC→SQL Agent",
        instructions=instructions,
        model=resolved_model,
        tools=[read_workflow_json],
    )

    async def _run() -> str:
        result = await Runner.run(
            agent,
            input=(
                "Convert the IDMC workflow at this path to SQL and return "
                "only the SQL.\n"
                f"workflow_path: {str(path)}"
            ),
        )
        return result.final_output or ""

    return asyncio.run(_run())
