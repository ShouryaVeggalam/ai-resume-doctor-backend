import re
from collections import Counter

from app.schemas import AnalysisResponse, AtsCheck, KeywordAnalysis, ResumeRecommendation, SkillGap


# Curated skills/technologies for the hackathon MVP. Add domain-specific skills as needed.
SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "sql", "nosql", "html", "css",
    "react", "next.js", "node.js", "fastapi", "django", "flask", "rest api", "graphql",
    "machine learning", "deep learning", "natural language processing", "nlp", "computer vision",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "aws", "azure", "gcp",
    "docker", "kubernetes", "ci/cd", "continuous integration", "continuous delivery", "git", "github",
    "linux", "mongodb", "postgresql", "mysql", "redis", "firebase", "figma", "agile", "scrum",
    "project management", "excel", "power bi", "tableau", "data analysis", "data science", "api",
    "rest", "terraform", "jenkins", "github actions", "microservices", "unit testing", "pytest",
]

# Canonical names keep the UI clean while aliases improve detection.
ALIASES = {
    "rest": "rest api",
    "rest apis": "rest api",
    "apis": "rest api",
    "continuous integration": "ci/cd",
    "continuous delivery": "ci/cd",
    "github actions": "ci/cd",
    "natural language processing": "nlp",
    "scikit learn": "scikit-learn",
    "node": "node.js",
}

GENERIC_KEYWORDS = {
    "the", "and", "for", "with", "you", "our", "are", "will", "this", "from", "that", "your",
    "have", "has", "their", "they", "who", "what", "where", "when", "into", "using", "used",
    "work", "working", "team", "teams", "strong", "skills", "skill", "experience", "experienced",
    "software", "engineer", "engineering", "developer", "development", "applications", "application",
    "build", "built", "building", "maintain", "maintains", "maintaining", "knowledge", "ability",
    "role", "responsibilities", "requirements", "required", "preferred", "candidate", "company",
    "job", "position", "including", "such", "more", "good", "excellent", "best", "other", "etc",
}

ACTION_VERBS = {
    "built", "developed", "implemented", "designed", "created", "automated", "optimized", "deployed",
    "led", "launched", "integrated", "engineered", "analyzed", "improved", "reduced", "increased",
    "delivered", "architected", "tested", "managed", "migrated", "refactored",
}

SECTION_HEADINGS = {
    "summary": ["summary", "profile", "objective"],
    "experience": ["experience", "work experience", "employment"],
    "education": ["education", "academic background"],
    "skills": ["skills", "technical skills", "technologies"],
    "projects": ["projects", "selected projects"],
    "certifications": ["certifications", "certificates"],
}


def normalize(text: str) -> str:
    text = text.lower().replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()


def contains_term(text: str, term: str) -> bool:
    # Phrase-aware matching prevents e.g. "aws" from matching unrelated words.
    pattern = r"(?<![a-z0-9+#])" + re.escape(term.lower()) + r"(?![a-z0-9+#])"
    return re.search(pattern, text.lower()) is not None


def find_skills(text: str) -> set[str]:
    normalized = normalize(text)
    found = set()
    for skill in SKILLS:
        if contains_term(normalized, skill):
            found.add(ALIASES.get(skill, skill))
    return found


def extract_job_keywords(jd: str, jd_skills: set[str]) -> list[str]:
    """Return meaningful job-specific terms, not generic resume vocabulary."""
    normalized = normalize(jd)
    words = re.findall(r"[a-z][a-z0-9+.#/-]{2,}", normalized)
    counts = Counter(words)

    # Skills are always more useful than generic words.
    result = list(sorted(jd_skills))
    for word, count in counts.most_common(100):
        if word in GENERIC_KEYWORDS or word in result or len(word) < 3:
            continue
        if count >= 2:
            result.append(word)
        if len(result) >= 30:
            break
    return result[:30]


def _importance_for_skill(skill: str, jd: str) -> str:
    text = normalize(jd)
    high_markers = [
        rf"required[^.\n]{{0,80}}{re.escape(skill)}",
        rf"{re.escape(skill)}[^.\n]{{0,80}}required",
        rf"must have[^.\n]{{0,80}}{re.escape(skill)}",
        rf"{re.escape(skill)}[^.\n]{{0,60}}(?:required|must|mandatory)",
    ]
    if any(re.search(pattern, text) for pattern in high_markers):
        return "High"
    # Skills appearing multiple times or near requirements are generally more important.
    if len(re.findall(re.escape(skill), text)) >= 2 or "requirements" in text[:1500]:
        return "High"
    return "Medium"


def _skill_reason(skill: str, jd: str) -> str:
    text = normalize(jd)
    if re.search(rf"(?:required|must have|mandatory)[^.\n]{{0,100}}{re.escape(skill)}", text):
        return "This skill is explicitly presented as a required qualification in the job description."
    if re.search(rf"{re.escape(skill)}[^.\n]{{0,100}}(?:required|must have|mandatory)", text):
        return "The job description explicitly connects this skill to a required qualification."
    return "This skill appears in the job description but was not detected in the resume."


def _experience_score(resume: str, jd: str) -> int:
    text = normalize(resume)
    signals = sum(1 for verb in ACTION_VERBS if contains_term(text, verb))
    project_signals = sum(1 for term in ["experience", "intern", "internship", "project", "work experience"] if contains_term(text, term))
    quantified = len(re.findall(r"\b\d+(?:\.\d+)?%|\b\d+\+|\$\s?\d+|\b\d+\s?(?:users|customers|projects|years|months)\b", text))
    score = 48 + min(25, signals * 3) + min(15, project_signals * 3) + min(12, quantified * 4)

    years = re.findall(r"(\d+(?:\.\d+)?)\+?\s+years?", normalize(jd))
    if years and quantified == 0 and not re.search(r"\b\d+(?:\.\d+)?\+?\s+years?", text):
        score -= 8
    return max(0, min(100, score))


def _has_quantified_impact(resume: str) -> bool:
    return bool(re.search(r"\b\d+(?:\.\d+)?%|\b\d+\+|\$\s?\d+|\b\d+\s?(?:users|customers|projects|years|months)\b", normalize(resume)))


def _section_score(resume: str) -> tuple[int, list[AtsCheck]]:
    text = normalize(resume)
    checks: list[AtsCheck] = []

    contact_ok = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)) and bool(re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", text))
    checks.append(AtsCheck(
        label="Contact information",
        status="pass" if contact_ok else "warning",
        detail="Email and phone details detected." if contact_ok else "Add a clear email address and phone number."
    ))

    heading_hits = sum(1 for variants in SECTION_HEADINGS.values() if any(contains_term(text, h) for h in variants))
    heading_status = "pass" if heading_hits >= 4 else "warning" if heading_hits >= 2 else "fail"
    checks.append(AtsCheck(
        label="Standard section headings",
        status=heading_status,
        detail=f"Detected {heading_hits}/6 common resume section categories."
    ))

    bullets = len(re.findall(r"(?:^|\n)\s*[•●▪*-]\s+", resume))
    action_hits = sum(1 for verb in ACTION_VERBS if contains_term(text, verb))
    bullet_status = "pass" if bullets >= 3 and action_hits >= 2 else "warning" if action_hits >= 1 else "fail"
    checks.append(AtsCheck(
        label="Bullet/action language",
        status=bullet_status,
        detail=f"Detected {action_hits} distinct action verbs and {bullets} bullet markers."
    ))

    formatting_noise = sum(1 for marker in ["tables", "text box", "header", "footer"] if marker in text)
    checks.append(AtsCheck(
        label="ATS-friendly formatting",
        status="warning" if formatting_noise else "pass",
        detail="No obvious ATS-unfriendly formatting signals were detected." if not formatting_noise else "Review complex formatting, tables, text boxes, headers, or footers."
    ))

    return heading_hits, checks


def analyze(resume: str, jd: str) -> AnalysisResponse:
    resume_n = normalize(resume)
    jd_n = normalize(jd)
    resume_skills = find_skills(resume)
    jd_skills = find_skills(jd)

    matched = sorted(resume_skills & jd_skills)
    missing = sorted(jd_skills - resume_skills)
    skill_score = round((len(matched) / len(jd_skills)) * 100) if jd_skills else 50

    keywords = extract_job_keywords(jd, jd_skills)
    matched_keywords = [k for k in keywords if contains_term(resume_n, k)]
    missing_keywords = [k for k in keywords if not contains_term(resume_n, k)]
    keyword_score = round((len(matched_keywords) / len(keywords)) * 100) if keywords else 50

    experience_score = _experience_score(resume, jd)

    _, ats_checks = _section_score(resume)
    # Keyword alignment is an ATS factor, but it is not the whole ATS score.
    keyword_status = "pass" if keyword_score >= 75 else "warning" if keyword_score >= 50 else "fail"
    ats_checks.append(AtsCheck(
        label="Job keyword alignment",
        status=keyword_status,
        detail=f"{keyword_score}% of meaningful job-specific keywords appear in the resume."
    ))

    # Score each check with realistic weights. Missing keywords should prevent a 100 by default.
    status_points = {"pass": 100, "warning": 65, "fail": 30}
    ats_score = round(sum(status_points[c.status] for c in ats_checks) / len(ats_checks))
    if missing_keywords:
        ats_score = min(ats_score, 97)

    match_score = round(skill_score * 0.45 + keyword_score * 0.25 + experience_score * 0.15 + ats_score * 0.15)

    gaps = [
        SkillGap(name=s, importance=_importance_for_skill(s, jd_n), reason=_skill_reason(s, jd_n))
        for s in missing[:12]
    ]

    recommendations: list[ResumeRecommendation] = []
    if missing:
        names = ", ".join(missing[:5])
        recommendations.append(ResumeRecommendation(
            problem="Important job skills are missing or not clearly demonstrated.",
            why_it_matters="Recruiters and ATS systems often screen for role-specific skills before a human review.",
            before=f"The resume does not clearly demonstrate: {names}.",
            after=f"Only add skills you genuinely have. If you have used {', '.join(missing[:3])}, show where, how, and what outcome you achieved. Otherwise, do not add them just to increase the score.",
        ))

    if not _has_quantified_impact(resume):
        recommendations.append(ResumeRecommendation(
            problem="Few measurable outcomes were detected.",
            why_it_matters="Numbers make achievements more credible and help recruiters understand impact quickly.",
            before="Worked on a software project.",
            after="Developed a software project used by 50+ users and reduced processing time by 30%.",
        ))

    # Only suggest rewriting a generic bullet when the resume actually contains one.
    generic_bullet = re.search(r"(?i)(worked on|helped with|responsible for)\s+[^.\n]+", resume)
    if generic_bullet:
        before = generic_bullet.group(0).strip()
        recommendations.append(ResumeRecommendation(
            problem="A resume bullet uses generic language instead of showing ownership and impact.",
            why_it_matters="Action + task + technology + outcome bullets are easier for recruiters to evaluate.",
            before=before,
            after="Developed a specific feature using the relevant technology and quantify the result, scale, or improvement where the evidence exists.",
        ))

    if not recommendations:
        recommendations.append(ResumeRecommendation(
            problem="The resume is well aligned, but it can still be made more specific.",
            why_it_matters="Specific outcomes and role-relevant evidence improve both human and ATS readability.",
            before="Keep generic responsibilities as-is.",
            after="Prioritize measurable outcomes, technologies used, and evidence of ownership in each major bullet.",
        ))

    if match_score >= 85:
        verdict = "Strong match"
    elif match_score >= 70:
        verdict = "Good match with some gaps"
    elif match_score >= 55:
        verdict = "Moderate match"
    else:
        verdict = "Weak match"

    summary = (
        f"Your resume is an estimated {match_score}% match for this role ({verdict}). "
        f"It demonstrates {len(matched)} of {len(jd_skills)} detected role-specific skills. "
        f"The biggest opportunities are to address missing requirements and strengthen evidence of impact."
    )

    return AnalysisResponse(
        match_score=max(0, min(100, match_score)),
        ats_score=ats_score,
        skills_match=skill_score,
        experience_match=experience_score,
        keyword_match=keyword_score,
        matched_skills=matched,
        missing_skills=gaps,
        keyword_analysis=KeywordAnalysis(matched=matched_keywords[:25], missing=missing_keywords[:25]),
        ats_checks=ats_checks,
        recommendations=recommendations[:5],
        summary=summary,
        engine="deterministic",
    )
