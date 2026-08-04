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


@pytest.fixture(autouse=True)
def reset_client_cache(monkeypatch):
    """bridgeai caches its client in a module global; start each test clean."""
    monkeypatch.setattr(bridgeai, "_client", None)


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


def test_get_client_passes_api_key_and_caches_instance(fake_client):
    fake_client(lambda model: "ok")

    client = bridgeai.get_client()

    assert client.api_key == "test-key"
    assert bridgeai.get_client() is client
    assert bridgeai._client is client


def test_get_client_returns_none_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    assert bridgeai.get_client() is None


def test_get_client_returns_none_when_init_fails(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    def broken_client(api_key=None):
        raise ValueError("bad key")

    monkeypatch.setattr(google.genai, "Client", broken_client)

    assert bridgeai.get_client() is None
    assert bridgeai._client is None


def test_build_prompt_includes_audience_task_and_information():
    prompt = bridgeai.build_prompt(
        "Children", "Simplify the information below.", information="the facts"
    )

    assert "Children" in prompt
    assert "Simplify the information below." in prompt
    assert "Information:\nthe facts" in prompt
    assert "## Simple Explanation" in prompt
    assert "## Key Points" in prompt
    assert "## Important Actions" in prompt


def test_build_prompt_omits_information_section_when_not_given():
    prompt = bridgeai.build_prompt("Seniors", "Analyze this document image.")

    assert "Information:" not in prompt


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
    assert [model for model, _ in calls] == bridgeai.MODELS


def test_generate_ai_response_skips_models_with_empty_text(fake_client):
    def behaviour(model):
        return "" if model == "gemini-2.5-flash" else "second answer"

    calls = fake_client(behaviour)

    assert bridgeai.generate_ai_response("hello") == "second answer"
    assert len(calls) == 2


def test_generate_ai_response_reports_when_all_models_fail(fake_client):
    calls = fake_client(lambda model: RuntimeError("boom"))

    assert bridgeai.generate_ai_response("hello") == bridgeai.UNAVAILABLE_MESSAGE
    assert len(calls) == len(bridgeai.MODELS)


def test_generate_ai_response_reports_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = bridgeai.generate_ai_response("hello")

    assert "BridgeAI Error" in result
    assert "GEMINI_API_KEY` is missing" in result


def test_simplify_text_builds_prompt_with_audience_and_text(fake_client):
    calls = fake_client(lambda model: "ok")

    assert bridgeai.simplify_text("complex clause", audience="Children") == "ok"

    prompt = calls[0][1]
    assert "Children" in prompt
    assert "complex clause" in prompt
    assert "Simplify the information below." in prompt


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


def test_analyze_image_defaults_to_general_public(fake_client):
    calls = fake_client(lambda model: "ok")

    bridgeai.analyze_image(object())

    assert "General public" in calls[0][1][0]
