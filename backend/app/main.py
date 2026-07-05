from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# import app.core.config первым — он вызывает authbilling.configure(settings).
from app.core.config import get_settings

settings = get_settings()

from app.api.routers import analysis, auth, payments, resumes, vacancies  # noqa: E402

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# auth/payments роутеры уже содержат префикс (/api/auth, /api/payments) от фабрик.
app.include_router(auth.router)
app.include_router(payments.router)
app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
app.include_router(vacancies.router, prefix="/api/vacancies", tags=["vacancies"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])


@app.get("/api/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
