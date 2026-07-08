import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { resources } from "../api/resources";
import { useAuth } from "../context/AuthContext";
import { Logo } from "../components/Logo";
import { Footer } from "../components/Footer";
import { Toast } from "../components/Toast";
import { useToast } from "../hooks/useToast";
import { Payment } from "../types";

const PRO_PRICE_RUB = 490; // за месяц, синхронно с backend PRO_PRICE_KOPECKS=49000
const PERIODS = [
  { months: 1, label: "1 месяц" },
  { months: 3, label: "3 месяца" },
  { months: 6, label: "6 месяцев" },
  { months: 12, label: "12 месяцев" },
];

function formatRub(kopecks: number): string {
  return `${(kopecks / 100).toLocaleString("ru-RU")} ₽`;
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("ru-RU", { day: "2-digit", month: "long", year: "numeric" });
}

const STATUS_LABEL: Record<string, string> = {
  pending: "ожидает оплаты",
  succeeded: "оплачен",
  canceled: "отменён",
};

export function BillingPage() {
  const { token, user, logout, refreshMe } = useAuth();
  const { toast, showToast, clearToast } = useToast();
  const [params, setParams] = useSearchParams();

  const [periodMonths, setPeriodMonths] = useState(1);
  const [busy, setBusy] = useState(false);
  const [payments, setPayments] = useState<Payment[]>([]);

  const amount = useMemo(() => PRO_PRICE_RUB * periodMonths, [periodMonths]);

  useEffect(() => {
    if (!token) return;
    resources.paymentHistory(token).then(setPayments).catch(() => setPayments([]));
  }, [token]);

  // Возврат из платёжной формы Т-Банка.
  useEffect(() => {
    if (params.get("paid") === "1") {
      showToast("Оплата прошла успешно. Подписка PRO активирована.");
      void refreshMe();
      params.delete("paid");
      setParams(params, { replace: true });
    } else if (params.get("failed") === "1") {
      showToast("Оплата не завершена. Попробуйте ещё раз.", "error");
      params.delete("failed");
      setParams(params, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!token || !user) return null;

  const subscribe = async () => {
    setBusy(true);
    try {
      const { confirmation_url } = await resources.createPayment(token, periodMonths);
      window.location.href = confirmation_url;
    } catch (err) {
      showToast((err as Error).message, "error");
      setBusy(false);
    }
  };

  const isPro = user.subscription_type !== "free";

  return (
    <div>
      {toast ? <Toast message={toast.message} kind={toast.kind} onClose={clearToast} /> : null}

      <header className="container nav">
        <Link to="/" className="nav-brand" aria-label="CV Tailor">
          <Logo />
        </Link>
        <div className="nav-links">
          <Link to="/dashboard">Личный кабинет</Link>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => void logout()}>
            Выйти
          </button>
        </div>
      </header>

      <section className="container">
        <div className="cabinet-head">
          <div>
            <h1 style={{ margin: 0 }}>Подписка PRO</h1>
            <p className="muted" style={{ margin: "4px 0 0" }}>
              Текущий тариф: <span className="badge badge-success">{user.subscription_type}</span>
              {isPro && user.subscription_until ? ` · активна до ${formatDate(user.subscription_until)}` : null}
            </p>
          </div>
        </div>

        <div className="cabinet-grid">
          <article className="card card--flat">
            <h2 style={{ marginTop: 0 }}>PRO — безлимитные анализы</h2>
            <p className="muted">{PRO_PRICE_RUB} ₽ в месяц. Оплата картой через Т-Банк.</p>

            <label className="field-label" style={{ marginTop: 12 }}>Период</label>
            <div className="entity-list" style={{ marginTop: 8 }}>
              {PERIODS.map((p) => (
                <div
                  key={p.months}
                  className={`entity-item${periodMonths === p.months ? " entity-item--active" : ""}`}
                  onClick={() => setPeriodMonths(p.months)}
                >
                  <strong>{p.label}</strong>
                  <span className="badge">{formatRub(PRO_PRICE_RUB * p.months * 100)}</span>
                </div>
              ))}
            </div>

            <button className="btn btn-primary" style={{ marginTop: 16, width: "100%" }} onClick={subscribe} disabled={busy}>
              {busy ? "Переходим к оплате…" : `Оплатить ${formatRub(amount * 100)}`}
            </button>
            <p className="muted" style={{ fontSize: 13, marginTop: 10 }}>
              После оплаты вы вернётесь в кабинет. Чек по 54-ФЗ придёт на вашу почту.
            </p>
          </article>

          <article className="card card--flat">
            <h2 style={{ marginTop: 0 }}>История платежей</h2>
            {payments.length === 0 ? (
              <p className="muted">Платежей пока нет.</p>
            ) : (
              <div className="entity-list">
                {payments.map((p) => (
                  <div key={p.id} className="entity-item" style={{ cursor: "default" }}>
                    <span>
                      {p.plan.toUpperCase()} · {p.period_months} мес. · {formatRub(p.amount_kopecks)}
                    </span>
                    <span className={`badge${p.status === "succeeded" ? " badge-success" : ""}`}>
                      {STATUS_LABEL[p.status] ?? p.status}
                    </span>
                    <span className="muted" style={{ fontSize: 13 }}>{formatDate(p.created_at)}</span>
                  </div>
                ))}
              </div>
            )}
          </article>
        </div>
      </section>

      <Footer />
    </div>
  );
}
