"""Integration tests — require a running Ollama instance.

Run with:  pytest -m integration
Skip with: pytest -m "not integration"
"""
import pytest
import ollama

pytestmark = pytest.mark.integration

MODEL = "sam860/lfm2.5:1.2b"


@pytest.fixture(autouse=True)
def require_ollama(ollama_available):
    """All tests in this module need Ollama reachable."""


# ---------------------------------------------------------------------------
# Connectivity
# ---------------------------------------------------------------------------

def test_ollama_list_returns_response():
    result = ollama.list()
    assert result is not None
    assert "models" in result


def test_ollama_list_is_dict_or_object():
    result = ollama.list()
    # ollama SDK may return a ListResponse object or a dict
    assert hasattr(result, "models") or "models" in result


# ---------------------------------------------------------------------------
# Model availability
# ---------------------------------------------------------------------------

def test_configured_model_is_pulled():
    result = ollama.list()
    models = result.models if hasattr(result, "models") else result.get("models", [])
    names = []
    for m in models:
        name = m.model if hasattr(m, "model") else m.get("name", m.get("model", ""))
        names.append(name)
    pulled = any(MODEL in n or n.startswith(MODEL.split(":")[0]) for n in names)
    assert pulled, (
        f"Model '{MODEL}' is not pulled. "
        f"Run: ollama pull {MODEL}\n"
        f"Available models: {names}"
    )


# ---------------------------------------------------------------------------
# Chat communication via the ollama library
# ---------------------------------------------------------------------------

def test_ollama_chat_returns_content():
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": "Reply with exactly one word: hello"}],
    )
    content = response["message"]["content"] if isinstance(response, dict) else response.message.content
    assert isinstance(content, str)
    assert len(content.strip()) > 0


def test_ollama_chat_response_is_string():
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": "What is 1+1?"}],
    )
    content = response["message"]["content"] if isinstance(response, dict) else response.message.content
    assert isinstance(content, str)


# ---------------------------------------------------------------------------
# ChatClient end-to-end with real Ollama
# ---------------------------------------------------------------------------

def test_chat_client_get_initial_greeting():
    from chat_client import ChatClient
    from prompts import SUBJECT_SYSTEM_PROMPT

    client = ChatClient(model=MODEL)
    client.set_system_prompt("A1", "Greetings")
    reply = client.get_initial_greeting()

    assert isinstance(reply, str)
    assert len(reply.strip()) > 0
    assert "Error" not in reply


def test_chat_client_get_response():
    from chat_client import ChatClient

    client = ChatClient(model=MODEL, system_prompt="You are an English tutor.")
    reply = client.get_response("Say hello in one short sentence.")

    assert isinstance(reply, str)
    assert len(reply.strip()) > 0
    assert "Error" not in reply


def test_chat_client_maintains_history():
    from chat_client import ChatClient

    client = ChatClient(model=MODEL, system_prompt="You are a tutor.")
    client.get_response("My name is Alex.")
    history_before = len(client.messages)
    client.get_response("What is my name?")
    assert len(client.messages) > history_before
