from __future__ import annotations

import json
from pathlib import Path

import pytest

import codex_test.llm as llm


def test_build_idmc_prompt_structure() -> None:
    mapping = {
        "mappings": [
            {
                "name": "m1",
                "source": {"name": "SRC", "fields": ["id"]},
                "target": {"name": "TGT", "fields": ["id"]},
            }
        ]
    }
    msgs = llm.build_idmc_prompt(mapping)
    assert isinstance(msgs, list) and len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"
    assert "INSERT INTO" in msgs[1]["content"]
    assert "JOIN" in msgs[1]["content"]
    # JSON payload should be embedded
    assert "mappings" in msgs[1]["content"]


def test_llm_convert_idmc_to_sql_monkeypatched(tmp_path: Path, monkeypatch) -> None:
    # Prepare an IDMC JSON file
    data = {
        "mappings": [
            {
                "name": "m1",
                "source": {"name": "SRC", "fields": ["id"]},
                "target": {"name": "TGT", "fields": ["id"]},
            }
        ]
    }
    wf = tmp_path / "wf.json"
    wf.write_text(json.dumps(data))

    # Fake OpenAI client response
    class _Msg:
        content = "-- fake sql\nSELECT 1;"

    class _Choice:
        message = _Msg()

    class _Resp:
        choices = [_Choice()]

    class _FakeChatCompletions:
        def create(self, **kwargs):  # type: ignore[no-untyped-def]
            return _Resp()

    class _FakeChat:
        completions = _FakeChatCompletions()

    class _FakeClient:
        chat = _FakeChat()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(llm, "get_openai_client", lambda: _FakeClient())

    out = llm.llm_convert_idmc_to_sql(wf, model="test-model")
    assert "fake sql" in out


def test_get_openai_client_requires_env(monkeypatch) -> None:
    # Ensure missing API key raises a clear error
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Protect against accidental .env loading by stubbing loader to no-op
    monkeypatch.setattr(llm, "_maybe_load_dotenv", lambda: None)
    with pytest.raises(RuntimeError) as exc:
        llm.get_openai_client()
    assert "OPENAI_API_KEY" in str(exc.value)
