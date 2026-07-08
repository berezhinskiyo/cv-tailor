import { API_URL, api, publicApi } from "./client";
import { Analysis, Payment, Resume, ResumeDocument, Vacancy } from "../types";

export const resources = {
  listResumes: (token: string) => api<Resume[]>("/resumes", {}, token),
  createResume: (token: string, payload: { title: string; original_text: string }) =>
    api<Resume>("/resumes", { method: "POST", body: JSON.stringify(payload) }, token),
  deleteResume: (token: string, id: number) =>
    api<void>(`/resumes/${id}`, { method: "DELETE" }, token),

  listVacancies: (token: string) => api<Vacancy[]>("/vacancies", {}, token),
  createVacancy: (token: string, payload: { title: string; vacancy_text: string }) =>
    api<Vacancy>("/vacancies", { method: "POST", body: JSON.stringify(payload) }, token),
  deleteVacancy: (token: string, id: number) =>
    api<void>(`/vacancies/${id}`, { method: "DELETE" }, token),

  listAnalyses: (token: string) => api<Analysis[]>("/analysis", {}, token),
  createAnalysis: (payload: Record<string, unknown>, token: string) =>
    api<Analysis>("/analysis", { method: "POST", body: JSON.stringify(payload) }, token),
  saveDocument: (
    token: string,
    id: number,
    resume_document: ResumeDocument,
    cover_letter: string
  ) =>
    api<Analysis>(
      `/analysis/${id}/document`,
      { method: "PUT", body: JSON.stringify({ resume_document, cover_letter }) },
      token
    ),

  // Оплата PRO-подписки (Т-Банк). Возвращает ссылку на платёжную форму.
  createPayment: (token: string, periodMonths = 1) =>
    api<{ confirmation_url: string; payment_id: number }>(
      "/payments",
      { method: "POST", body: JSON.stringify({ period_months: periodMonths }) },
      token
    ),
  paymentHistory: (token: string) => api<Payment[]>("/payments", {}, token),

  // Демо-анализ без авторизации (анонимный лимит на бэкенде).
  demoAnalysis: (payload: Record<string, unknown>, anonymousId: string) =>
    publicApi<Analysis>("/analysis", {
      method: "POST",
      body: JSON.stringify(payload),
      headers: { "X-Anonymous-Id": anonymousId },
    }),

  analysisPdfUrl: (id: number, token: string) =>
    `${API_URL}/analysis/${id}/pdf?access_token=${encodeURIComponent(token)}`,
};
