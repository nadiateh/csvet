import json
from types import SimpleNamespace

import pytest

from csvet.llm import make_caller, make_openai_caller
from csvet.privacy import mask_profile
from csvet.proposer import propose_rules


class FakeClient:
    def __init__(self, content):
        self.content = content
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content=self.content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


MESSAGES = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]


def test_caller_sends_model_messages_and_json_mode():
    client = FakeClient('{"rules": []}')
    make_caller(client, "some-model")(MESSAGES)
    sent = client.calls[0]
    assert sent["model"] == "some-model"
    assert sent["messages"] == MESSAGES
    assert sent["response_format"] == {"type": "json_object"}


def test_caller_returns_the_reply_text():
    assert make_caller(FakeClient("hello"), "m")(MESSAGES) == "hello"


def test_caller_turns_an_empty_reply_into_empty_text():
    assert make_caller(FakeClient(None), "m")(MESSAGES) == ""


def test_caller_plugs_into_propose_rules():
    reply = json.dumps({"rules": [
        {"type": "normalize_text", "column": "city", "case": "title", "reason": "x"},
    ]})
    profile = mask_profile({
        "row_count": 1,
        "columns": {"city": {"top_values": [{"value": "QC", "count": 1}]}},
    })
    rule_set, attempts = propose_rules(profile, make_caller(FakeClient(reply), "m"))
    assert attempts == 1
    assert rule_set.rules[0].column == "city"


def test_missing_key_is_reported(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "m")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        make_openai_caller()


def test_placeholder_key_is_reported(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "your-key-here")
    monkeypatch.setenv("OPENAI_MODEL", "m")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        make_openai_caller()


def test_missing_model_is_reported(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_MODEL"):
        make_openai_caller()


def test_caller_is_built_when_settings_exist(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "some-model")
    assert callable(make_openai_caller())