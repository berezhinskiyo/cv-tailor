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
    analysis_count: int
    consent_at: datetime | None
    consent_version: str | None
    created_at: datetime

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


class AnalysisResponse(BaseModel):
    id: int | None = None
    score: int
    matched_skills: list[str]
    missing_skills: list[str]
    improved_resume: str
    cover_letter: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
