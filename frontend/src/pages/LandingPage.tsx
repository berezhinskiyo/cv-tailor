import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { API_URL } from "../api/client";
import { resources } from "../api/resources";
import { useAuth } from "../context/AuthContext";
import { Logo } from "../components/Logo";
import { Footer } from "../components/Footer";
import { HeroArt } from "../components/HeroArt";
import { SmartCaptcha } from "../components/SmartCaptcha";
import { AnalysisResultCard } from "../components/AnalysisResultCard";
import { Analysis } from "../types";

const demoResume =
  "Senior backend engineer. Python, FastAPI, PostgreSQL, Docker, Redis, CI/CD. Строил production-API, повышал надёжность сервисов, менторил инженеров.";
const demoVacancy =
  "Ищем Senior Python Engineer: FastAPI, PostgreSQL, Docker, Kubernetes, CI/CD, AWS. Опыт построения отказоустойчивых сервисов.";

export function LandingPage() {
  const { login, requestRegisterCode, verifyRegisterCode, token } = useAuth();
  const navigate = useNavigate();

  // ── авторизация
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [verificationSent, setVerificationSent] = useState(false);
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [consent, setConsent] = useState(false);
  const [captchaToken, setCaptchaToken] = useState("");

  // ── демо-анализ
  const [resumeText, setResumeText] = useState(demoResume);
  const [vacancyText, setVacancyText] = useState(demoVacancy);
  const [demoResult, setDemoResult] = useState<Analysis | null>(null);
  const [demoError, setDemoError] = useState("");
  const [demoBusy, setDemoBusy] = useState(false);

  const anonymousId = useMemo(() => {
    const key = "cv-tailor-anonymous-id";
    const existing = localStorage.getItem(key);
    if (existing) return existing;
    const created =
      typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}`;
    localStorage.setItem(key, created);
    return created;
  }, []);

  useEffect(() => {
    if (token) navigate("/dashboard", { replace: true });
  }, [token, navigate]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setMessage("");
    try {
      if (mode === "login") {
        await login(email, password);
        return;
      }
      if (!verificationSent) {
        await requestRegisterCode(email, password, captchaToken);
        setVerificationSent(true);
        setMessage("Код отправлен на почту. Введите его для завершения регистрации.");
        return;
      }
      await verifyRegisterCode(email, code);
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  const runDemo = async () => {
    setDemoBusy(true);
    setDemoError("");
    try {
      const result = await resources.demoAnalysis(
        { resume_text: resumeText, vacancy_text: vacancyText, anonymous_id: anonymousId },
        anonymousId
      );
      setDemoResult(result);
    } catch (err) {
      setDemoError((err as Error).message);
    } finally {
      setDemoBusy(false);
    }
  };

  const startOAuth = (provider: "yandex" | "vk") => {
    window.location.href = `${API_URL}/auth/oauth/${provider}/start`;
  };

  return (
    <div>
      <header className="container nav">
        <Link to="/" className="nav-brand" aria-label="CV Tailor">
          <Logo />
        </Link>
        <div className="nav-links">
          <a href="#demo">Демо</a>
          <a href="#features">Возможности</a>
          <a href="#pricing">Тарифы</a>
          <Link to="/contacts">Контакты</Link>
        </div>
      </header>

      <section className="container hero">
        <div>
          <span className="badge">🎯 AI-адаптация резюме под вакансию</span>
          <h1>Резюме, которое отвечает вакансии как коммерческое предложение</h1>
          <p className="muted" style={{ fontSize: 18, maxWidth: 560 }}>
            Вставьте резюме и текст вакансии — получите процент совпадения, карту недостающих
            навыков, переписанное под роль резюме и сопроводительное письмо. Всё в одном потоке.
          </p>
          <div className="hero-cta">
            <a href="#auth" className="btn btn-primary">
              Войти в кабинет
            </a>
            <a href="#demo" className="btn btn-secondary">
              Попробовать демо →
            </a>
          </div>
          <div className="hero-stats">
            <div>
              <strong>10 сек</strong>
              <span>на первый результат</span>
            </div>
            <div>
              <strong>ATS</strong>
              <span>ориентированный output</span>
            </div>
            <div>
              <strong>PDF</strong>
              <span>готов к отправке</span>
            </div>
          </div>
          <HeroArt />
        </div>

        <div className="hero-panel" id="auth">
          <h2 style={{ marginTop: 0 }}>{mode === "login" ? "Вход" : "Регистрация"}</h2>
          <p style={{ opacity: 0.9 }}>
            {mode === "login"
              ? "Войдите, чтобы сохранять резюме, вакансии, историю анализов и выгружать PDF."
              : "Создайте аккаунт — 3 бесплатных анализа и личный кабинет."}
          </p>
          <form onSubmit={onSubmit} style={{ display: "grid", gap: 12, marginTop: 16 }}>
            {!verificationSent ? (
              <>
                <input
                  className="input input--dark"
                  type="email"
                  placeholder="Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  disabled={submitting}
                />
                <input
                  className="input input--dark"
                  type="password"
                  placeholder={mode === "login" ? "Пароль" : "Пароль (мин. 8 символов)"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={mode === "register" ? 8 : 1}
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                  disabled={submitting}
                />
                {mode === "register" ? (
                  <label className="consent-line">
                    <input
                      type="checkbox"
                      checked={consent}
                      onChange={(e) => setConsent(e.target.checked)}
                      disabled={submitting}
                    />
                    <span>
                      Я принимаю условия{" "}
                      <Link to="/offer" target="_blank">
                        оферты
                      </Link>{" "}
                      и даю согласие на обработку персональных данных согласно{" "}
                      <Link to="/privacy" target="_blank">
                        политике конфиденциальности
                      </Link>
                      .
                    </span>
                  </label>
                ) : null}
                {mode === "register" ? <SmartCaptcha onToken={setCaptchaToken} /> : null}
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ width: "100%" }}
                  disabled={submitting || (mode === "register" && (!consent || !captchaToken))}
                >
                  {submitting ? "Загрузка..." : mode === "login" ? "Войти" : "Создать аккаунт"}
                </button>
              </>
            ) : (
              <>
                <div style={{ fontSize: 14, opacity: 0.9, marginBottom: 4 }}>
                  Код отправлен на <strong>{email}</strong>
                </div>
                <input
                  className="input input--dark"
                  type="text"
                  placeholder="— — — — — —"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  maxLength={6}
                  required
                  disabled={submitting}
                  autoFocus
                  style={{ fontSize: 22, letterSpacing: "10px", textAlign: "center", fontWeight: 700 }}
                />
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ width: "100%" }}
                  disabled={submitting || code.length !== 6}
                >
                  {submitting ? "Загрузка..." : "Подтвердить"}
                </button>
                <button
                  type="button"
                  className="link-btn"
                  onClick={() => {
                    setVerificationSent(false);
                    setCode("");
                    setMessage("");
                  }}
                  style={{ textAlign: "center", opacity: 0.8, fontSize: 13, marginTop: 4 }}
                >
                  ← Вернуться
                </button>
              </>
            )}
          </form>

          {mode === "login" ? (
            <p style={{ marginTop: 12, opacity: 0.85, fontSize: 14 }}>
              Нет аккаунта?{" "}
              <button
                type="button"
                className="link-btn"
                onClick={() => {
                  setMode("register");
                  setMessage("");
                  setVerificationSent(false);
                }}
              >
                Зарегистрироваться
              </button>
            </p>
          ) : (
            <p style={{ marginTop: 12, opacity: 0.85, fontSize: 14 }}>
              Уже есть аккаунт?{" "}
              <button
                type="button"
                className="link-btn"
                onClick={() => {
                  setMode("login");
                  setMessage("");
                  setVerificationSent(false);
                }}
              >
                Войти
              </button>
            </p>
          )}

          {message ? <p style={{ color: "#fecaca", fontSize: 14, marginTop: 12 }}>{message}</p> : null}

          {!verificationSent && (
            <>
              <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "20px 0 12px", opacity: 0.7 }}>
                <div style={{ flex: 1, height: 1, background: "rgba(255,255,255,0.2)" }} />
                <span style={{ fontSize: 12 }}>или</span>
                <div style={{ flex: 1, height: 1, background: "rgba(255,255,255,0.2)" }} />
              </div>
              <div style={{ display: "grid", gap: 8 }}>
                <button
                  type="button"
                  onClick={() => startOAuth("yandex")}
                  className="btn"
                  style={{ width: "100%", fontSize: 14, fontWeight: 700, background: "#fc3f1d", color: "#fff", border: "none" }}
                >
                  Войти через Яндекс
                </button>
                <button
                  type="button"
                  onClick={() => startOAuth("vk")}
                  className="btn"
                  style={{ width: "100%", fontSize: 14, fontWeight: 700, background: "#0077ff", color: "#fff", border: "none" }}
                >
                  Войти через VK
                </button>
              </div>
              <p style={{ fontSize: 12, opacity: 0.8, marginTop: 12, lineHeight: 1.45 }}>
                Входя через провайдера, вы принимаете условия{" "}
                <Link to="/offer" target="_blank" style={{ color: "#bfdbfe", textDecoration: "underline" }}>
                  оферты
                </Link>{" "}
                и{" "}
                <Link to="/privacy" target="_blank" style={{ color: "#bfdbfe", textDecoration: "underline" }}>
                  политики обработки персональных данных
                </Link>
                .
              </p>
            </>
          )}
        </div>
      </section>

      <section className="container" id="demo" style={{ paddingBottom: 48 }}>
        <h2>Попробуйте без регистрации</h2>
        <p className="muted" style={{ maxWidth: 640, marginBottom: 24 }}>
          Один бесплатный анализ для анонимного пользователя. Зарегистрируйтесь, чтобы сохранять
          резюме и историю.
        </p>
        <div className="card card--flat">
          <div className="cabinet-grid">
            <div className="stack">
              <div>
                <label className="field-label">Ваше резюме</label>
                <textarea
                  className="textarea"
                  rows={8}
                  value={resumeText}
                  onChange={(e) => setResumeText(e.target.value)}
                />
              </div>
            </div>
            <div className="stack">
              <div>
                <label className="field-label">Текст вакансии</label>
                <textarea
                  className="textarea"
                  rows={8}
                  value={vacancyText}
                  onChange={(e) => setVacancyText(e.target.value)}
                />
              </div>
            </div>
          </div>
          {demoError ? <p className="error-text" style={{ marginTop: 12 }}>{demoError}</p> : null}
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={runDemo} disabled={demoBusy}>
            {demoBusy ? "Анализируем..." : "Адаптировать резюме"}
          </button>
        </div>
        {demoResult ? (
          <div style={{ marginTop: 20 }}>
            <AnalysisResultCard analysis={demoResult} />
          </div>
        ) : null}
      </section>

      <section className="container" id="features" style={{ paddingBottom: 48 }}>
        <h2>Что делает сервис продающим</h2>
        <div className="grid-3">
          <article className="card feature-card">
            <span className="feature-ic" style={{ background: "#e8f0ff" }}>🧭</span>
            <h3>Карта пробелов</h3>
            <p className="muted">Показывает, каких навыков и формулировок не хватает под конкретную роль.</p>
          </article>
          <article className="card feature-card">
            <span className="feature-ic" style={{ background: "#dcfce7" }}>♻️</span>
            <h3>ATS-переписывание</h3>
            <p className="muted">Перепаковывает уже имеющийся опыт под язык вакансии — без выдуманного опыта.</p>
          </article>
          <article className="card feature-card">
            <span className="feature-ic" style={{ background: "#f3e8ff" }}>📨</span>
            <h3>Готовые материалы</h3>
            <p className="muted">Сразу формирует сопроводительное письмо и PDF для отправки рекрутёру.</p>
          </article>
        </div>
      </section>

      <section className="container" id="pricing" style={{ paddingBottom: 80 }}>
        <h2>Модель доступа</h2>
        <div className="grid-3">
          <article className="card price-card">
            <span className="feature-ic" style={{ background: "#eef2f7" }}>🎁</span>
            <h3>Гость</h3>
            <p className="muted">1 анализ без регистрации, чтобы почувствовать продукт.</p>
          </article>
          <article className="card price-card price-card--featured">
            <span className="price-flag">Популярный</span>
            <span className="feature-ic" style={{ background: "#e8f0ff" }}>⭐</span>
            <h3>Free account</h3>
            <p className="muted">3 анализа, история результатов, сохранённые резюме и выгрузка PDF.</p>
          </article>
          <article className="card price-card">
            <span className="feature-ic" style={{ background: "#fef3c7" }}>🚀</span>
            <h3>Subscription-ready</h3>
            <p className="muted">После лимита подключается paywall и подписка без переделки UX.</p>
          </article>
        </div>
      </section>

      <Footer />
    </div>
  );
}
