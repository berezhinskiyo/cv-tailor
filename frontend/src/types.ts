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
  analysis_count: number;
  consent_at: string | null;
  consent_version: string | null;
  created_at: string;
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

export type Analysis = {
  id?: number | null;
  score: number;
  matched_skills: string[];
  missing_skills: string[];
  improved_resume: string;
  cover_letter: string;
  created_at?: string | null;
};
