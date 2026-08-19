from __future__ import annotations

from src.llm import can_use_llm, llm_model_name, llm_provider


def clear_provider_env(monkeypatch):
    for name in [
        "AI_PROVIDER",
        "GROQ_API_KEY",
        "GROQ_MODEL",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
    ]:
        monkeypatch.delenv(name, raising=False)


def test_no_key_keeps_manual_review_mode(monkeypatch):
    clear_provider_env(monkeypatch)
    assert llm_provider() is None
    assert llm_model_name() is None
    assert can_use_llm() is False


def test_groq_is_preferred_in_auto_mode(monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("GROQ_API_KEY", "test-groq")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    assert llm_provider() == "groq"
    assert llm_model_name() == "openai/gpt-oss-20b"
    assert can_use_llm() is True


def test_explicit_openai_selection(monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    assert llm_provider() == "openai"
    assert llm_model_name() == "gpt-5.6"


def test_explicit_provider_without_key_is_unavailable(monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "groq")
    assert llm_provider() is None
    assert can_use_llm() is False
