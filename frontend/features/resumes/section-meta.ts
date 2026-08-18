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
