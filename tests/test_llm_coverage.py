from __future__ import annotations

import types
from pathlib import Path

import pytest

import codex_test.llm as llm


def test__maybe_load_dotenv_loads_from_cwd(tmp_path: Path, monkeypatch) -> None:
    # Create a .env in the current working directory
    monkeypatch.chdir(tmp_path)
    env_path = tmp_path / ".env"
    env_path.write_text("OPENAI_MODEL=gpt-xyz\n", encoding="utf-8")

    # Install a fake `dotenv` module to observe calls to load_dotenv
    calls: list[Path] = []

    def _fake_load_dotenv(p: Path) -> None:  # type: ignore[no-untyped-def]
        calls.append(p)

    fake_dotenv = types.SimpleNamespace(load_dotenv=_fake_load_dotenv)
    monkeypatch.setitem(__import__("sys").modules, "dotenv", fake_dotenv)

    llm._maybe_load_dotenv()

    # Should have attempted to load the .env from CWD
    assert calls and calls[0] == env_path


def test_get_openai_client_import_error_path(monkeypatch) -> None:
    # Provide an API key so the function proceeds to import `openai`
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Insert a dummy `openai` module without `OpenAI` attribute to trigger error
    fake_openai = types.SimpleNamespace()
    monkeypatch.setitem(__import__("sys").modules, "openai", fake_openai)

    with pytest.raises(RuntimeError) as exc:
        llm.get_openai_client()
    assert "openai" in str(exc.value).lower()

