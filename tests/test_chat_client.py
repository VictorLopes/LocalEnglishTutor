"""Unit tests for ChatClient — ollama is fully mocked."""
import pytest
from unittest.mock import patch, MagicMock


def _make_client(model="test-model", system_prompt=None):
    from chat_client import ChatClient
    return ChatClient(model=model, system_prompt=system_prompt)


def _ollama_response(text):
    return {"message": {"content": text}}


# ---------------------------------------------------------------------------
# clean_text
# ---------------------------------------------------------------------------

def test_clean_text_removes_bold_markers():
    client = _make_client()
    assert client.clean_text("**hello** world") == "hello world"


def test_clean_text_removes_italic_markers():
    client = _make_client()
    assert client.clean_text("*hello*") == "hello"


def test_clean_text_removes_non_ascii():
    client = _make_client()
    result = client.clean_text("Hello \U0001F600 world")
    assert "\U0001F600" not in result
    assert "Hello" in result


def test_clean_text_strips_whitespace():
    client = _make_client()
    assert client.clean_text("  hello  ") == "hello"


def test_clean_text_combined():
    client = _make_client()
    result = client.clean_text("  **Great** \U0001F44D job!  ")
    assert result == "Great  job!"


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def test_default_model_from_config():
    from chat_client import ChatClient
    client = ChatClient()
    assert client.model == "sam860/lfm2.5:1.2b"


def test_explicit_model_overrides_config():
    client = _make_client(model="llama3")
    assert client.model == "llama3"


def test_system_prompt_added_to_messages():
    client = _make_client(system_prompt="You are a tutor.")
    assert client.messages[0] == {"role": "system", "content": "You are a tutor."}


def test_no_system_prompt_means_empty_history():
    client = _make_client()
    assert client.messages == []


# ---------------------------------------------------------------------------
# set_system_prompt / clear_history
# ---------------------------------------------------------------------------

def test_set_system_prompt_clears_history():
    client = _make_client()
    client.messages.append({"role": "user", "content": "old"})
    client.set_system_prompt("B2", "Technology")
    assert len(client.messages) == 1
    assert client.messages[0]["role"] == "system"
    assert "B2" in client.messages[0]["content"]
    assert "Technology" in client.messages[0]["content"]


def test_clear_history_keeps_system_prompt():
    client = _make_client(system_prompt="Be helpful.")
    client.messages.append({"role": "user", "content": "hi"})
    client.clear_history()
    assert client.messages == [{"role": "system", "content": "Be helpful."}]


def test_clear_history_without_system_prompt():
    client = _make_client()
    client.messages.append({"role": "user", "content": "hi"})
    client.clear_history()
    assert client.messages == []


# ---------------------------------------------------------------------------
# load_history
# ---------------------------------------------------------------------------

def test_load_history_maps_ai_sender():
    client = _make_client(system_prompt="Tutor.")
    db_rows = [("Hello", "ai"), ("Hi back", "user")]
    client.load_history(db_rows)
    # system prompt + 2 messages
    assert len(client.messages) == 3
    assert client.messages[1] == {"role": "assistant", "content": "Hello"}
    assert client.messages[2] == {"role": "user", "content": "Hi back"}


# ---------------------------------------------------------------------------
# get_initial_greeting
# ---------------------------------------------------------------------------

def test_get_initial_greeting_returns_cleaned_text():
    client = _make_client(system_prompt="Be a tutor.")
    with patch('chat_client.ollama.chat', return_value=_ollama_response("**Hello!**")):
        reply = client.get_initial_greeting()
    assert reply == "Hello!"


def test_get_initial_greeting_appends_to_history():
    client = _make_client(system_prompt="Tutor.")
    with patch('chat_client.ollama.chat', return_value=_ollama_response("Hi!")):
        client.get_initial_greeting()
    assert any(m["role"] == "assistant" for m in client.messages)


def test_get_initial_greeting_connection_error():
    client = _make_client()
    with patch('chat_client.ollama.chat', side_effect=Exception("connection refused")):
        reply = client.get_initial_greeting()
    assert "ollama" in reply.lower() or "error" in reply.lower()


def test_get_initial_greeting_model_not_found_triggers_pull():
    client = _make_client()
    success_response = _ollama_response("Hello after pull!")
    with patch('chat_client.ollama.chat', side_effect=[Exception("404 not found"), success_response]) as mock_chat, \
         patch('chat_client.ollama.pull') as mock_pull:
        reply = client.get_initial_greeting()
    mock_pull.assert_called_once()
    assert reply == "Hello after pull!"


# ---------------------------------------------------------------------------
# get_response
# ---------------------------------------------------------------------------

def test_get_response_returns_cleaned_text():
    client = _make_client(system_prompt="Tutor.")
    with patch('chat_client.ollama.chat', return_value=_ollama_response("*Good* answer!")):
        reply = client.get_response("Tell me about food.")
    assert reply == "Good answer!"


def test_get_response_appends_user_and_assistant_to_history():
    client = _make_client(system_prompt="Tutor.")
    with patch('chat_client.ollama.chat', return_value=_ollama_response("Nice!")):
        client.get_response("Hello")
    roles = [m["role"] for m in client.messages]
    assert "user" in roles
    assert "assistant" in roles


def test_get_response_error_returns_message():
    client = _make_client()
    with patch('chat_client.ollama.chat', side_effect=Exception("timeout")):
        reply = client.get_response("hi")
    assert "error" in reply.lower() or "ollama" in reply.lower()
