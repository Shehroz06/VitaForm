import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { VolunteerExperience, VolunteerExperiencePayload } from "@/features/profile/types";

export const volunteerExperienceService = createCrudService<
  VolunteerExperience,
  VolunteerExperiencePayload
>("/volunteer-experience");
