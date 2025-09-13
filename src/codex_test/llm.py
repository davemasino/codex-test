from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _maybe_load_dotenv() -> None:
    """Load .env if python-dotenv is available and file exists.

    We avoid a hard dependency: in dev, python-dotenv is included via the
    optional "dev" extras. In production, environment variables should be set
    by the runtime environment.
    """

    try:
        from dotenv import load_dotenv

        # Only attempt if a .env is present in CWD or project root
        for candidate in (
            Path.cwd() / ".env",
            Path(__file__).resolve().parents[2] / ".env",
        ):
            if candidate.exists():
                load_dotenv(candidate)
                break
    except Exception:
        # Silently ignore if dotenv isn't installed or any load issue occurs
        pass


def get_openai_client() -> Any:
    """Return an OpenAI client configured from environment.

    Requires `OPENAI_API_KEY` to be present. Attempts to load from `.env` if
    python-dotenv is available and a file exists.
    """

    _maybe_load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set. Provide it via env or a .env file.")

    try:
        from openai import OpenAI
    except Exception as exc:  # pragma: no cover - import-time failure path
        raise RuntimeError(
            "The 'openai' package is required. Install it in your environment."
        ) from exc

    return OpenAI(api_key=api_key)


def build_idmc_prompt(mapping_json: dict[str, Any]) -> list[dict[str, str]]:
    """Construct a chat prompt asking the model to emit ANSI SQL for mappings.

    The prompt instructs the model to generate INSERT ... SELECT statements for
    each mapping found, mirroring the deterministic converter but allowing the
    model to infer complex transformations when present.
    """

    system = (
        "You are a precise data engineer. Convert Informatica IDMC mappings "
        "to ANSI SQL. Prefer deterministic output. If uncertain, comment with "
        "TODO notes rather than guessing."
    )
    user = (
        "Given the following IDMC workflow JSON, generate SQL for each mapping.\n"
        "- Use INSERT INTO <target>(cols) SELECT ... FROM ...;\n"
        "- Use JOIN ... USING(...) when sources share columns; else CROSS JOIN.\n"
        "- If a target column is not found, project NULL AS <col>.\n"
        "- Separate multiple mappings with a blank line.\n\n"
        f"JSON:\n{json.dumps(mapping_json, indent=2)}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def llm_convert_idmc_to_sql(path: Path, model: str | None = None) -> str:
    """Call OpenAI to convert an IDMC JSON workflow to SQL.

    Parameters
    ----------
    path: Path
        Path to an IDMC JSON file.
    model: str | None
        OpenAI model name. If None, reads from the environment variable
        `OPENAI_MODEL` (loaded from .env in dev if available), defaulting to
        "gpt-5-mini".
    """

    # Resolve model from argument, env, or fallback
    _maybe_load_dotenv()
    resolved_model = model or os.getenv("OPENAI_MODEL") or "gpt-5-mini"

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    messages = build_idmc_prompt(data)
    client = get_openai_client()
    # Use Chat Completions for broad compatibility
    resp = client.chat.completions.create(
        model=resolved_model,
        messages=messages,
        temperature=0,
    )
    return resp.choices[0].message.content or ""
