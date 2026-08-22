import {
  Award,
  BadgeCheck,
  Briefcase,
  Building2,
  Code2,
  Contact2,
  FileBadge2,
  FileText,
  FlaskConical,
  FolderKanban,
  GraduationCap,
  HeartHandshake,
  Languages,
  Medal,
  Trophy,
  Users,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import type { SectionType } from "@/features/resumes/types";

export const SECTION_ORDER: SectionType[] = [
  "summary",
  "education",
  "experience",
  "projects",
  "skills",
  "certifications",
  "achievements",
  "awards",
  "research",
  "volunteer_experience",
  "leadership_roles",
  "organizations",
  "languages",
  "references",
  "hackathons",
  "competitions",
  "patents",
];

// Sections beyond this "core" set start collapsed in the builder so the
// editor reads as a document, not a 17-card wall of forms.
export const CORE_SECTIONS: SectionType[] = ["education", "experience", "projects", "skills"];

// Skills/Languages/References render as simple inline lists with no
// per-entry title/org/description of their own -- mirrors the backend's
// TITLE_FIELDS registry (section_registry.py), which is exactly the set of
// section types a title_override/subtitle_override/description_override
// is meaningful for. Every other section type has a "sub-heading" (its own
// title, and usually an org/institution line) worth editing per resume.
export const ITEM_EDITABLE_SECTIONS = new Set<SectionType>(
  SECTION_ORDER.filter(
    (type): type is Exclude<SectionType, "summary" | "skills" | "languages" | "references"> =>
      type !== "summary" && type !== "skills" && type !== "languages" && type !== "references",
  ),
);

export const SECTION_LABELS: Record<Exclude<SectionType, "summary">, string> = {
  education: "Education",
  experience: "Experience",
  projects: "Projects",
  skills: "Skills",
  certifications: "Certifications",
  achievements: "Achievements",
  awards: "Awards",
  research: "Research & Publications",
  volunteer_experience: "Volunteer Experience",
  leadership_roles: "Leadership",
  organizations: "Organizations",
  languages: "Languages",
  references: "References",
  hackathons: "Hackathons",
  competitions: "Competitions",
  patents: "Patents",
};

export const SECTION_ICONS: Record<SectionType, LucideIcon> = {
  summary: FileText,
  education: GraduationCap,
  experience: Briefcase,
  projects: FolderKanban,
  skills: Wrench,
  certifications: BadgeCheck,
  achievements: Trophy,
  awards: Award,
  research: FlaskConical,
  volunteer_experience: HeartHandshake,
  leadership_roles: Users,
  organizations: Building2,
  languages: Languages,
  references: Contact2,
  hackathons: Code2,
  competitions: Medal,
  patents: FileBadge2,
};
