export interface CoverLetter {
  id: string;
  company_name: string;
  role_title: string;
  hiring_manager: string | null;
  job_description_id: string | null;
  body: string;
  created_at: string;
}

export interface GenerateCoverLetterPayload {
  company_name: string;
  role_title: string;
  hiring_manager?: string | null;
  job_description_id?: string | null;
  job_description_text?: string | null;
}

export interface LinkedinGeneration {
  id: string;
  target_role: string | null;
  headline: string;
  about: string;
  created_at: string;
}

export interface GenerateLinkedinPayload {
  target_role?: string | null;
}
