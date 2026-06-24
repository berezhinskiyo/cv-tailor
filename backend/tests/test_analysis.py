def register(client, email: str = "user@example.com", password: str = "strongpass123") -> str:
    response = client.post("/api/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201
    return response.json()["access_token"]


def test_authenticated_analysis_flow(client) -> None:
    token = register(client)
    headers = {"Authorization": f"Bearer {token}"}

    resume = client.post(
        "/api/resumes",
        headers=headers,
        json={"title": "Backend Engineer", "original_text": "Python FastAPI PostgreSQL Docker Redis Git"},
    )
    assert resume.status_code == 201

    vacancy = client.post(
        "/api/vacancies",
        headers=headers,
        json={"title": "Python Engineer", "vacancy_text": "We need Python FastAPI PostgreSQL Docker Kubernetes CI/CD"},
    )
    assert vacancy.status_code == 201

    analysis = client.post(
        "/api/analysis",
        headers=headers,
        json={"resume_id": resume.json()["id"], "vacancy_id": vacancy.json()["id"], "vacancy_text": "placeholder"},
    )
    assert analysis.status_code == 200
    payload = analysis.json()
    assert payload["score"] == 67
    assert "kubernetes" in payload["missing_skills"]


def test_anonymous_analysis_limit(client) -> None:
    payload = {
        "resume_text": "Python FastAPI PostgreSQL",
        "vacancy_text": "Python FastAPI PostgreSQL Docker",
        "anonymous_id": "demo-user",
    }
    first = client.post("/api/analysis", json=payload)
    assert first.status_code == 200

    second = client.post("/api/analysis", json=payload)
    assert second.status_code == 402
    assert second.json()["detail"] == "Требуется подписка."

