import re
from app.config import settings
from app.schemas import ImproveResponse
from app.services.llm import improve_with_llm


def deterministic_improve(text: str, context: str = "") -> ImproveResponse:
    original = text.strip()
    improved = original

    replacements = [
        (r"(?i)^worked on\s+", "Developed "),
        (r"(?i)^helped with\s+", "Contributed to "),
        (r"(?i)^responsible for\s+", "Managed "),
        (r"(?i)^participated in\s+", "Collaborated on "),
    ]
    for pattern, replacement in replacements:
        improved = re.sub(pattern, replacement, improved)
        if improved != original:
            break

    if improved == original:
        improved = original.rstrip(".") + ". Quantify the scale, technology, and measurable outcome where the evidence supports it."
        rationale = "The bullet already uses reasonably specific language; add evidence of scale or measurable impact rather than inventing metrics."
    else:
        rationale = "Replaced generic responsibility language with stronger ownership language. Add technology and measurable outcomes only when they are true."

    return ImproveResponse(original=original, improved=improved, rationale=rationale, engine="deterministic")


async def improve(text: str, context: str = "", use_llm: bool = True) -> ImproveResponse:
    if use_llm and settings.llm_api_key:
        result = await improve_with_llm(text, context)
        if result:
            return result
    return deterministic_improve(text, context)
