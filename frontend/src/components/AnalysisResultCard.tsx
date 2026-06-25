import { Analysis } from "../types";

type Props = {
  analysis: Analysis;
  pdfUrl?: string;
  summaryOnly?: boolean;
};

function scoreClass(score: number): string {
  if (score >= 75) return "score-ring--ok";
  if (score >= 45) return "score-ring--mid";
  return "score-ring--low";
}

export function AnalysisResultCard({ analysis, pdfUrl, summaryOnly }: Props) {
  return (
    <article className="card card--flat">
      <div className="row-between">
        <div className="row-between" style={{ gap: 18 }}>
          <span className={`score-ring ${scoreClass(analysis.score)}`}>{analysis.score}%</span>
          <div>
            <h2 style={{ margin: 0 }}>Совпадение с вакансией</h2>
            <p className="muted" style={{ margin: "4px 0 0" }}>
              {analysis.matched_skills.length} совпавших · {analysis.missing_skills.length} недостающих навыков
            </p>
          </div>
        </div>
        {pdfUrl ? (
          <a href={pdfUrl} target="_blank" rel="noreferrer" className="btn btn-secondary">
            📥 Скачать PDF
          </a>
        ) : null}
      </div>

      <div className="result-block">
        <h3>Совпавшие навыки</h3>
        <div className="chips">
          {analysis.matched_skills.length ? (
            analysis.matched_skills.map((skill) => (
              <span key={skill} className="chip chip--matched">
                {skill}
              </span>
            ))
          ) : (
            <span className="muted">Пока нет совпадений.</span>
          )}
        </div>
      </div>

      <div className="result-block">
        <h3>Недостающие навыки</h3>
        <div className="chips">
          {analysis.missing_skills.length ? (
            analysis.missing_skills.map((skill) => (
              <span key={skill} className="chip chip--missing">
                {skill}
              </span>
            ))
          ) : (
            <span className="muted">Критичных пробелов нет.</span>
          )}
        </div>
      </div>

      {summaryOnly ? null : (
        <>
          <div className="result-block">
            <h3>Улучшенное резюме</h3>
            <div className="result-text">{analysis.improved_resume}</div>
          </div>

          <div className="result-block">
            <h3>Сопроводительное письмо</h3>
            <div className="result-text">{analysis.cover_letter}</div>
          </div>
        </>
      )}
    </article>
  );
}
