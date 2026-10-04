from typing import Literal
from pydantic import BaseModel, Field


class SkillGap(BaseModel):
    name: str
    importance: Literal["High", "Medium", "Low"]
    reason: str


class KeywordAnalysis(BaseModel):
    matched: list[str] = []
    missing: list[str] = []


class ResumeRecommendation(BaseModel):
    problem: str
    why_it_matters: str
    before: str
    after: str


class AtsCheck(BaseModel):
    label: str
    status: Literal["pass", "warning", "fail"]
    detail: str


class AnalysisResponse(BaseModel):
    match_score: int = Field(ge=0, le=100)
    ats_score: int = Field(ge=0, le=100)
    skills_match: int = Field(ge=0, le=100)
    experience_match: int = Field(ge=0, le=100)
    keyword_match: int = Field(ge=0, le=100)
    matched_skills: list[str]
    missing_skills: list[SkillGap]
    keyword_analysis: KeywordAnalysis
    ats_checks: list[AtsCheck]
    recommendations: list[ResumeRecommendation]
    summary: str
    engine: Literal["deterministic", "llm"]


class ImproveRequest(BaseModel):
    text: str = Field(min_length=10)
    context: str = ""
    use_llm: bool = True


class ImproveResponse(BaseModel):
    original: str
    improved: str
    rationale: str
    engine: Literal["deterministic", "llm"]


class ResumeChange(BaseModel):
    section: str
    original: str
    suggested: str
    reason: str
    requires_user_confirmation: bool = True


class OptimizeResponse(BaseModel):
    optimized_resume: str
    changes: list[ResumeChange]
    warnings: list[str]
    summary: str
    engine: Literal["deterministic", "llm"]
