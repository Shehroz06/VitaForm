import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Language, LanguagePayload } from "@/features/profile/types";

export const languageService = createCrudService<Language, LanguagePayload>("/languages");
