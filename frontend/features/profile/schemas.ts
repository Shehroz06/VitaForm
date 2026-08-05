import { z } from "zod";

const url = z
  .string()
  .regex(/^https?:\/\/.+\..+$/, "Must be a valid URL starting with http:// or https://")
  .optional()
  .or(z.literal(""));

export const profileBasicsSchema = z.object({
  headline: z.string().max(150).optional().or(z.literal("")),
  bio: z.string().max(2000).optional().or(z.literal("")),
  phone: z.string().max(30).optional().or(z.literal("")),
  location: z.string().max(150).optional().or(z.literal("")),
  website_url: url,
  github_url: url,
  linkedin_url: url,
});

const dateOrder = <T extends { start_date?: string; end_date?: string | null }>(data: T) => {
  if (data.start_date && data.end_date) {
    return new Date(data.end_date) >= new Date(data.start_date);
  }
  return true;
};

export const educationSchema = z
  .object({
    institution_name: z.string().min(1, "Required").max(200),
    degree: z.string().min(1, "Required").max(150),
    field_of_study: z.string().max(150).optional().or(z.literal("")),
    grade: z.string().max(50).optional().or(z.literal("")),
    description: z.string().max(2000).optional().or(z.literal("")),
    start_date: z.string().min(1, "Required"),
    end_date: z.string().optional().or(z.literal("")),
    is_current: z.boolean(),
  })
  .refine(dateOrder, { message: "End date must be on or after start date.", path: ["end_date"] });

export const experienceSchema = z
  .object({
    company_name: z.string().min(1, "Required").max(200),
    job_title: z.string().min(1, "Required").max(150),
    employment_type: z.enum([
      "full_time",
      "part_time",
      "internship",
      "contract",
      "freelance",
      "volunteer",
    ]),
    location: z.string().max(150).optional().or(z.literal("")),
    description: z.string().max(2000).optional().or(z.literal("")),
    start_date: z.string().min(1, "Required"),
    end_date: z.string().optional().or(z.literal("")),
    is_current: z.boolean(),
  })
  .refine(dateOrder, { message: "End date must be on or after start date.", path: ["end_date"] });

export const skillSchema = z.object({
  name: z.string().min(1, "Required").max(100),
  category: z.enum(["technical", "soft", "tool", "other"]),
  level: z.enum(["beginner", "intermediate", "advanced", "expert"]).optional(),
});

export const projectSchema = z
  .object({
    title: z.string().min(1, "Required").max(200),
    description: z.string().max(2000).optional().or(z.literal("")),
    role: z.string().max(150).optional().or(z.literal("")),
    status: z.enum(["in_progress", "completed", "archived", "on_hold"]),
    start_date: z.string().optional().or(z.literal("")),
    end_date: z.string().optional().or(z.literal("")),
    repository_url: url,
    demo_url: url,
    is_pinned: z.boolean(),
    skill_ids: z.array(z.string()),
  })
  .refine(dateOrder, { message: "End date must be on or after start date.", path: ["end_date"] });

export const achievementSchema = z.object({
  title: z.string().min(1, "Required").max(200),
  issuer: z.string().max(200).optional().or(z.literal("")),
  date_achieved: z.string().optional().or(z.literal("")),
  description: z.string().max(2000).optional().or(z.literal("")),
});

export const certificationSchema = z
  .object({
    name: z.string().min(1, "Required").max(200),
    issuing_organization: z.string().min(1, "Required").max(200),
    issue_date: z.string().optional().or(z.literal("")),
    expiration_date: z.string().optional().or(z.literal("")),
    credential_id: z.string().max(150).optional().or(z.literal("")),
    credential_url: url,
  })
  .refine(
    (data) => {
      if (data.issue_date && data.expiration_date) {
        return new Date(data.expiration_date) >= new Date(data.issue_date);
      }
      return true;
    },
    { message: "Expiration date must be on or after issue date.", path: ["expiration_date"] },
  );

export const awardSchema = z.object({
  title: z.string().min(1, "Required").max(200),
  issuer: z.string().max(200).optional().or(z.literal("")),
  date_received: z.string().optional().or(z.literal("")),
  description: z.string().max(2000).optional().or(z.literal("")),
});

export const researchSchema = z.object({
  title: z.string().min(1, "Required").max(300),
  publication_venue: z.string().max(200).optional().or(z.literal("")),
  publication_date: z.string().optional().or(z.literal("")),
  url,
  description: z.string().max(2000).optional().or(z.literal("")),
});

export const volunteerExperienceSchema = z
  .object({
    organization_name: z.string().min(1, "Required").max(200),
    role: z.string().min(1, "Required").max(150),
    start_date: z.string().min(1, "Required"),
    end_date: z.string().optional().or(z.literal("")),
    is_current: z.boolean(),
    description: z.string().max(2000).optional().or(z.literal("")),
  })
  .refine(dateOrder, { message: "End date must be on or after start date.", path: ["end_date"] });

export const leadershipRoleSchema = z
  .object({
    organization_name: z.string().min(1, "Required").max(200),
    title: z.string().min(1, "Required").max(150),
    start_date: z.string().min(1, "Required"),
    end_date: z.string().optional().or(z.literal("")),
    is_current: z.boolean(),
    description: z.string().max(2000).optional().or(z.literal("")),
  })
  .refine(dateOrder, { message: "End date must be on or after start date.", path: ["end_date"] });

export const organizationSchema = z
  .object({
    organization_name: z.string().min(1, "Required").max(200),
    role: z.string().max(150).optional().or(z.literal("")),
    start_date: z.string().optional().or(z.literal("")),
    end_date: z.string().optional().or(z.literal("")),
    is_current: z.boolean(),
    description: z.string().max(2000).optional().or(z.literal("")),
  })
  .refine(dateOrder, { message: "End date must be on or after start date.", path: ["end_date"] });

export const languageSchema = z.object({
  name: z.string().min(1, "Required").max(100),
  proficiency: z.enum(["basic", "conversational", "professional", "fluent", "native"]),
});

export const referenceSchema = z.object({
  name: z.string().min(1, "Required").max(150),
  relationship: z.string().max(150).optional().or(z.literal("")),
  contact_email: z.email("Enter a valid email address.").optional().or(z.literal("")),
  contact_phone: z.string().max(30).optional().or(z.literal("")),
  description: z.string().max(2000).optional().or(z.literal("")),
});

export const hackathonSchema = z.object({
  name: z.string().min(1, "Required").max(200),
  project_name: z.string().max(200).optional().or(z.literal("")),
  event_date: z.string().optional().or(z.literal("")),
  result: z.string().max(150).optional().or(z.literal("")),
  url,
  description: z.string().max(2000).optional().or(z.literal("")),
});

export const competitionSchema = z.object({
  name: z.string().min(1, "Required").max(200),
  event_date: z.string().optional().or(z.literal("")),
  result: z.string().max(150).optional().or(z.literal("")),
  description: z.string().max(2000).optional().or(z.literal("")),
});

export const patentSchema = z.object({
  title: z.string().min(1, "Required").max(300),
  patent_number: z.string().max(100).optional().or(z.literal("")),
  status: z.enum(["filed", "pending", "granted", "rejected"]),
  filing_date: z.string().optional().or(z.literal("")),
  url,
  description: z.string().max(2000).optional().or(z.literal("")),
});

export type ProfileBasicsFormValues = z.infer<typeof profileBasicsSchema>;
export type EducationFormValues = z.infer<typeof educationSchema>;
export type ExperienceFormValues = z.infer<typeof experienceSchema>;
export type SkillFormValues = z.infer<typeof skillSchema>;
export type ProjectFormValues = z.infer<typeof projectSchema>;
export type AchievementFormValues = z.infer<typeof achievementSchema>;
export type CertificationFormValues = z.infer<typeof certificationSchema>;
export type AwardFormValues = z.infer<typeof awardSchema>;
export type ResearchFormValues = z.infer<typeof researchSchema>;
export type VolunteerExperienceFormValues = z.infer<typeof volunteerExperienceSchema>;
export type LeadershipRoleFormValues = z.infer<typeof leadershipRoleSchema>;
export type OrganizationFormValues = z.infer<typeof organizationSchema>;
export type LanguageFormValues = z.infer<typeof languageSchema>;
export type ReferenceFormValues = z.infer<typeof referenceSchema>;
export type HackathonFormValues = z.infer<typeof hackathonSchema>;
export type CompetitionFormValues = z.infer<typeof competitionSchema>;
export type PatentFormValues = z.infer<typeof patentSchema>;
