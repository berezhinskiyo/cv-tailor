import { Link } from "react-router-dom";
import { Logo } from "./Logo";

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="site-footer">
      <div className="container site-footer-inner">
        <div className="site-footer-brand">
          <Logo light />
          <p>
            AI-сервис адаптации резюме под вакансию: анализ соответствия, разбор пробелов в
            навыках, улучшенное резюме и сопроводительное письмо.
          </p>
          <div className="site-footer-badges">
            <span>🎯 Score-match по навыкам</span>
            <span>🤖 AI-улучшение резюме</span>
            <span>📄 Экспорт в PDF</span>
          </div>
        </div>

        <nav className="site-footer-col">
          <h4>Навигация</h4>
          <a href="/#demo">Демо-анализ</a>
          <a href="/#features">Возможности</a>
          <a href="/#pricing">Тарифы</a>
          <Link to="/contacts">Контакты</Link>
          <Link to="/offer">Оферта</Link>
          <Link to="/privacy">Конфиденциальность</Link>
        </nav>

        <nav className="site-footer-col">
          <h4>Сервис делает</h4>
          <span>📊 Процент совпадения</span>
          <span>🧭 Карту недостающих навыков</span>
          <span>✍️ Cover letter</span>
          <span>📥 PDF для отправки</span>
        </nav>
      </div>

      <div className="container site-footer-bottom">
        <span>
          © {year} CV Tailor · Самозанятый Бережинский О. В. · ИНН 772319402569 ·{" "}
          <span className="age-mark">6+</span>
        </span>
        <Link to="/contacts" className="site-footer-made">
          Контакты и реквизиты
        </Link>
      </div>
    </footer>
  );
}
