from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int = Field(default=900, description="Access token TTL, seconds")


class EmailCodeRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    captcha_token: str | None = None


class EmailCodeVerify(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=12)


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    consent_accepted: bool = True


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=72)


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    display_name: str | None = None
    is_admin: bool = False
    subscription_type: str
    subscription_until: datetime | None = None
    analysis_count: int
    consent_at: datetime | None
    consent_version: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentResponse(BaseModel):
    id: int
    amount_kopecks: int
    plan: str
    period_months: int
    status: str
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ResumeCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    original_text: str = Field(min_length=20)


class ResumeResponse(BaseModel):
    id: int
    title: str
    original_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class VacancyCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    vacancy_text: str = Field(min_length=20)


class VacancyResponse(BaseModel):
    id: int
    title: str
    vacancy_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisCreateRequest(BaseModel):
    resume_id: int | None = None
    vacancy_id: int | None = None
    resume_text: str | None = None
    vacancy_text: str
    anonymous_id: str | None = None


# ── Структурированный документ резюме (для редактора и красивого PDF) ─────────
class ResumeContacts(BaseModel):
    email: str = ""
    phone: str = ""
    location: str = ""
    website: str = ""


class ResumeExperience(BaseModel):
    company: str = ""
    role: str = ""
    period: str = ""
    location: str = ""
    bullets: list[str] = Field(default_factory=list)


class ResumeEducation(BaseModel):
    institution: str = ""
    degree: str = ""
    period: str = ""


class ResumeDocument(BaseModel):
    full_name: str = ""
    headline: str = ""
    photo: str | None = None  # data URL (base64) — добавляется пользователем
    contacts: ResumeContacts = Field(default_factory=ResumeContacts)
    summary: str = ""
    experience: list[ResumeExperience] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    education: list[ResumeEducation] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


class AnalysisDocumentUpdate(BaseModel):
    resume_document: ResumeDocument
    cover_letter: str | None = None


class AnalysisResponse(BaseModel):
    id: int | None = None
    score: int
    matched_skills: list[str]
    missing_skills: list[str]
    improved_resume: str
    cover_letter: str
    resume_document: ResumeDocument | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
