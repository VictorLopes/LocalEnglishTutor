import sys
import os
import io
import pytest

# Make src importable without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """Database backed by a temp file so tests are isolated."""
    import database
    monkeypatch.setattr(database, 'get_data_path', lambda path='': str(tmp_path / path))
    db = database.Database()
    yield db
    db.conn.close()


@pytest.fixture(autouse=True)
def reset_logger_singleton():
    """Each test gets a fresh Logger singleton."""
    from logger_util import Logger
    Logger._instance = None
    yield
    Logger._instance = None


@pytest.fixture(scope="session")
def ollama_available():
    """Session-scoped check: skip integration tests when Ollama is down."""
    try:
        import ollama
        ollama.list()
    except Exception as exc:
        pytest.skip(f"Ollama not reachable — skipping integration tests ({exc})")
