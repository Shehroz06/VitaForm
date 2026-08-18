export type ImportSessionStatus = "pending" | "confirmed" | "rejected" | "failed";

export interface ProposedData {
  bio: string | null;
  sections: Record<string, Record<string, unknown>[]>;
}

export interface ImportSession {
  id: string;
  source_filename: string;
  status: ImportSessionStatus;
  proposed_data: ProposedData;
  error_message: string | null;
  created_at: string;
}

export interface ImportConfirmPayload {
  bio: string | null;
  sections: Record<string, Record<string, unknown>[]>;
}

export interface ImportConfirmResult {
  created_counts: Record<string, number>;
  profile_headline_updated: boolean;
}

export const SECTION_LABELS: Record<string, string> = {
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

const TITLE_FIELDS = [
  "title",
  "name",
  "job_title",
  "company_name",
  "institution_name",
  "organization_name",
];
const SUBTITLE_FIELDS = ["company_name", "institution_name", "organization_name", "issuer"];

export function describeItem(item: Record<string, unknown>): { title: string; subtitle: string | null } {
  const title = TITLE_FIELDS.map((field) => item[field]).find((value) => typeof value === "string");
  const subtitleField = SUBTITLE_FIELDS.find(
    (field) => field !== TITLE_FIELDS.find((t) => item[t] === title) && typeof item[field] === "string",
  );
  return {
    title: typeof title === "string" ? title : JSON.stringify(item).slice(0, 80),
    subtitle: subtitleField ? (item[subtitleField] as string) : null,
  };
}
