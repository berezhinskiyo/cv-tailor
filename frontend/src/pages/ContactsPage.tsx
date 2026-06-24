import { Link } from "react-router-dom";
import { Logo } from "../components/Logo";
import { Footer } from "../components/Footer";

export function ContactsPage() {
  return (
    <div>
      <header className="container nav">
        <Link to="/" className="nav-brand" aria-label="CV Tailor">
          <Logo />
        </Link>
        <div className="nav-links">
          <Link to="/offer">Оферта</Link>
          <Link to="/">На главную</Link>
        </div>
      </header>

      <section className="container" style={{ paddingTop: 32, paddingBottom: 64 }}>
        <h1>Контакты и реквизиты</h1>
        <p className="muted" style={{ maxWidth: 640 }}>
          Услуги предоставляет самозанятый (плательщик налога на профессиональный доход).
        </p>

        <div className="card contacts-card">
          <dl className="contacts-list">
            <div>
              <dt>Исполнитель</dt>
              <dd>Бережинский Олег Владимирович</dd>
            </div>
            <div>
              <dt>Статус</dt>
              <dd>Самозанятый (плательщик НПД)</dd>
            </div>
            <div>
              <dt>ИНН</dt>
              <dd>772319402569</dd>
            </div>
            <div>
              <dt>E-mail</dt>
              <dd>
                <a href="mailto:oberezhinsky@yandex.ru">oberezhinsky@yandex.ru</a>
              </dd>
            </div>
          </dl>
          <p className="muted" style={{ margin: "16px 0 0", fontSize: 14 }}>
            По вопросам оплаты, доступа и поддержки пишите на указанный e-mail.
          </p>
          <p style={{ margin: "12px 0 0", fontSize: 14 }}>
            Условия использования и предоставления услуг — в <Link to="/offer">Публичной оферте</Link>.
          </p>
        </div>
      </section>

      <Footer />
    </div>
  );
}
