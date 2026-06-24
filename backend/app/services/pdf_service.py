from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.domain.schemas import AnalysisResponse


class PdfService:
    def build_analysis_pdf(self, analysis: AnalysisResponse) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("AI Resume Tailor Report", styles["Title"]),
            Spacer(1, 12),
            Paragraph(f"Совпадение: {analysis.score}%", styles["Heading2"]),
            Paragraph(f"Совпавшие навыки: {', '.join(analysis.matched_skills) or 'Нет'}", styles["BodyText"]),
            Paragraph(f"Отсутствующие навыки: {', '.join(analysis.missing_skills) or 'Нет'}", styles["BodyText"]),
            Spacer(1, 12),
            Paragraph("Улучшенное резюме", styles["Heading2"]),
            Paragraph(analysis.improved_resume.replace("\n", "<br/>"), styles["BodyText"]),
            Spacer(1, 12),
            Paragraph("Сопроводительное письмо", styles["Heading2"]),
            Paragraph(analysis.cover_letter.replace("\n", "<br/>"), styles["BodyText"]),
        ]
        doc.build(story)
        return buffer.getvalue()

