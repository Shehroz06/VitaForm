import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Research, ResearchPayload } from "@/features/profile/types";

export const researchService = createCrudService<Research, ResearchPayload>("/research");
