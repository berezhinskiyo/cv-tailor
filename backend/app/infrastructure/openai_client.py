from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from app.core.config import get_settings

settings = get_settings()


@dataclass
class AiGenerationResult:
    improved_resume: str
    cover_letter: str


class OpenAIGenerator:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def generate(self, *, resume_text: str, vacancy_text: str, matched_skills: list[str], missing_skills: list[str]) -> AiGenerationResult:
        if self.client is None:
            return self._fallback(resume_text, vacancy_text, matched_skills, missing_skills)

        system_prompt = (
            "Ты HR и карьерный консультант. Улучши резюме под вакансию, не придумывая опыт, "
            "усиль существующие формулировки и сделай текст привлекательнее для ATS. "
            "Верни два блока с заголовками IMPROVED_RESUME и COVER_LETTER."
        )
        user_prompt = (
            f"Резюме:\n{resume_text}\n\n"
            f"Вакансия:\n{vacancy_text}\n\n"
            f"Совпадающие навыки: {', '.join(matched_skills) or 'нет'}\n"
            f"Отсутствующие навыки: {', '.join(missing_skills) or 'нет'}"
        )
        response = self.client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = response.output_text
        improved_resume, cover_letter = self._split_sections(text)
        return AiGenerationResult(improved_resume=improved_resume, cover_letter=cover_letter)

    def _fallback(self, resume_text: str, vacancy_text: str, matched_skills: list[str], missing_skills: list[str]) -> AiGenerationResult:
        improved_resume = (
            "ПРОФЕССИОНАЛЬНЫЙ ПРОФИЛЬ\n"
            f"Кандидат с релевантным опытом в областях: {', '.join(matched_skills) or 'базовая инженерная практика'}.\n\n"
            "АКЦЕНТЫ ДЛЯ ВАКАНСИИ\n"
            f"- Подтвержденный опыт: {', '.join(matched_skills) or 'не указан явно'}.\n"
            f"- Зоны развития: {', '.join(missing_skills) or 'критичных пробелов не обнаружено'}.\n\n"
            "ОБНОВЛЕННАЯ ВЕРСИЯ РЕЗЮМЕ\n"
            f"{resume_text.strip()}\n\n"
            "Рекомендация: добавьте измеримые результаты и формулировки, связанные с требованиями вакансии:\n"
            f"{vacancy_text[:450].strip()}..."
        )
        cover_letter = (
            "Здравствуйте!\n\n"
            "Меня заинтересовала ваша вакансия. Мой опыт хорошо соотносится с задачами роли, "
            f"особенно в направлениях: {', '.join(matched_skills) or 'разработка и delivery'}.\n"
            "Я внимательно отношусь к качеству решений, умею быстро встраиваться в продуктовый контекст "
            "и усиливать существующие процессы.\n"
        )
        if missing_skills:
            cover_letter += (
                f"Также вижу области роста: {', '.join(missing_skills)}. "
                "Готов быстро закрыть эти пробелы за счет релевантной инженерной базы.\n"
            )
        cover_letter += "\nБуду рад обсудить, как смогу быть полезен вашей команде."
        return AiGenerationResult(improved_resume=improved_resume, cover_letter=cover_letter)

    @staticmethod
    def _split_sections(text: str) -> tuple[str, str]:
        if "COVER_LETTER" in text and "IMPROVED_RESUME" in text:
            _, tail = text.split("IMPROVED_RESUME", 1)
            improved_part, cover_part = tail.split("COVER_LETTER", 1)
            return improved_part.strip(), cover_part.strip()
        return text.strip(), "Сопроводительное письмо не было выделено моделью отдельно."

