# AI Resume Doctor — Hackathon Backend

## Endpoints

- `GET /health` — health check
- `POST /api/v1/analyze` — resume + job diagnosis
- `POST /api/v1/improve` — improve one resume bullet/summary
- `POST /api/v1/optimize` — generate a reviewable full-resume optimization plan

## `/api/v1/optimize`

Multipart form:
- `resume`: PDF/DOCX
- `job_description`: text
- `use_llm`: `true`/`false`

The response contains:
- `optimized_resume`
- `changes[]` with original/suggested/reason
- `warnings[]`
- `summary`
- `engine`

The LLM is instructed to never fabricate metrics, skills, employers, dates, certifications, technologies, or achievements. Changes remain reviewable by the candidate.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
```

Swagger: http://127.0.0.1:8000/docs
