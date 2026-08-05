import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Patent, PatentPayload } from "@/features/profile/types";

export const patentService = createCrudService<Patent, PatentPayload>("/patents");
