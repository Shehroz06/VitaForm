import type {
  Achievement,
  Award,
  Certification,
  Competition,
  Education,
  Experience,
  Hackathon,
  Language,
  LeadershipRole,
  Organization,
  Patent,
  Project,
  Reference,
  Research,
  Skill,
  VolunteerExperience,
} from "@/features/profile/types";
import type { ResumePreviewItem } from "@/features/resumes/templates/types";

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

function formatMonth(iso: string): string {
  const [year, month] = iso.split("-");
  const label = MONTHS[Number(month) - 1];
  return label ? `${label} ${year}` : year;
}

function formatDateRange(
  start: string | null | undefined,
  end: string | null | undefined,
  isCurrent?: boolean,
): string | undefined {
  const startLabel = start ? formatMonth(start) : "";
  const endLabel = isCurrent ? "Present" : end ? formatMonth(end) : "";
  if (startLabel && endLabel) return `${startLabel} — ${endLabel}`;
  return startLabel || endLabel || undefined;
}

function formatSingleDate(date: string | null | undefined): string | undefined {
  return date ? formatMonth(date) : undefined;
}

function titleCase(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

const EMPLOYMENT_TYPE_LABELS: Record<Experience["employment_type"], string> = {
  full_time: "Full-time",
  part_time: "Part-time",
  internship: "Internship",
  contract: "Contract",
  freelance: "Freelance",
  volunteer: "Volunteer",
};

export function mapEducation(items: Education[] | undefined): ResumePreviewItem[] {
  return (items ?? []).map((e) => ({
    id: e.id,
    title: e.institution_name,
    subtitle: [e.degree, e.field_of_study].filter(Boolean).join(", ") || undefined,
    meta: e.grade ?? undefined,
    dateRange: formatDateRange(e.start_date, e.end_date, e.is_current),
    description: e.description,
  }));
}

export function mapExperience(items: Experience[] | undefined): ResumePreviewItem[] {
  return (items ?? []).map((e) => ({
    id: e.id,
    title: e.job_title,
    subtitle: e.company_name,
    meta: [EMPLOYMENT_TYPE_LABELS[e.employment_type], e.location].filter(Boolean).join(" · "),
    dateRange: formatDateRange(e.start_date, e.end_date, e.is_current),
    description: e.description,
  }));
}

export function mapProjects(items: Project[] | undefined): ResumePreviewItem[] {
  return (items ?? []).map((p) => ({
    id: p.id,
    title: p.title,
    subtitle: p.role ?? undefined,
    dateRange: formatDateRange(p.start_date, p.end_date, false),
    description: p.description,
    tags: p.skills.map((s) => s.name),
    links: [p.repository_url, p.demo_url].filter((v): v is string => Boolean(v)),
  }));
}

export function mapSkills(items: Skill[] | undefined): ResumePreviewItem[] {
  return (items ?? []).map((s) => ({
    id: s.id,
    title: s.name,
    meta: s.level ? titleCase(s.level) : undefined,
  }));
}

export function mapCertifications(items: Certification[] | undefined): ResumePreviewItem[] {
  return (items ?? []).map((c) => ({
    id: c.id,
    title: c.name,
    subtitle: c.issuing_organization,
    dateRange: formatSingleDate(c.issue_date),
    links: c.credential_url ? [c.credential_url] : undefined,
  }));
}

export function mapAchievements(items: Achievement[] | undefined): ResumePreviewItem[] {
  return (items ?? []).map((a) => ({
    id: a.id,
    title: a.title,
    subtitle: a.issuer ?? undefined,
    dateRange: formatSingleDate(a.date_achieved),
    description: a.description,
  }));
}

export function mapAwards(items: Award[] | undefined): ResumePreviewItem[] {
  return (items ?? []).map((a) => ({
    id: a.id,
    title: a.title,
    subtitle: a.issuer ?? undefined,
    dateRange: formatSingleDate(a.date_received),
    description: a.description,
  }));
}

export function mapResearch(items: Research[] | undefined): ResumePreviewItem[] {
  return (items ?? []).map((r) => ({
    id: r.id,
    title: r.title,
    subtitle: r.publication_venue ?? undefined,
    dateRange: formatSingleDate(r.publication_date),
    description: r.description,
    links: r.url ? [r.url] : undefined,
  }));
}

export function mapVolunteerExperience(
  items: VolunteerExperience[] | undefined,
): ResumePreviewItem[] {
  return (items ?? []).map((v) => ({
    id: v.id,
    title: v.role,
    subtitle: v.organization_name,
    dateRange: formatDateRange(v.start_date, v.end_date, v.is_current),
    description: v.description,
  }));
}

export function mapLeadershipRoles(items: LeadershipRole[] | undefined): ResumePreviewItem[] {
  return (items ?? []).map((l) => ({
    id: l.id,
    title: l.title,
    subtitle: l.organization_name,
    dateRange: formatDateRange(l.start_date, l.end_date, l.is_current),
    description: l.description,
  }));
}

export function mapOrganizations(items: Organization[] | undefined): ResumePreviewItem[] {
  return (items ?? []).map((o) => ({
    id: o.id,
    title: o.organization_name,
    subtitle: o.role ?? undefined,
    dateRange: formatDateRange(o.start_date, o.end_date, o.is_current),
    description: o.description,
  }));
}

export function mapLanguages(items: Language[] | undefined): ResumePreviewItem[] {
  return (items ?? []).map((l) => ({
    id: l.id,
    title: l.name,
    meta: titleCase(l.proficiency),
  }));
}

export function mapReferences(items: Reference[] | undefined): ResumePreviewItem[] {
  return (items ?? []).map((r) => ({
    id: r.id,
    title: r.name,
    subtitle: r.relationship ?? undefined,
    description: r.description,
    links: [r.contact_email, r.contact_phone].filter((v): v is string => Boolean(v)),
  }));
}

export function mapHackathons(items: Hackathon[] | undefined): ResumePreviewItem[] {
  return (items ?? []).map((h) => ({
    id: h.id,
    title: h.project_name ? `${h.name} · ${h.project_name}` : h.name,
    subtitle: h.result ?? undefined,
    dateRange: formatSingleDate(h.event_date),
    description: h.description,
    links: h.url ? [h.url] : undefined,
  }));
}

export function mapCompetitions(items: Competition[] | undefined): ResumePreviewItem[] {
  return (items ?? []).map((c) => ({
    id: c.id,
    title: c.name,
    subtitle: c.result ?? undefined,
    dateRange: formatSingleDate(c.event_date),
    description: c.description,
  }));
}

export function mapPatents(items: Patent[] | undefined): ResumePreviewItem[] {
  return (items ?? []).map((p) => ({
    id: p.id,
    title: p.patent_number ? `${p.title} (${p.patent_number})` : p.title,
    meta: titleCase(p.status),
    dateRange: formatSingleDate(p.filing_date),
    description: p.description,
    links: p.url ? [p.url] : undefined,
  }));
}

