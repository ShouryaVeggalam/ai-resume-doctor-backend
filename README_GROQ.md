# Groq setup

This version uses Groq's OpenAI-compatible Chat Completions endpoint.

## Environment

Create `.env`:

```env
APP_NAME=AI Resume Doctor API
CORS_ORIGINS=http://localhost:3000
MAX_FILE_SIZE_MB=5
LLM_BASE_URL=https://api.groq.com/openai/v1
GROQ_API_KEY=gsk_...
LLM_MODEL=openai/gpt-oss-120b
```

Never commit `.env` or expose the API key in the frontend.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
```

Use `/docs` to test `use_llm=true`.

If the Groq request fails, the API safely falls back to the deterministic engine.
