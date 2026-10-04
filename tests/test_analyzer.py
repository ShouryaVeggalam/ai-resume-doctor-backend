from app.services.analyzer import analyze, extract_job_keywords, find_skills


def test_skill_detection_and_gaps():
    resume = "Python FastAPI PostgreSQL Git GitHub machine learning"
    jd = "Requirements: Python, FastAPI, AWS, Docker, Kubernetes, PostgreSQL, CI/CD"
    result = analyze(resume, jd)
    assert "python" in result.matched_skills
    assert "aws" in [x.name for x in result.missing_skills]
    assert result.ats_score < 100


def test_generic_keywords_are_filtered():
    keywords = extract_job_keywords("Strong software engineer experience using Python and AWS", {"python", "aws"})
    assert "python" in keywords
    assert "aws" in keywords
    assert "strong" not in keywords
    assert "software" not in keywords
    assert "experience" not in keywords


def test_aliases():
    skills = find_skills("Built REST APIs with continuous integration and delivery")
    assert "rest api" in skills
    assert "ci/cd" in skills
