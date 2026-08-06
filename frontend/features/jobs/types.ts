import type { EmploymentType } from "@/features/profile/types";

export interface JobAnalysis {
  keywords: string[];
  required_skills: string[];
  preferred_skills: string[];
}

export interface JobDescription {
  id: string;
  title: string;
  raw_text: string;
  location: string | null;
  employment_type: EmploymentType | null;
  company_id: string | null;
  company_name: string | null;
  keywords: string[];
  required_skills: string[];
  preferred_skills: string[];
  created_at: string;
  updated_at: string;
}

export interface JobDescriptionCreatePayload {
  title: string;
  raw_text: string;
  company_name?: string | null;
  location?: string | null;
  employment_type?: EmploymentType | null;
}

export interface AtsScore {
  id: string;
  job_description_id: string;
  overall_score: number;
  matched_skills: string[];
  missing_skills: string[];
  recommendations: string[];
  created_at: string;
}
