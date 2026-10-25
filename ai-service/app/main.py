import re
from collections import Counter

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Slow & Steady AI", version="0.1.0")


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


def summarize(text: str, max_sentences: int) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return ""
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    frequencies = Counter(words)
    ranked = sorted(
        enumerate(sentences),
        key=lambda pair: (
            sum(frequencies[w] for w in re.findall(r"\b[a-zA-Z]{3,}\b", pair[1].lower()))
            / max(len(pair[1].split()), 1),
            -pair[0],
        ),
        reverse=True,
    )
    chosen = {index for index, _ in ranked[:max_sentences]}
    return " ".join(sentence for index, sentence in enumerate(sentences) if index in chosen)


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
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    sentences = split_sentences(request.text)
    normalized = [re.sub(r"\W+", " ", s.lower()).strip() for s in sentences]
    duplicates = sum(count - 1 for count in Counter(normalized).values() if count > 1)
    return AnalyzeResponse(
        summary=summarize(request.text, request.max_sentences),
        action_items=extract_action_items(sentences),
        duplicate_sentence_count=duplicates,
        mode="extractive",
    )
