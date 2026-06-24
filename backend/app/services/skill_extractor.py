from __future__ import annotations

import re

KNOWN_SKILLS = {
    "python",
    "fastapi",
    "django",
    "flask",
    "java",
    "spring",
    "spring boot",
    "kafka",
    "postgresql",
    "mysql",
    "redis",
    "docker",
    "kubernetes",
    "aws",
    "gcp",
    "azure",
    "react",
    "typescript",
    "javascript",
    "vite",
    "material ui",
    "sql",
    "graphql",
    "rest",
    "git",
    "ci/cd",
    "pytest",
    "celery",
    "rabbitmq",
    "linux",
    "terraform",
    "pandas",
    "numpy",
    "scikit-learn",
    "airflow",
    "nginx",
}


def normalize_skill(skill: str) -> str:
    return re.sub(r"\s+", " ", skill.strip().lower())


def extract_skills(text: str) -> list[str]:
    lowered_text = text.lower()
    found = {skill for skill in KNOWN_SKILLS if skill in lowered_text}
    bullet_candidates = re.findall(r"(?:^|\n)[\-\*\d\.\)\s]*([A-Za-z][A-Za-z0-9/+\-\s]{1,40})", text)
    for candidate in bullet_candidates:
        normalized = normalize_skill(candidate)
        if 2 <= len(normalized) <= 30 and any(char.isalpha() for char in normalized):
            if normalized in KNOWN_SKILLS:
                found.add(normalized)
    return sorted(found)

