export type SectionType =
  | "summary"
  | "education"
  | "experience"
  | "projects"
  | "skills"
  | "certifications"
  | "achievements"
  | "awards"
  | "research"
  | "volunteer_experience"
  | "leadership_roles"
  | "organizations"
  | "languages"
  | "references"
  | "hackathons"
  | "competitions"
  | "patents";

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

/**
 * The four font choices map to real installed font stacks server-side (see
 * backend's renderer.py FONT_STACKS) -- arial/times are always available
 * (fonts-liberation), calibri/georgia need fonts-crosextra-carlito/caladea.
 */
export type FontFamily = "arial" | "calibri" | "times" | "georgia";
export type Spacing = "compact" | "cozy" | "relaxed";

/**
 * Visual knobs the exported PDF actually renders with -- part of the real,
 * persisted resume content (not a client-only preview toggle), so what the
 * user picks in the builder is what shows up in the downloaded file.
 */
export interface ResumeStyle {
  accent_color: string;
  font_family: FontFamily;
  spacing: Spacing;
  // Computed-only (0.8-1.0): set exclusively by the AI-generation one-page
  // trim loop when spacing presets alone don't make content fit -- never a
  // manual choice in the customizer.
  content_density: number;
}

export interface ResumeContent {
  summary: string | null;
  contact_visibility: ContactVisibility;
  sections: ResumeSection[];
  style: ResumeStyle;
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

export interface ResumeGeneratePayload {
  title?: string | null;
  // Optional, same as title -- omitted means "use the default template."
  template_id?: string | null;
  accent_color?: string | null;
  job_description: string;
  target_role?: string | null;
  target_company?: string | null;
}

export interface GenerateResumeResponse {
  resume_id: string;
  file: ExportedResumeFile;
}
