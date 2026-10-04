import re
from app.config import settings
from app.schemas import AnalysisResponse, OptimizeResponse, ResumeChange
from app.services.llm import optimize_with_llm


def _deterministic_optimize(resume: str, baseline: AnalysisResponse) -> OptimizeResponse:
    """Safe fallback: never rewrites factual content; produces an actionable change plan."""
    gaps = ", ".join(x.name for x in baseline.missing_skills[:6]) or "none detected"
    warnings = [
        "AI Resume Doctor does not invent skills, metrics, employers, certifications, or achievements.",
        "Verify every suggested change before using the optimized resume in an application.",
    ]
    changes: list[ResumeChange] = []

    for rec in baseline.recommendations[:5]:
        changes.append(
            ResumeChange(
                section="Resume improvement",
                original=rec.before,
                suggested=rec.after,
                reason=rec.why_it_matters,
                requires_user_confirmation=True,
            )
        )

    summary = (
        f"Prepared a safe improvement plan. The main gaps are: {gaps}. "
        "No factual resume content was automatically fabricated or replaced."
    )
    return OptimizeResponse(
        optimized_resume=resume,
        changes=changes,
        warnings=warnings,
        summary=summary,
        engine="deterministic",
    )


async def optimize_resume(resume: str, jd: str, baseline: AnalysisResponse, use_llm: bool = True) -> OptimizeResponse:
    if use_llm and settings.llm_api_key:
        result = await optimize_with_llm(resume, jd, baseline)
        if result:
            return result
    return _deterministic_optimize(resume, baseline)
