from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import analysis, auth, resumes, vacancies
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
app.include_router(vacancies.router, prefix="/api/vacancies", tags=["vacancies"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

