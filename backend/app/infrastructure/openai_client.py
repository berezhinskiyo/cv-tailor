from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from openai import OpenAI

from app.core.config import get_settings

settings = get_settings()

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?\d[\d\-\s()]{7,}\d)")
_URL_RE = re.compile(r"(?:https?://|www\.)[^\s,;]+", re.IGNORECASE)


@dataclass
class AiGenerationResult:
    improved_resume: str
    cover_letter: str
    document: dict = field(default_factory=dict)


class OpenAIGenerator:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def generate(
        self,
        *,
        resume_text: str,
        vacancy_text: str,
        matched_skills: list[str],
        missing_skills: list[str],
    ) -> AiGenerationResult:
        if self.client is None:
            return self._fallback(resume_text, vacancy_text, matched_skills, missing_skills)
        try:
            return self._generate_ai(resume_text, vacancy_text, matched_skills, missing_skills)
        except Exception:  # noqa: BLE001 — при любом сбое модели не роняем анализ
            return self._fallback(resume_text, vacancy_text, matched_skills, missing_skills)

    # ── AI ────────────────────────────────────────────────────────────────────
    def _generate_ai(
        self, resume_text: str, vacancy_text: str, matched_skills: list[str], missing_skills: list[str]
    ) -> AiGenerationResult:
        system_prompt = (
            "Ты — карьерный консультант и резюме-райтер. На основе резюме кандидата и текста "
            "вакансии собери УЛУЧШЕННОЕ структурированное резюме под эту вакансию: усиль формулировки, "
            "не выдумывай опыт, подчеркни релевантные навыки, добавь измеримые результаты там, где это "
            "уместно по тексту. Также напиши сопроводительное письмо. "
            "Верни СТРОГО валидный JSON без markdown-обёртки по схеме:\n"
            "{\n"
            '  "full_name": str, "headline": str (желаемая должность),\n'
            '  "contacts": {"email": str, "phone": str, "location": str, "website": str},\n'
            '  "summary": str (3-5 предложений профиля под вакансию),\n'
            '  "experience": [{"company": str, "role": str, "period": str, "location": str, '
            '"bullets": [str, ...]}],\n'
            '  "skills": [str, ...], "education": [{"institution": str, "degree": str, "period": str}],\n'
            '  "languages": [str, ...], "cover_letter": str\n'
            "}\n"
            "Все поля заполняй на языке резюме. Если данных нет — оставляй пустую строку/массив."
        )
        user_prompt = (
            f"Резюме кандидата:\n{resume_text}\n\n"
            f"Вакансия:\n{vacancy_text}\n\n"
            f"Совпадающие навыки: {', '.join(matched_skills) or 'нет'}\n"
            f"Недостающие навыки: {', '.join(missing_skills) or 'нет'}"
        )
        response = self.client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        data = _extract_json(response.output_text)
        cover_letter = (data.pop("cover_letter", "") or "").strip()
        document = _normalize_document(data, resume_text, matched_skills)
        if not cover_letter:
            cover_letter = _fallback_cover_letter(matched_skills, missing_skills)
        return AiGenerationResult(
            improved_resume=_flatten_document(document),
            cover_letter=cover_letter,
            document=document,
        )

    # ── Fallback (без ключа OpenAI) ─────────────────────────────────────────────
    def _fallback(
        self, resume_text: str, vacancy_text: str, matched_skills: list[str], missing_skills: list[str]
    ) -> AiGenerationResult:
        document = _heuristic_document(resume_text, vacancy_text, matched_skills, missing_skills)
        cover_letter = _fallback_cover_letter(matched_skills, missing_skills)
        return AiGenerationResult(
            improved_resume=_flatten_document(document),
            cover_letter=cover_letter,
            document=document,
        )


# ── Хелперы ────────────────────────────────────────────────────────────────────
def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        return json.loads(text[start : end + 1])
    raise ValueError("model returned no JSON")


def _normalize_document(data: dict, resume_text: str, matched_skills: list[str]) -> dict:
    contacts = data.get("contacts") or {}
    if not isinstance(contacts, dict):
        contacts = {}
    fallback_contacts = _extract_contacts(resume_text)
    document = {
        "full_name": str(data.get("full_name") or "").strip(),
        "headline": str(data.get("headline") or "").strip(),
        "photo": None,
        "contacts": {
            "email": str(contacts.get("email") or fallback_contacts["email"]).strip(),
            "phone": str(contacts.get("phone") or fallback_contacts["phone"]).strip(),
            "location": str(contacts.get("location") or "").strip(),
            "website": str(contacts.get("website") or fallback_contacts["website"]).strip(),
        },
        "summary": str(data.get("summary") or "").strip(),
        "experience": _normalize_experience(data.get("experience")),
        "skills": _normalize_str_list(data.get("skills")) or list(matched_skills),
        "education": _normalize_education(data.get("education")),
        "languages": _normalize_str_list(data.get("languages")),
    }
    return document


def _normalize_str_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if str(v).strip()]


def _normalize_experience(value) -> list[dict]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "company": str(item.get("company") or "").strip(),
                "role": str(item.get("role") or "").strip(),
                "period": str(item.get("period") or "").strip(),
                "location": str(item.get("location") or "").strip(),
                "bullets": _normalize_str_list(item.get("bullets")),
            }
        )
    return out


def _normalize_education(value) -> list[dict]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "institution": str(item.get("institution") or "").strip(),
                "degree": str(item.get("degree") or "").strip(),
                "period": str(item.get("period") or "").strip(),
            }
        )
    return out


def _extract_contacts(resume_text: str) -> dict:
    email = _EMAIL_RE.search(resume_text)
    url = _URL_RE.search(resume_text)
    phone = _PHONE_RE.search(resume_text)
    return {
        "email": email.group(0) if email else "",
        "phone": phone.group(0).strip() if phone else "",
        "website": url.group(0) if url else "",
    }


def _heuristic_document(
    resume_text: str, vacancy_text: str, matched_skills: list[str], missing_skills: list[str]
) -> dict:
    lines = [ln.strip() for ln in resume_text.splitlines() if ln.strip()]
    contacts = _extract_contacts(resume_text)

    # Имя — первая «короткая» строка без цифр и @, похожая на ФИО.
    full_name = ""
    for ln in lines[:3]:
        if "@" not in ln and not any(ch.isdigit() for ch in ln) and 1 <= len(ln.split()) <= 4:
            full_name = ln
            break

    # Bullets — содержательные строки/предложения резюме.
    raw_bullets: list[str] = []
    for ln in lines:
        if ln == full_name:
            continue
        for part in re.split(r"(?<=[.!?])\s+|;\s*|•", ln):
            part = part.strip(" -–—\t")
            if len(part) >= 12:
                raw_bullets.append(part[0].upper() + part[1:])
    bullets = raw_bullets[:8] or [resume_text.strip()[:200]]

    summary = (
        "Специалист с релевантным опытом под вакансию. "
        + (f"Сильные стороны: {', '.join(matched_skills[:6])}. " if matched_skills else "")
        + (
            "Готов(а) усилить компетенции в направлениях: " + ", ".join(missing_skills[:4]) + "."
            if missing_skills
            else ""
        )
    ).strip()

    return {
        "full_name": full_name,
        "headline": "",
        "photo": None,
        "contacts": {
            "email": contacts["email"],
            "phone": contacts["phone"],
            "location": "",
            "website": contacts["website"],
        },
        "summary": summary,
        "experience": [{"company": "", "role": "", "period": "", "location": "", "bullets": bullets}],
        "skills": list(matched_skills),
        "education": [],
        "languages": [],
    }


def _fallback_cover_letter(matched_skills: list[str], missing_skills: list[str]) -> str:
    text = (
        "Здравствуйте!\n\n"
        "Меня заинтересовала ваша вакансия — мой опыт хорошо соотносится с задачами роли"
        + (f", особенно в направлениях: {', '.join(matched_skills[:6])}" if matched_skills else "")
        + ".\n\nЯ внимательно отношусь к качеству решений, быстро встраиваюсь в продуктовый контекст "
        "и усиливаю существующие процессы."
    )
    if missing_skills:
        text += (
            f"\n\nВижу зоны роста ({', '.join(missing_skills[:5])}) и готов(а) быстро закрыть их "
            "за счёт сильной инженерной базы."
        )
    text += "\n\nБуду рад(а) обсудить, чем смогу быть полезен(на) вашей команде.\n\nС уважением."
    return text


def _flatten_document(document: dict) -> str:
    """Плоский текст резюме (для текстовой колонки и базового PDF)."""
    parts: list[str] = []
    if document.get("full_name"):
        parts.append(document["full_name"])
    if document.get("headline"):
        parts.append(document["headline"])
    c = document.get("contacts") or {}
    contact_line = " · ".join(v for v in [c.get("email"), c.get("phone"), c.get("location"), c.get("website")] if v)
    if contact_line:
        parts.append(contact_line)
    if document.get("summary"):
        parts.append("\nПРОФИЛЬ\n" + document["summary"])
    if document.get("experience"):
        parts.append("\nОПЫТ")
        for exp in document["experience"]:
            head = " — ".join(v for v in [exp.get("role"), exp.get("company")] if v)
            if exp.get("period"):
                head = f"{head} ({exp['period']})" if head else exp["period"]
            if head:
                parts.append(head)
            for b in exp.get("bullets", []):
                parts.append(f"• {b}")
    if document.get("skills"):
        parts.append("\nНАВЫКИ\n" + ", ".join(document["skills"]))
    if document.get("education"):
        parts.append("\nОБРАЗОВАНИЕ")
        for ed in document["education"]:
            parts.append(" — ".join(v for v in [ed.get("degree"), ed.get("institution"), ed.get("period")] if v))
    if document.get("languages"):
        parts.append("\nЯЗЫКИ\n" + ", ".join(document["languages"]))
    return "\n".join(parts).strip()
