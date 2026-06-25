import { useMemo, useRef, useState } from "react";
import { resources } from "../api/resources";
import {
  Analysis,
  ResumeDocument,
  ResumeEducation,
  ResumeExperience,
  emptyResumeDocument,
} from "../types";

type Props = {
  analysis: Analysis;
  token: string;
  onSaved?: (updated: Analysis) => void;
  notify?: (message: string, kind?: "success" | "error") => void;
};

// Сжимаем фото в квадрат ~400px и отдаём data-URL (чтобы не хранить мегабайты).
async function fileToSquareDataUrl(file: File, size = 400): Promise<string> {
  const dataUrl = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
  const img = await new Promise<HTMLImageElement>((resolve, reject) => {
    const i = new Image();
    i.onload = () => resolve(i);
    i.onerror = reject;
    i.src = dataUrl;
  });
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) return dataUrl;
  const side = Math.min(img.width, img.height);
  const sx = (img.width - side) / 2;
  const sy = (img.height - side) / 2;
  ctx.drawImage(img, sx, sy, side, side, 0, 0, size, size);
  return canvas.toDataURL("image/jpeg", 0.85);
}

function TagInput({ value, onChange, placeholder }: { value: string[]; onChange: (v: string[]) => void; placeholder?: string }) {
  const [draft, setDraft] = useState("");
  const add = () => {
    const v = draft.trim();
    if (v && !value.includes(v)) onChange([...value, v]);
    setDraft("");
  };
  return (
    <div>
      <div className="chips" style={{ marginBottom: value.length ? 8 : 0 }}>
        {value.map((t) => (
          <span key={t} className="chip chip--matched" style={{ cursor: "pointer" }} onClick={() => onChange(value.filter((x) => x !== t))}>
            {t} ✕
          </span>
        ))}
      </div>
      <input
        className="input"
        placeholder={placeholder ?? "Добавить и Enter"}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === ",") {
            e.preventDefault();
            add();
          }
        }}
        onBlur={add}
      />
    </div>
  );
}

export function ResumeEditor({ analysis, token, onSaved, notify }: Props) {
  const initialDoc = useMemo<ResumeDocument>(
    () => analysis.resume_document ?? emptyResumeDocument(),
    [analysis.resume_document]
  );
  const [doc, setDoc] = useState<ResumeDocument>(initialDoc);
  const [cover, setCover] = useState(analysis.cover_letter);
  const [tab, setTab] = useState<"resume" | "letter">("resume");
  const [saving, setSaving] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const patch = (p: Partial<ResumeDocument>) => setDoc((d) => ({ ...d, ...p }));
  const patchContact = (p: Partial<ResumeDocument["contacts"]>) =>
    setDoc((d) => ({ ...d, contacts: { ...d.contacts, ...p } }));

  const setExp = (i: number, p: Partial<ResumeExperience>) =>
    setDoc((d) => ({ ...d, experience: d.experience.map((e, idx) => (idx === i ? { ...e, ...p } : e)) }));
  const addExp = () =>
    setDoc((d) => ({ ...d, experience: [...d.experience, { company: "", role: "", period: "", location: "", bullets: [] }] }));
  const removeExp = (i: number) => setDoc((d) => ({ ...d, experience: d.experience.filter((_, idx) => idx !== i) }));

  const setEdu = (i: number, p: Partial<ResumeEducation>) =>
    setDoc((d) => ({ ...d, education: d.education.map((e, idx) => (idx === i ? { ...e, ...p } : e)) }));
  const addEdu = () => setDoc((d) => ({ ...d, education: [...d.education, { institution: "", degree: "", period: "" }] }));
  const removeEdu = (i: number) => setDoc((d) => ({ ...d, education: d.education.filter((_, idx) => idx !== i) }));

  const onPhoto = async (file?: File) => {
    if (!file) return;
    try {
      patch({ photo: await fileToSquareDataUrl(file) });
    } catch {
      notify?.("Не удалось обработать изображение", "error");
    }
  };

  const save = async () => {
    if (!analysis.id) {
      notify?.("Сохранение доступно после анализа в кабинете", "error");
      return;
    }
    setSaving(true);
    try {
      const updated = await resources.saveDocument(token, analysis.id, doc, cover);
      onSaved?.(updated);
      notify?.("Резюме сохранено");
    } catch (err) {
      notify?.((err as Error).message, "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="editor-toolbar no-print">
        <div className="editor-tabs">
          <button type="button" className={`editor-tab${tab === "resume" ? " editor-tab--active" : ""}`} onClick={() => setTab("resume")}>
            📄 Резюме
          </button>
          <button type="button" className={`editor-tab${tab === "letter" ? " editor-tab--active" : ""}`} onClick={() => setTab("letter")}>
            ✉️ Письмо
          </button>
        </div>
        <span className="spacer" />
        <button type="button" className="btn btn-secondary btn-sm" onClick={() => window.print()}>
          🖨 Скачать PDF
        </button>
        <button type="button" className="btn btn-primary btn-sm" onClick={save} disabled={saving}>
          {saving ? "Сохранение..." : "Сохранить"}
        </button>
      </div>

      <div className="editor-grid">
        {/* ── Форма ── */}
        <div className="editor-form no-print">
          {tab === "resume" ? (
            <>
              <section className="editor-section">
                <h4>Заголовок и фото</h4>
                <div className="photo-uploader" style={{ marginBottom: 12 }}>
                  {doc.photo ? (
                    <img className="photo-thumb" src={doc.photo} alt="фото" />
                  ) : (
                    <div className="photo-thumb photo-thumb--empty">👤</div>
                  )}
                  <div style={{ display: "grid", gap: 6 }}>
                    <input
                      ref={fileRef}
                      type="file"
                      accept="image/*"
                      style={{ display: "none" }}
                      onChange={(e) => onPhoto(e.target.files?.[0])}
                    />
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => fileRef.current?.click()}>
                      {doc.photo ? "Заменить фото" : "Загрузить фото"}
                    </button>
                    {doc.photo ? (
                      <button type="button" className="btn btn-danger btn-sm" onClick={() => patch({ photo: null })}>
                        Удалить фото
                      </button>
                    ) : null}
                  </div>
                </div>
                <div className="editor-field">
                  <label className="field-label">Имя и фамилия</label>
                  <input className="input" value={doc.full_name} onChange={(e) => patch({ full_name: e.target.value })} />
                </div>
                <div className="editor-field">
                  <label className="field-label">Желаемая должность</label>
                  <input className="input" value={doc.headline} onChange={(e) => patch({ headline: e.target.value })} />
                </div>
              </section>

              <section className="editor-section">
                <h4>Контакты</h4>
                <div className="editor-row">
                  <div className="editor-field">
                    <label className="field-label">Email</label>
                    <input className="input" value={doc.contacts.email} onChange={(e) => patchContact({ email: e.target.value })} />
                  </div>
                  <div className="editor-field">
                    <label className="field-label">Телефон</label>
                    <input className="input" value={doc.contacts.phone} onChange={(e) => patchContact({ phone: e.target.value })} />
                  </div>
                  <div className="editor-field">
                    <label className="field-label">Город</label>
                    <input className="input" value={doc.contacts.location} onChange={(e) => patchContact({ location: e.target.value })} />
                  </div>
                  <div className="editor-field">
                    <label className="field-label">Сайт / профиль</label>
                    <input className="input" value={doc.contacts.website} onChange={(e) => patchContact({ website: e.target.value })} />
                  </div>
                </div>
              </section>

              <section className="editor-section">
                <h4>О себе</h4>
                <textarea className="textarea" rows={4} value={doc.summary} onChange={(e) => patch({ summary: e.target.value })} />
              </section>

              <section className="editor-section">
                <div className="editor-subcard-head" style={{ marginBottom: 12 }}>
                  <h4 style={{ margin: 0 }}>Опыт работы</h4>
                  <button type="button" className="icon-btn icon-btn--add" onClick={addExp} title="Добавить">＋</button>
                </div>
                {doc.experience.map((exp, i) => (
                  <div key={i} className="editor-subcard">
                    <div className="editor-subcard-head">
                      <strong style={{ fontSize: 13 }}>Место #{i + 1}</strong>
                      <button type="button" className="icon-btn" onClick={() => removeExp(i)} title="Удалить">✕</button>
                    </div>
                    <div className="editor-row">
                      <div className="editor-field">
                        <label className="field-label">Должность</label>
                        <input className="input" value={exp.role} onChange={(e) => setExp(i, { role: e.target.value })} />
                      </div>
                      <div className="editor-field">
                        <label className="field-label">Компания</label>
                        <input className="input" value={exp.company} onChange={(e) => setExp(i, { company: e.target.value })} />
                      </div>
                      <div className="editor-field">
                        <label className="field-label">Период</label>
                        <input className="input" value={exp.period} onChange={(e) => setExp(i, { period: e.target.value })} placeholder="2022 — наст. время" />
                      </div>
                      <div className="editor-field">
                        <label className="field-label">Локация</label>
                        <input className="input" value={exp.location} onChange={(e) => setExp(i, { location: e.target.value })} />
                      </div>
                    </div>
                    <label className="field-label">Достижения</label>
                    {exp.bullets.map((b, bi) => (
                      <div key={bi} className="editor-bullet">
                        <textarea
                          className="textarea"
                          rows={2}
                          value={b}
                          onChange={(e) => setExp(i, { bullets: exp.bullets.map((x, xi) => (xi === bi ? e.target.value : x)) })}
                        />
                        <button type="button" className="icon-btn" onClick={() => setExp(i, { bullets: exp.bullets.filter((_, xi) => xi !== bi) })}>✕</button>
                      </div>
                    ))}
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => setExp(i, { bullets: [...exp.bullets, ""] })}>
                      ＋ Пункт
                    </button>
                  </div>
                ))}
              </section>

              <section className="editor-section">
                <h4>Навыки</h4>
                <TagInput value={doc.skills} onChange={(v) => patch({ skills: v })} placeholder="Навык + Enter" />
              </section>

              <section className="editor-section">
                <div className="editor-subcard-head" style={{ marginBottom: 12 }}>
                  <h4 style={{ margin: 0 }}>Образование</h4>
                  <button type="button" className="icon-btn icon-btn--add" onClick={addEdu} title="Добавить">＋</button>
                </div>
                {doc.education.map((ed, i) => (
                  <div key={i} className="editor-subcard">
                    <div className="editor-subcard-head">
                      <strong style={{ fontSize: 13 }}>#{i + 1}</strong>
                      <button type="button" className="icon-btn" onClick={() => removeEdu(i)}>✕</button>
                    </div>
                    <div className="editor-field">
                      <label className="field-label">Специальность / степень</label>
                      <input className="input" value={ed.degree} onChange={(e) => setEdu(i, { degree: e.target.value })} />
                    </div>
                    <div className="editor-row">
                      <div className="editor-field">
                        <label className="field-label">Учебное заведение</label>
                        <input className="input" value={ed.institution} onChange={(e) => setEdu(i, { institution: e.target.value })} />
                      </div>
                      <div className="editor-field">
                        <label className="field-label">Период</label>
                        <input className="input" value={ed.period} onChange={(e) => setEdu(i, { period: e.target.value })} />
                      </div>
                    </div>
                  </div>
                ))}
              </section>

              <section className="editor-section">
                <h4>Языки</h4>
                <TagInput value={doc.languages} onChange={(v) => patch({ languages: v })} placeholder="Например: Английский — B2" />
              </section>
            </>
          ) : (
            <section className="editor-section">
              <h4>Сопроводительное письмо</h4>
              <textarea className="textarea" rows={18} value={cover} onChange={(e) => setCover(e.target.value)} />
            </section>
          )}
        </div>

        {/* ── Предпросмотр (печатается) ── */}
        <div className="editor-preview">
          <div className="sheet-scroll">
            <div className="print-area">
              {tab === "resume" ? <ResumeSheet doc={doc} /> : <LetterSheet doc={doc} cover={cover} />}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ResumeSheet({ doc }: { doc: ResumeDocument }) {
  const c = doc.contacts;
  return (
    <div className="resume-sheet">
      <aside className="resume-aside">
        {doc.photo ? (
          <img className="resume-photo" src={doc.photo} alt="фото" />
        ) : (
          <div className="resume-photo resume-photo--empty">👤</div>
        )}
        {(c.email || c.phone || c.location || c.website) && (
          <>
            <h3>Контакты</h3>
            <div className="resume-aside-contact">
              {c.email ? <span>✉️ {c.email}</span> : null}
              {c.phone ? <span>📞 {c.phone}</span> : null}
              {c.location ? <span>📍 {c.location}</span> : null}
              {c.website ? <span>🔗 {c.website}</span> : null}
            </div>
          </>
        )}
        {doc.skills.length ? (
          <>
            <h3>Навыки</h3>
            <div>
              {doc.skills.map((s) => (
                <span key={s} className="resume-aside-skill">{s}</span>
              ))}
            </div>
          </>
        ) : null}
        {doc.languages.length ? (
          <>
            <h3>Языки</h3>
            <div className="resume-aside-langs">
              {doc.languages.map((l) => (
                <span key={l}>{l}</span>
              ))}
            </div>
          </>
        ) : null}
      </aside>

      <main className="resume-main">
        <h1 className="resume-name">{doc.full_name || "Ваше имя"}</h1>
        {doc.headline ? <p className="resume-headline">{doc.headline}</p> : null}
        {doc.summary ? (
          <>
            <h3>О себе</h3>
            <p className="resume-summary">{doc.summary}</p>
          </>
        ) : null}
        {doc.experience.length ? (
          <>
            <h3>Опыт работы</h3>
            {doc.experience.map((exp, i) => (
              <div key={i} className="resume-exp">
                <div className="resume-exp-head">
                  <div>
                    <span className="resume-exp-role">{exp.role || "Должность"}</span>
                    {exp.company ? <span className="resume-exp-company"> · {exp.company}</span> : null}
                  </div>
                  {exp.period ? <span className="resume-exp-period">{exp.period}</span> : null}
                </div>
                {exp.bullets.length ? (
                  <ul>
                    {exp.bullets.filter((b) => b.trim()).map((b, bi) => (
                      <li key={bi}>{b}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ))}
          </>
        ) : null}
        {doc.education.length ? (
          <>
            <h3>Образование</h3>
            {doc.education.map((ed, i) => (
              <div key={i} className="resume-edu">
                <strong>{ed.degree || ed.institution}</strong>
                <span>{[ed.institution !== ed.degree ? ed.institution : "", ed.period].filter(Boolean).join(" · ")}</span>
              </div>
            ))}
          </>
        ) : null}
      </main>
    </div>
  );
}

function LetterSheet({ doc, cover }: { doc: ResumeDocument; cover: string }) {
  const c = doc.contacts;
  const contactLine = [c.email, c.phone, c.location].filter(Boolean).join("  ·  ");
  return (
    <div className="letter-sheet">
      <div className="letter-from">
        <strong>{doc.full_name || "Ваше имя"}</strong>
        {doc.headline ? <div>{doc.headline}</div> : null}
        {contactLine ? <div>{contactLine}</div> : null}
      </div>
      <div className="letter-body">{cover || "Текст сопроводительного письма появится здесь."}</div>
    </div>
  );
}
