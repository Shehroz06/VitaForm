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

export type ProfileBasicsFormValues = z.infer<typeof profileBasicsSchema>;
export type EducationFormValues = z.infer<typeof educationSchema>;
export type ExperienceFormValues = z.infer<typeof experienceSchema>;
export type SkillFormValues = z.infer<typeof skillSchema>;
export type ProjectFormValues = z.infer<typeof projectSchema>;
