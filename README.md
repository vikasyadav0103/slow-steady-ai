# Slow & Steady AI

An open-source productivity assistant that summarizes text with an open-weight sequence-to-sequence model, extracts action-item candidates, and detects repeated sentences. The public API uses Java 21 and Spring Boot; a Python FastAPI service calls Hugging Face Inference.

## Architecture
Client -> Spring Boot API (:8080) -> Python FastAPI (:8000) -> Hugging Face Inference API -> open model

## Open innovation
The summarization model is configurable with `HF_MODEL` and defaults to `sshleifer/distilbart-cnn-12-6`, an openly published DistilBART model. Model availability, terms, and license should be verified on its Hugging Face model card before use. The app does not claim that the model weights are hosted locally: inference is performed by Hugging Face's hosted inference service. The app's API and orchestration code are MIT-licensed.

## Project layout
- `spring-api/` — public REST API and orchestration
- `ai-service/` — model-backed summarization, action-item candidates, duplicate detection

## Local development
Requirements: Java 21+, Maven 3.9+, Python 3.11+.

Set an inference token in your environment before starting the Python service:
```bash
export HF_TOKEN=your_hugging_face_access_token
# Optional: choose another compatible summarization model
export HF_MODEL=sshleifer/distilbart-cnn-12-6
```

Start the AI service:
```bash
cd ai-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Start the Spring API in a second terminal:
```bash
cd spring-api
mvn spring-boot:run
```

Test the API:
```bash
curl -X POST http://localhost:8080/api/v1/analyze -H 'Content-Type: application/json' -d '{"text":"The team will review the launch plan on Tuesday. Maya must send the revised budget by Friday. We will measure adoption after launch. The team will review the launch plan on Tuesday."}'
```

## Configuration
- Spring Boot: `AI_SERVICE_URL` (default `http://localhost:8000`)
- Python: `HF_TOKEN` is required for model inference; configure it as a secret, never commit it.
- Python: `HF_MODEL` optionally selects the Hugging Face model identifier.

## Deployment on Render
Deploy `ai-service` and `spring-api` as separate Docker web services from this repository. Set the service root directory to the respective folder. Configure `HF_TOKEN` (secret) on the Python service and `AI_SERVICE_URL` on the Spring service to the Python service's internal URL. Use `/health` and `/actuator/health` for health checks respectively. Verify logs, networking, model availability, and request latency before sharing a demo URL.

## Limitations and safety
Action items are heuristic candidates, not verified facts. Hosted inference sends submitted text to the configured inference provider; do not send confidential text to a public deployment. Add authentication, rate limits, and strict quotas before production use.

## License
MIT — see LICENSE.
