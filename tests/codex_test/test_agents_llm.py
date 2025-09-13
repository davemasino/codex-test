from __future__ import annotations

import types
from pathlib import Path

import pytest

import codex_test.agents_llm as agents_llm


class _FakeResult:
    def __init__(self, text: str) -> None:
        self.final_output = text


def _install_fake_agents(monkeypatch, expected_text: str = "SELECT 1;") -> None:
    """Install a fake `agents` SDK into sys.modules for isolated testing."""

    class _FakeAgent:
        def __init__(self, *, name: str, instructions: str, model: str, tools):  # type: ignore[no-untyped-def]
            self.name = name
            self.instructions = instructions
            self.model = model
            self.tools = tools

    class _FakeRunner:
        @staticmethod
        async def run(agent, input: str):  # type: ignore[no-untyped-def]
            # Validate that a tool has been wired in and is callable
            assert agent.tools and callable(agent.tools[0])
            # Extract workflow_path from the provided input and invoke the tool
            wf_path = None
            for line in str(input).splitlines():
                if line.startswith("workflow_path: "):
                    wf_path = line.split(": ", 1)[1]
                    break
            if wf_path:
                agent.tools[0](wf_path)
            return _FakeResult(expected_text)

    def _function_tool(f):  # type: ignore[no-untyped-def]
        return f

    fake_mod = types.SimpleNamespace(
        Agent=_FakeAgent,
        Runner=_FakeRunner,
        function_tool=_function_tool,
    )
    monkeypatch.setitem(__import__("sys").modules, "agents", fake_mod)


def test_agent_convert_idmc_to_sql_reads_file_and_returns_sql(
    tmp_path: Path, monkeypatch
) -> None:
    # Prepare a minimal JSON file the tool will read
    wf = tmp_path / "wf.json"
    wf.write_text("{\n  \"mappings\": []\n}\n", encoding="utf-8")

    # Ensure API key requirement passes
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Provide the fake agents SDK
    _install_fake_agents(monkeypatch, expected_text="-- agent sql\nSELECT * FROM t;")

    out = agents_llm.agent_convert_idmc_to_sql(wf, model="fake-model")
    assert "agent sql" in out


def test_agent_convert_idmc_to_sql_errors_without_api_key(
    tmp_path: Path, monkeypatch
) -> None:
    wf = tmp_path / "wf.json"
    wf.write_text("{}", encoding="utf-8")
    # Prevent the helper from loading a real .env during this test
    monkeypatch.setattr(agents_llm, "_maybe_load_dotenv", lambda: None)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        agents_llm.agent_convert_idmc_to_sql(wf)
