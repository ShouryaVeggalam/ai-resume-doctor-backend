from app.services.optimizer import _deterministic_optimize
from app.schemas import AnalysisResponse


def baseline():
    return AnalysisResponse(
        match_score=70, ats_score=86, skills_match=65, experience_match=70, keyword_match=68,
        matched_skills=["python"],
        missing_skills=[{"name":"aws","importance":"High","reason":"Not demonstrated."}],
        keyword_analysis={"matched":["python"],"missing":["aws"]},
        ats_checks=[],
        recommendations=[{
            "problem":"Weak bullet", "why_it_matters":"Impact is clearer.",
            "before":"Worked on a project.", "after":"Describe the real technology and outcome without inventing facts."
        }],
        summary="test", engine="deterministic"
    )


def test_optimizer_never_changes_resume_in_fallback():
    resume = "Worked on a project."
    result = _deterministic_optimize(resume, baseline())
    assert result.optimized_resume == resume
    assert result.engine == "deterministic"
    assert result.changes[0].requires_user_confirmation is True
