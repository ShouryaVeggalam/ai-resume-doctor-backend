import json
import httpx

from app.config import settings
from app.schemas import AnalysisResponse, ImproveResponse, OptimizeResponse


def _extract_json(content: str) -> dict:
    """Parse strict JSON even if a provider wraps it in a markdown fence."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content
        if content.endswith("```"):
            content = content[:-3]
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        start, end = content.find("{"), content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start:end + 1])
        raise


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }


async def enhance_with_llm(resume: str, jd: str, baseline: AnalysisResponse) -> AnalysisResponse:
    if not settings.llm_api_key:
        return baseline

    prompt = f"""
You are an expert resume reviewer. Analyze the candidate resume against the job description.
Use the deterministic analysis as factual constraints. Never invent a skill, employer, metric,
certification, technology, or experience. If a skill is not supported by the resume, call it
missing/not demonstrated. Return ONLY valid JSON matching the provided schema.

DETERMINISTIC BASELINE:
{baseline.model_dump_json()}

RESUME:
{resume[:50000]}

JOB DESCRIPTION:
{jd[:30000]}

Return JSON with these fields:
match_score, ats_score, skills_match, experience_match, keyword_match, matched_skills,
missing_skills, keyword_analysis, ats_checks, recommendations, summary.
Keep recommendations actionable and evidence-based. Do not tell the user to add a skill they do not have.
"""
    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": settings.llm_model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You output strict JSON only."},
            {"role": "user", "content": prompt},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(url, headers=_headers(), json=payload)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = _extract_json(content)
            parsed["engine"] = "llm"
            return AnalysisResponse.model_validate(parsed)
    except Exception:
        return baseline


async def improve_with_llm(text: str, context: str = "") -> ImproveResponse | None:
    prompt = f"""
Improve this resume bullet or summary for a specific job.
Never invent metrics, tools, responsibilities, employers, or achievements.
Keep facts intact. Make the language concise, specific, and achievement-oriented.
Return ONLY JSON: {{"original":"...","improved":"...","rationale":"..."}}

TEXT:
{text[:8000]}

JOB CONTEXT:
{context[:12000]}
"""
    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": settings.llm_model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You output strict JSON only."},
            {"role": "user", "content": prompt},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=_headers(), json=payload)
            response.raise_for_status()
            parsed = _extract_json(response.json()["choices"][0]["message"]["content"])
            return ImproveResponse(
                original=parsed["original"],
                improved=parsed["improved"],
                rationale=parsed["rationale"],
                engine="llm",
            )
    except Exception:
        return None

async def optimize_with_llm(resume: str, jd: str, baseline: AnalysisResponse) -> OptimizeResponse | None:
    """Generate a reviewable optimized resume without inventing unsupported facts."""
    prompt = f"""
You are a conservative senior resume editor. Produce a proposed optimized resume using ONLY facts
explicitly supported by the candidate resume. The optimized resume must not invent or guess:
- metrics, percentages, user counts, revenue, performance results
- employers, job titles, dates, degrees, certifications
- technologies, cloud platforms, tools, responsibilities, awards
- projects or achievements

If a stronger bullet needs information that is absent, preserve the original fact and write a
reviewable suggestion that asks the candidate to supply the missing fact. Never insert fake numbers.
Do not add missing job skills merely to increase ATS score. A missing skill must remain missing unless
the resume already provides evidence for it.

Preserve the candidate's actual structure and facts. Improve clarity, action language, keyword alignment
where supported, and concision. Return ONLY valid JSON with this shape:
{{
  "optimized_resume": "full proposed resume text",
  "changes": [
    {{"section":"...","original":"...","suggested":"...","reason":"...","requires_user_confirmation":true}}
  ],
  "warnings": ["..."],
  "summary": "..."
}}

DETERMINISTIC ANALYSIS:
{baseline.model_dump_json()}

RESUME:
{resume[:50000]}

JOB DESCRIPTION:
{jd[:30000]}
"""
    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": settings.llm_model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You output strict JSON only and never fabricate resume facts."},
            {"role": "user", "content": prompt},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=_headers(), json=payload)
            response.raise_for_status()
            parsed = _extract_json(response.json()["choices"][0]["message"]["content"])
            parsed["engine"] = "llm"
            return OptimizeResponse.model_validate(parsed)
    except Exception:
        return None
