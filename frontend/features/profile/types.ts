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
