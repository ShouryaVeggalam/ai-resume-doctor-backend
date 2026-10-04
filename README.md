# AI Resume Doctor — Backend v2

FastAPI backend for a hackathon MVP that analyzes a resume against a job description and explains **why** the resume may not be shortlisted and **what to improve**.

## What v2 adds

- More realistic ATS scoring (no automatic 100 when meaningful gaps exist)
- Curated job-specific keyword extraction instead of generic-word counting
- Skill aliases (`REST APIs` → `rest api`, CI/CD variants → `ci/cd`)
- Required-vs-preferred style importance detection
- Experience/impact signals and measurable-outcome detection
- Better ATS checks for contact information, section structure, bullets/action language, formatting signals, and keyword alignment
- New `/api/v1/improve` endpoint for bullet/summary improvement
- Optional LLM reasoning layer with deterministic fallback
- Safety rule: never tell candidates to claim skills or achievements they do not actually have

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
python3 -m uvicorn app.main:app --reload --port 8000
```

Docs: http://127.0.0.1:8000/docs

Health: http://127.0.0.1:8000/health

## API

### `POST /api/v1/analyze`

Multipart form:
- `resume`: PDF or DOCX
- `job_description`: text
- `use_llm`: boolean

### `POST /api/v1/improve`

JSON:

```json
{
  "text": "Worked on a machine learning project.",
  "context": "Software Engineer — AI Platform",
  "use_llm": true
}
```

## LLM configuration

The backend supports OpenAI-compatible `/chat/completions` APIs. Set these in `.env`:

```env
LLM_API_KEY=...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=...
```

If no key is provided, the system remains fully usable with the deterministic engine.

## Demo strategy

For a hackathon, demonstrate:

1. Upload a resume.
2. Paste a job description.
3. Show the match score.
4. Show missing skills and why they matter.
5. Show ATS checks.
6. Show a before/after improvement.
7. Explain that the system distinguishes **missing** from **not demonstrated** and never asks a candidate to fake experience.
