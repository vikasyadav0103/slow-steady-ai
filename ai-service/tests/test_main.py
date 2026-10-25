import pytest
from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_uses_open_model_and_extracts_action_item(monkeypatch):
    async def fake_model_summary(text: str, max_sentences: int) -> str:
        assert "launch plan" in text
        assert max_sentences == 2
        return "The team will review the launch plan. Maya must send the budget."

    monkeypatch.setattr(main, "summarize_with_open_model", fake_model_summary)
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
    assert payload["summary"].startswith("The team")
    assert payload["mode"].startswith("huggingface:")


def test_missing_huggingface_token_returns_service_unavailable(monkeypatch):
    async def no_token(text: str, max_sentences: int) -> str:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Model inference is not configured.")

    monkeypatch.setattr(main, "summarize_with_open_model", no_token)
    response = client.post("/analyze", json={"text": "This is a sufficiently long text for testing."})
    assert response.status_code == 503


def test_rejects_too_short_text():
    response = client.post("/analyze", json={"text": "too short"})
    assert response.status_code == 422
