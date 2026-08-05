export type EmploymentType =
  | "full_time"
  | "part_time"
  | "internship"
  | "contract"
  | "freelance"
  | "volunteer";

export type ProjectStatus = "in_progress" | "completed" | "archived" | "on_hold";

export type SkillCategory = "technical" | "soft" | "tool" | "other";

export type SkillLevel = "beginner" | "intermediate" | "advanced" | "expert";

export interface Profile {
  id: string;
  user_id: string;
  headline: string | null;
  bio: string | null;
  phone: string | null;
  location: string | null;
  website_url: string | null;
  github_url: string | null;
  linkedin_url: string | null;
  avatar_url: string | null;
  completion_percentage: number;
}

export interface ProfileUpdatePayload {
  headline?: string | null;
  bio?: string | null;
  phone?: string | null;
  location?: string | null;
  website_url?: string | null;
  github_url?: string | null;
  linkedin_url?: string | null;
}

export interface Education {
  id: string;
  institution_name: string;
  degree: string;
  field_of_study: string | null;
  grade: string | null;
  description: string | null;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  created_at: string;
  updated_at: string;
}

export type EducationPayload = Omit<Education, "id" | "created_at" | "updated_at">;

export interface Experience {
  id: string;
  company_name: string;
  job_title: string;
  employment_type: EmploymentType;
  location: string | null;
  description: string | null;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  created_at: string;
  updated_at: string;
}

export type ExperiencePayload = Omit<Experience, "id" | "created_at" | "updated_at">;

export interface Skill {
  id: string;
  name: string;
  category: SkillCategory;
  level: SkillLevel | null;
  created_at: string;
  updated_at: string;
}

export type SkillPayload = Omit<Skill, "id" | "created_at" | "updated_at">;

export interface Project {
  id: string;
  title: string;
  description: string | null;
  role: string | null;
  status: ProjectStatus;
  start_date: string | null;
  end_date: string | null;
  repository_url: string | null;
  demo_url: string | null;
  is_pinned: boolean;
  skills: Skill[];
  created_at: string;
  updated_at: string;
}

export interface ProjectPayload {
  title: string;
  description?: string | null;
  role?: string | null;
  status: ProjectStatus;
  start_date?: string | null;
  end_date?: string | null;
  repository_url?: string | null;
  demo_url?: string | null;
  is_pinned: boolean;
  skill_ids: string[];
}

export interface PaginatedMeta {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export type LanguageProficiency =
  | "basic"
  | "conversational"
  | "professional"
  | "fluent"
  | "native";

export type PatentStatus = "filed" | "pending" | "granted" | "rejected";

export interface Achievement {
  id: string;
  title: string;
  issuer: string | null;
  date_achieved: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export type AchievementPayload = Omit<Achievement, "id" | "created_at" | "updated_at">;

export interface Certification {
  id: string;
  name: string;
  issuing_organization: string;
  issue_date: string | null;
  expiration_date: string | null;
  credential_id: string | null;
  credential_url: string | null;
  created_at: string;
  updated_at: string;
}

export type CertificationPayload = Omit<Certification, "id" | "created_at" | "updated_at">;

export interface Award {
  id: string;
  title: string;
  issuer: string | null;
  date_received: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export type AwardPayload = Omit<Award, "id" | "created_at" | "updated_at">;

export interface Research {
  id: string;
  title: string;
  publication_venue: string | null;
  publication_date: string | null;
  url: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export type ResearchPayload = Omit<Research, "id" | "created_at" | "updated_at">;

export interface VolunteerExperience {
  id: string;
  organization_name: string;
  role: string;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export type VolunteerExperiencePayload = Omit<
  VolunteerExperience,
  "id" | "created_at" | "updated_at"
>;

export interface LeadershipRole {
  id: string;
  organization_name: string;
  title: string;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export type LeadershipRolePayload = Omit<LeadershipRole, "id" | "created_at" | "updated_at">;

export interface Organization {
  id: string;
  organization_name: string;
  role: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export type OrganizationPayload = Omit<Organization, "id" | "created_at" | "updated_at">;

export interface Language {
  id: string;
  name: string;
  proficiency: LanguageProficiency;
  created_at: string;
  updated_at: string;
}

export type LanguagePayload = Omit<Language, "id" | "created_at" | "updated_at">;

export interface Reference {
  id: string;
  name: string;
  relationship: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export type ReferencePayload = Omit<Reference, "id" | "created_at" | "updated_at">;

export interface Hackathon {
  id: string;
  name: string;
  project_name: string | null;
  event_date: string | null;
  result: string | null;
  url: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export type HackathonPayload = Omit<Hackathon, "id" | "created_at" | "updated_at">;

export interface Competition {
  id: string;
  name: string;
  event_date: string | null;
  result: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export type CompetitionPayload = Omit<Competition, "id" | "created_at" | "updated_at">;

export interface Patent {
  id: string;
  title: string;
  patent_number: string | null;
  status: PatentStatus;
  filing_date: string | null;
  url: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export type PatentPayload = Omit<Patent, "id" | "created_at" | "updated_at">;
