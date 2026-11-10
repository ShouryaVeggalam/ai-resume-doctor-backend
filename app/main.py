from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import AnalysisResponse, ImproveRequest, ImproveResponse, OptimizeResponse
from app.services.analyzer import analyze
from app.services.document_parser import extract_text
from app.services.llm import enhance_with_llm
from app.services.improver import improve
from app.services.optimizer import optimize_resume

app = FastAPI(title=settings.app_name, version="1.0.1")

cors_origins = [origin.strip().rstrip("/") for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/")
async def root() -> dict:
    return {"status": "ok", "service": settings.app_name, "docs": "/docs"}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": settings.app_name}


async def _read_resume_and_validate(resume: UploadFile, job_description: str) -> tuple[str, str]:
    if not job_description or len(job_description.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Job description is too short. Provide at least 50 characters.",
        )
    filename = (resume.filename or "").lower()
    if not filename.endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX resumes are supported.")
    resume_text = await extract_text(resume, settings.max_file_size_mb)
    return resume_text, job_description.strip()


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    use_llm: bool = Form(True),
) -> AnalysisResponse:
    resume_text, jd = await _read_resume_and_validate(resume, job_description)
    baseline = analyze(resume_text, jd)
    if use_llm:
        return await enhance_with_llm(resume_text, jd, baseline)
    return baseline


@app.post("/api/v1/improve", response_model=ImproveResponse)
async def improve_resume(request: ImproveRequest) -> ImproveResponse:
    return await improve(request.text, request.context, request.use_llm)


@app.post("/api/v1/optimize", response_model=OptimizeResponse)
async def optimize_resume_endpoint(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    use_llm: bool = Form(True),
) -> OptimizeResponse:
    resume_text, jd = await _read_resume_and_validate(resume, job_description)
    baseline = analyze(resume_text, jd)
    return await optimize_resume(resume_text, jd, baseline, use_llm)
