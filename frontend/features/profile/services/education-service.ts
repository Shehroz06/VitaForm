import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Education, EducationPayload } from "@/features/profile/types";

export const educationService = createCrudService<Education, EducationPayload>("/education");
