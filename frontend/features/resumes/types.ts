export type SectionType =
  | "summary"
  | "education"
  | "experience"
  | "projects"
  | "skills"
  | "certifications"
  | "achievements"
  | "awards";

export interface ContactVisibility {
  phone: boolean;
  location: boolean;
  website: boolean;
  github: boolean;
  linkedin: boolean;
  email: boolean;
}

export interface ResumeSection {
  section_type: SectionType;
  custom_title: string | null;
  visible: boolean;
  item_ids: string[];
}

export interface ResumeContent {
  summary: string | null;
  contact_visibility: ContactVisibility;
  sections: ResumeSection[];
}

export interface ResumeTemplate {
  id: string;
  slug: string;
  name: string;
  description: string | null;
}

export interface Resume {
  id: string;
  title: string;
  template_id: string;
  created_at: string;
  updated_at: string;
  latest_version_number: number;
}

export interface ResumeCreatePayload {
  title: string;
  template_id: string;
}

export interface ResumeUpdatePayload {
  title?: string;
  template_id?: string;
}

export interface ResumeVersion {
  id: string;
  resume_id: string;
  version_number: number;
  content: ResumeContent;
  rendered_file_id: string | null;
  rendered_at: string | null;
  created_at: string;
}

export interface ResumeVersionSummary {
  id: string;
  version_number: number;
  rendered_file_id: string | null;
  rendered_at: string | null;
  created_at: string;
}

export interface ExportedResumeFile {
  id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  url: string;
  created_at: string;
}
