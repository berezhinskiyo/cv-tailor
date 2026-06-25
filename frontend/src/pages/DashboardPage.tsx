import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { resources } from "../api/resources";
import { useAuth } from "../context/AuthContext";
import { Logo } from "../components/Logo";
import { Footer } from "../components/Footer";
import { Toast } from "../components/Toast";
import { useToast } from "../hooks/useToast";
import { AnalysisResultCard } from "../components/AnalysisResultCard";
import { ResumeEditor } from "../components/ResumeEditor";
import { Analysis, Resume, Vacancy } from "../types";

export function DashboardPage() {
  const { token, user, logout } = useAuth();
  const { toast, showToast, clearToast } = useToast();

  const [resumes, setResumes] = useState<Resume[]>([]);
  const [vacancies, setVacancies] = useState<Vacancy[]>([]);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);

  const [resumeTitle, setResumeTitle] = useState("Senior Backend Engineer");
  const [resumeText, setResumeText] = useState("Python FastAPI PostgreSQL Redis Docker CI/CD");
  const [vacancyTitle, setVacancyTitle] = useState("Platform Engineer");
  const [vacancyText, setVacancyText] = useState("Python FastAPI PostgreSQL Docker Kubernetes CI/CD AWS");

  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null);
  const [selectedVacancyId, setSelectedVacancyId] = useState<number | null>(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState<Analysis | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!token) return;
    Promise.all([resources.listResumes(token), resources.listVacancies(token), resources.listAnalyses(token)])
      .then(([r, v, a]) => {
        setResumes(r);
        setVacancies(v);
        setAnalyses(a);
      })
      .catch((err) => showToast((err as Error).message, "error"));
  }, [token, showToast]);

  const latestAnalysis = useMemo(
    () => selectedAnalysis ?? analyses[0] ?? null,
    [analyses, selectedAnalysis]
  );

  if (!token || !user) return null;

  const createResume = async () => {
    try {
      const created = await resources.createResume(token, { title: resumeTitle, original_text: resumeText });
      setResumes((prev) => [created, ...prev]);
      setSelectedResumeId(created.id);
      showToast("Резюме сохранено");
    } catch (err) {
      showToast((err as Error).message, "error");
    }
  };

  const createVacancy = async () => {
    try {
      const created = await resources.createVacancy(token, { title: vacancyTitle, vacancy_text: vacancyText });
      setVacancies((prev) => [created, ...prev]);
      setSelectedVacancyId(created.id);
      showToast("Вакансия сохранена");
    } catch (err) {
      showToast((err as Error).message, "error");
    }
  };

  const runAnalysis = async () => {
    setBusy(true);
    try {
      const vacancy = vacancies.find((item) => item.id === selectedVacancyId);
      const created = await resources.createAnalysis(
        {
          resume_id: selectedResumeId ?? undefined,
          vacancy_id: selectedVacancyId ?? undefined,
          resume_text: selectedResumeId ? undefined : resumeText,
          vacancy_text: selectedVacancyId ? vacancy?.vacancy_text ?? vacancyText : vacancyText,
        },
        token
      );
      setAnalyses((prev) => [created, ...prev]);
      setSelectedAnalysis(created);
      showToast("Анализ готов");
    } catch (err) {
      showToast((err as Error).message, "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      {toast ? <Toast message={toast.message} kind={toast.kind} onClose={clearToast} /> : null}

      <header className="container nav">
        <Link to="/" className="nav-brand" aria-label="CV Tailor">
          <Logo />
        </Link>
        <div className="nav-links">
          <span className="badge badge-success">{user.subscription_type} · анализов: {user.analysis_count}</span>
          <Link to="/privacy">Конфиденциальность</Link>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => void logout()}>
            Выйти
          </button>
        </div>
      </header>

      <section className="container">
        <div className="cabinet-head">
          <div>
            <h1 style={{ margin: 0 }}>Личный кабинет</h1>
            <p className="muted" style={{ margin: "4px 0 0" }}>
              {user.display_name || user.email}
            </p>
          </div>
        </div>

        <div className="cabinet-grid">
          {/* шаг 1 — резюме */}
          <article className="card card--flat">
            <h2>1 · Резюме</h2>
            <label className="field-label" style={{ marginTop: 12 }}>Название</label>
            <input className="input" value={resumeTitle} onChange={(e) => setResumeTitle(e.target.value)} />
            <label className="field-label" style={{ marginTop: 12 }}>Текст резюме</label>
            <textarea className="textarea" rows={6} value={resumeText} onChange={(e) => setResumeText(e.target.value)} />
            <button className="btn btn-primary" style={{ marginTop: 12 }} onClick={createResume}>
              Сохранить резюме
            </button>
            {resumes.length ? (
              <div className="entity-list" style={{ marginTop: 16 }}>
                {resumes.map((r) => (
                  <div
                    key={r.id}
                    className={`entity-item${selectedResumeId === r.id ? " entity-item--active" : ""}`}
                    onClick={() => setSelectedResumeId(r.id)}
                  >
                    <strong>{r.title}</strong>
                    {selectedResumeId === r.id ? <span className="badge">выбрано</span> : null}
                  </div>
                ))}
              </div>
            ) : null}
          </article>

          {/* шаг 2 — вакансия */}
          <article className="card card--flat">
            <h2>2 · Вакансия</h2>
            <label className="field-label" style={{ marginTop: 12 }}>Название</label>
            <input className="input" value={vacancyTitle} onChange={(e) => setVacancyTitle(e.target.value)} />
            <label className="field-label" style={{ marginTop: 12 }}>Текст вакансии</label>
            <textarea className="textarea" rows={6} value={vacancyText} onChange={(e) => setVacancyText(e.target.value)} />
            <button className="btn btn-primary" style={{ marginTop: 12 }} onClick={createVacancy}>
              Сохранить вакансию
            </button>
            {vacancies.length ? (
              <div className="entity-list" style={{ marginTop: 16 }}>
                {vacancies.map((v) => (
                  <div
                    key={v.id}
                    className={`entity-item${selectedVacancyId === v.id ? " entity-item--active" : ""}`}
                    onClick={() => setSelectedVacancyId(v.id)}
                  >
                    <strong>{v.title}</strong>
                    {selectedVacancyId === v.id ? <span className="badge">выбрано</span> : null}
                  </div>
                ))}
              </div>
            ) : null}
          </article>

          {/* шаг 3 — анализ */}
          <article className="hero-panel">
            <h2 style={{ marginTop: 0, color: "#fff" }}>3 · Анализ</h2>
            <p style={{ opacity: 0.9 }}>
              Выберите сохранённое резюме и вакансию слева либо используйте текст из форм.
            </p>
            <div style={{ display: "grid", gap: 8, fontSize: 14, opacity: 0.92, marginBottom: 16 }}>
              <span>Резюме: {selectedResumeId ? resumes.find((r) => r.id === selectedResumeId)?.title : "текст из формы"}</span>
              <span>Вакансия: {selectedVacancyId ? vacancies.find((v) => v.id === selectedVacancyId)?.title : "текст из формы"}</span>
            </div>
            <button className="btn btn-primary" style={{ width: "100%" }} onClick={runAnalysis} disabled={busy}>
              {busy ? "Анализируем..." : "Запустить анализ"}
            </button>
            <p style={{ fontSize: 13, opacity: 0.8, marginTop: 12 }}>
              После лимита бесплатных анализов можно подключить подписку без изменения структуры кабинета.
            </p>
          </article>
        </div>

        {latestAnalysis ? (
          <div style={{ margin: "28px 0 16px" }}>
            <AnalysisResultCard analysis={latestAnalysis} summaryOnly />
            <div style={{ marginTop: 20 }}>
              <ResumeEditor
                analysis={latestAnalysis}
                token={token}
                notify={showToast}
                onSaved={(updated) => {
                  setSelectedAnalysis(updated);
                  setAnalyses((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
                }}
              />
            </div>
          </div>
        ) : null}
      </section>

      <Footer />
    </div>
  );
}
