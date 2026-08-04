import google.genai
import pytest

import bridgeai


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def __init__(self, behaviour, calls):
        self._behaviour = behaviour
        self._calls = calls

    def generate_content(self, model, contents):
        self._calls.append((model, contents))
        outcome = self._behaviour(model)
        if isinstance(outcome, Exception):
            raise outcome
        return FakeResponse(outcome)


class FakeClient:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.models = FakeModels(type(self).behaviour, type(self).calls)


@pytest.fixture
def fake_client(monkeypatch):
    """Install a stub genai.Client and expose its recorded calls."""

    def install(behaviour):
        calls = []
        client_class = type(
            "InstalledFakeClient",
            (FakeClient,),
            {"behaviour": staticmethod(behaviour), "calls": calls},
        )
        monkeypatch.setattr(google.genai, "Client", client_class)
        return calls

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    return install


def test_generate_ai_response_returns_first_successful_model(fake_client):
    calls = fake_client(lambda model: "simple explanation")

    assert bridgeai.generate_ai_response("hello") == "simple explanation"
    assert calls == [("gemini-2.5-flash", "hello")]


def test_generate_ai_response_falls_back_after_failures(fake_client):
    def behaviour(model):
        if model != "gemini-2.0-flash":
            return RuntimeError("model unavailable")
        return "fallback answer"

    calls = fake_client(behaviour)

    assert bridgeai.generate_ai_response("hello") == "fallback answer"
    assert [model for model, _ in calls] == [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
    ]


def test_generate_ai_response_skips_models_with_empty_text(fake_client):
    def behaviour(model):
        return "" if model == "gemini-2.5-flash" else "second answer"

    calls = fake_client(behaviour)

    assert bridgeai.generate_ai_response("hello") == "second answer"
    assert len(calls) == 2


def test_generate_ai_response_reports_when_all_models_fail(fake_client):
    fake_client(lambda model: RuntimeError("boom"))

    result = bridgeai.generate_ai_response("hello")

    assert "BridgeAI Error" in result
    assert "All AI models timed out or failed" in result


def test_generate_ai_response_reports_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = bridgeai.generate_ai_response("hello")

    assert "GEMINI_API_KEY` is missing" in result


def test_generate_ai_response_reports_client_init_failure(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    def broken_client(api_key=None):
        raise ValueError("bad key")

    monkeypatch.setattr(google.genai, "Client", broken_client)

    result = bridgeai.generate_ai_response("hello")

    assert "Could not initialize API client" in result
    assert "bad key" in result


def test_simplify_text_builds_prompt_with_audience_and_text(fake_client):
    calls = fake_client(lambda model: "ok")

    bridgeai.simplify_text("complex clause", audience="Children")

    prompt = calls[0][1]
    assert "Children" in prompt
    assert "complex clause" in prompt
    assert "## Simple Explanation" in prompt
    assert "## Key Points" in prompt
    assert "## Important Actions" in prompt


def test_simplify_text_defaults_to_general_public(fake_client):
    calls = fake_client(lambda model: "ok")

    bridgeai.simplify_text("complex clause")

    assert "General public" in calls[0][1]


def test_analyze_image_sends_prompt_and_image(fake_client):
    calls = fake_client(lambda model: "ok")
    image = object()

    assert bridgeai.analyze_image(image, "Seniors") == "ok"

    contents = calls[0][1]
    assert contents[1] is image
    assert "Seniors" in contents[0]
    assert "Analyze this document image." in contents[0]
