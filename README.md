# Slow & Steady AI

An open-source productivity assistant that summarizes text, extracts action-item candidates, and detects repeated sentences. The public API uses Java 21 and Spring Boot; a Python FastAPI service handles text analysis.

## Architecture
Client -> Spring Boot API (:8080) -> Python FastAPI (:8000)

## Project layout
- spring-api/ — public REST API and orchestration
- ai-service/ — extractive summarization and heuristic action-item extraction

## Local development
Requirements: Java 21+, Maven 3.9+, Python 3.11+.

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
- Spring Boot: AI_SERVICE_URL (default http://localhost:8000)
- Python: extractive mode by default.

## Deployment
Deploy ai-service and spring-api as separate Render web services. Configure AI_SERVICE_URL in the Spring service to point to the Python service's internal URL. Verify networking, health checks, resource limits, and logs before sharing the demo URL.

## Limitations and safety
Summaries are extractive and action items are heuristic candidates, not verified facts. Do not send confidential text to a public deployment. Add authentication, rate limits, and strict quotas before production use.

## License
MIT — see LICENSE.
