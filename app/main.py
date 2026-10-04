from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import AnalysisResponse, ImproveRequest, ImproveResponse, OptimizeResponse
from app.services.analyzer import analyze
from app.services.document_parser import extract_text
from app.services.llm import enhance_with_llm
from app.services.improver import improve
from app.services.optimizer import optimize_resume

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": settings.app_name}


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    use_llm: bool = Form(True),
) -> AnalysisResponse:
    if len(job_description.strip()) < 50:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Job description is too short. Provide at least 50 characters.")

    resume_text = await extract_text(resume, settings.max_file_size_mb)
    baseline = analyze(resume_text, job_description)
    if use_llm:
        return await enhance_with_llm(resume_text, job_description, baseline)
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
    if len(job_description.strip()) < 50:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Job description is too short. Provide at least 50 characters.")

    resume_text = await extract_text(resume, settings.max_file_size_mb)
    baseline = analyze(resume_text, job_description)
    return await optimize_resume(resume_text, job_description, baseline, use_llm)
