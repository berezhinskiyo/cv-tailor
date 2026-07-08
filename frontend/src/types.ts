export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

export type UserMe = {
  id: number;
  email: string;
  display_name: string | null;
  is_admin: boolean;
  subscription_type: string;
  subscription_until: string | null;
  analysis_count: number;
  consent_at: string | null;
  consent_version: string | null;
  created_at: string;
};

export type Payment = {
  id: number;
  amount_kopecks: number;
  plan: string;
  period_months: number;
  status: string;
  created_at: string;
  completed_at: string | null;
};

export type Resume = {
  id: number;
  title: string;
  original_text: string;
  created_at: string;
};

export type Vacancy = {
  id: number;
  title: string;
  vacancy_text: string;
  created_at: string;
};

export type ResumeContacts = {
  email: string;
  phone: string;
  location: string;
  website: string;
};

export type ResumeExperience = {
  company: string;
  role: string;
  period: string;
  location: string;
  bullets: string[];
};

export type ResumeEducation = {
  institution: string;
  degree: string;
  period: string;
};

export type ResumeDocument = {
  full_name: string;
  headline: string;
  photo: string | null;
  contacts: ResumeContacts;
  summary: string;
  experience: ResumeExperience[];
  skills: string[];
  education: ResumeEducation[];
  languages: string[];
};

export type Analysis = {
  id?: number | null;
  score: number;
  matched_skills: string[];
  missing_skills: string[];
  improved_resume: string;
  cover_letter: string;
  resume_document?: ResumeDocument | null;
  created_at?: string | null;
};

export const emptyResumeDocument = (): ResumeDocument => ({
  full_name: "",
  headline: "",
  photo: null,
  contacts: { email: "", phone: "", location: "", website: "" },
  summary: "",
  experience: [],
  skills: [],
  education: [],
  languages: [],
});
