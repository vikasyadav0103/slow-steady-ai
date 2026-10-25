from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_extracts_duplicate_and_action_item():
    response = client.post(
        "/analyze",
        json={
            "text": (
                "The team will review the launch plan on Tuesday. "
                "Maya must send the revised budget by Friday. "
                "The team will review the launch plan on Tuesday."
            ),
            "max_sentences": 2,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["duplicate_sentence_count"] == 1
    assert any("Maya" in item for item in payload["action_items"])
    assert payload["summary"]


def test_rejects_too_short_text():
    response = client.post("/analyze", json={"text": "too short"})
    assert response.status_code == 422
