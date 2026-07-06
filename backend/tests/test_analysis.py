import pytest


async def register(client, email: str = "user@example.com", password: str = "strongpass123") -> str:
    response = await client.post("/api/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_authenticated_analysis_flow(client) -> None:
    token = await register(client)
    headers = {"Authorization": f"Bearer {token}"}

    resume = await client.post(
        "/api/resumes",
        headers=headers,
        json={"title": "Backend Engineer", "original_text": "Python FastAPI PostgreSQL Docker Redis Git"},
    )
    assert resume.status_code == 201, resume.text

    vacancy = await client.post(
        "/api/vacancies",
        headers=headers,
        json={"title": "Python Engineer", "vacancy_text": "We need Python FastAPI PostgreSQL Docker Kubernetes CI/CD"},
    )
    assert vacancy.status_code == 201, vacancy.text

    analysis = await client.post(
        "/api/analysis",
        headers=headers,
        json={"resume_id": resume.json()["id"], "vacancy_id": vacancy.json()["id"], "vacancy_text": "placeholder"},
    )
    assert analysis.status_code == 200, analysis.text
    payload = analysis.json()
    assert payload["score"] == 67
    assert "kubernetes" in payload["missing_skills"]


@pytest.mark.asyncio
async def test_anonymous_analysis_limit(client) -> None:
    payload = {
        "resume_text": "Python FastAPI PostgreSQL",
        "vacancy_text": "Python FastAPI PostgreSQL Docker",
        "anonymous_id": "demo-user",
    }
    first = await client.post("/api/analysis", json=payload)
    assert first.status_code == 200, first.text

    second = await client.post("/api/analysis", json=payload)
    assert second.status_code == 402
    assert second.json()["detail"] == "Требуется подписка."
