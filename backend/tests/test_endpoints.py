"""
API endpoint and unit tests for Agent KHU.

Local run:
  ANTHROPIC_API_KEY=test DATABASE_URL=sqlite:///./test.db \
  pytest tests/test_endpoints.py -v
"""
import pytest
from app.question_classifier import QuestionClassifier


# ── HTTP endpoint tests ─────────────────────────────────────────

def test_ready_endpoint(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True


def test_health_endpoint_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_returns_401_for_unknown_user(client):
    """Unknown student_id must return 401, not 500."""
    response = client.post(
        "/api/auth/login",
        data={"username": "2021000001", "password": "wrongpassword"},
    )
    assert response.status_code == 401


# ── QuestionClassifier unit tests ───────────────────────────────

@pytest.fixture(scope="module")
def classifier():
    return QuestionClassifier()


def test_classifier_simple_query(classifier):
    assert classifier.classify("자료구조 몇 학점이야?") == "simple"


def test_classifier_complex_query(classifier):
    assert classifier.classify("어떤 전공선택 과목을 들으면 좋을까?") == "complex"


def test_classifier_length_heuristic(classifier):
    """Questions longer than 50 chars default to complex."""
    assert classifier.classify("a" * 51) == "complex"
