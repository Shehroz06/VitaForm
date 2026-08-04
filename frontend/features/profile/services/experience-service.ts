import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Experience, ExperiencePayload } from "@/features/profile/types";

export const experienceService = createCrudService<Experience, ExperiencePayload>("/experience");
