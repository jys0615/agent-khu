import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    """
    Session-scoped TestClient. External services (Redis, Elasticsearch, RAG)
    fail silently via try/except lifespan blocks — no mocking required.
    Required env: ANTHROPIC_API_KEY, DATABASE_URL=sqlite:///./test.db
    """
    from app.main import app
    with TestClient(app) as c:
        yield c
