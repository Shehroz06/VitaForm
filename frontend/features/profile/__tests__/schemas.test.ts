import { describe, expect, it } from "vitest";
import { educationSchema, experienceSchema, profileBasicsSchema } from "@/features/profile/schemas";

const validEducation = {
  institution_name: "MIT",
  degree: "BSc",
  field_of_study: "Computer Science",
  grade: "",
  description: "",
  start_date: "2018-01-01",
  end_date: "2022-01-01",
  is_current: false,
};

describe("educationSchema date ordering", () => {
  it("accepts an end date on or after the start date", () => {
    const result = educationSchema.safeParse(validEducation);
    expect(result.success).toBe(true);
  });

  it("accepts an end date equal to the start date", () => {
    const result = educationSchema.safeParse({
      ...validEducation,
      end_date: validEducation.start_date,
    });
    expect(result.success).toBe(true);
  });

  it("rejects an end date before the start date", () => {
    const result = educationSchema.safeParse({
      ...validEducation,
      start_date: "2022-01-01",
      end_date: "2018-01-01",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      const endDateIssue = result.error.issues.find((issue) => issue.path.includes("end_date"));
      expect(endDateIssue?.message).toBe("End date must be on or after start date.");
    }
  });

  it("allows an omitted end date (still in progress)", () => {
    const { end_date: _endDate, ...withoutEndDate } = validEducation;
    const result = educationSchema.safeParse({ ...withoutEndDate, end_date: "" });
    expect(result.success).toBe(true);
  });
});

describe("experienceSchema date ordering", () => {
  const validExperience = {
    company_name: "Acme",
    job_title: "Engineer",
    employment_type: "full_time" as const,
    location: "",
    description: "",
    start_date: "2020-01-01",
    end_date: "2022-01-01",
    is_current: false,
  };

  it("rejects an end date before the start date", () => {
    const result = experienceSchema.safeParse({
      ...validExperience,
      start_date: "2022-01-01",
      end_date: "2020-01-01",
    });
    expect(result.success).toBe(false);
  });
});

describe("profileBasicsSchema URL validation", () => {
  const base = {
    first_name: "Test",
    last_name: "User",
    phone: "",
    location: "",
    website_url: "",
    github_url: "",
    linkedin_url: "",
  };

  it("accepts an empty string for optional URL fields", () => {
    expect(profileBasicsSchema.safeParse(base).success).toBe(true);
  });

  it("accepts a well-formed https URL", () => {
    const result = profileBasicsSchema.safeParse({
      ...base,
      github_url: "https://github.com/example",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a URL missing the scheme", () => {
    const result = profileBasicsSchema.safeParse({
      ...base,
      website_url: "example.com",
    });
    expect(result.success).toBe(false);
  });
});
