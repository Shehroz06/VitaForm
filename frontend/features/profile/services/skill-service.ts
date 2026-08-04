import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Skill, SkillPayload } from "@/features/profile/types";

export const skillService = createCrudService<Skill, SkillPayload>("/skills");
