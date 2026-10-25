import os
import re
from collections import Counter

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Slow & Steady AI", version="0.2.0")

HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "sshleifer/distilbart-cnn-12-6")
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{HF_MODEL}"


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=20, max_length=20000)
    max_sentences: int = Field(default=3, ge=1, le=8)


class AnalyzeResponse(BaseModel):
    summary: str
    action_items: list[str]
    duplicate_sentence_count: int
    mode: str


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


async def summarize_with_open_model(text: str, max_sentences: int) -> str:
    """Summarize through Hugging Face Inference using an open model."""
    if not HF_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Model inference is not configured. Set the HF_TOKEN environment variable.",
        )
    payload = {
        "inputs": text,
        "parameters": {
            "max_length": min(180, max(40, max_sentences * 45)),
            "min_length": 10,
            "do_sample": False,
        },
        "options": {"wait_for_model": True},
    }
    try:
        async with httpx.AsyncClient(timeout=75.0) as client:
            response = await client.post(
                HF_API_URL,
                headers={"Authorization": f"Bearer {HF_TOKEN}"},
                json=payload,
            )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as exc:
        # Do not leak provider response bodies or credentials to callers.
        raise HTTPException(
            status_code=502,
            detail=f"Open model inference failed (provider status {exc.response.status_code}).",
        ) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Open model inference request failed.") from exc

    if isinstance(data, list) and data and isinstance(data[0], dict):
        summary = data[0].get("summary_text")
        if isinstance(summary, str) and summary.strip():
            return summary.strip()
    raise HTTPException(status_code=502, detail="Open model returned an unexpected response.")


def extract_action_items(sentences: list[str]) -> list[str]:
    patterns = re.compile(
        r"\b(must|should|need to|needs to|will|please|action item|follow up|send|review|complete|prepare|submit)\b",
        re.IGNORECASE,
    )
    return [sentence for sentence in sentences if patterns.search(sentence)][:10]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    sentences = split_sentences(request.text)
    normalized = [re.sub(r"\W+", " ", s.lower()).strip() for s in sentences]
    duplicates = sum(count - 1 for count in Counter(normalized).values() if count > 1)
    summary = await summarize_with_open_model(request.text, request.max_sentences)
    return AnalyzeResponse(
        summary=summary,
        action_items=extract_action_items(sentences),
        duplicate_sentence_count=duplicates,
        mode=f"huggingface:{HF_MODEL}",
    )
