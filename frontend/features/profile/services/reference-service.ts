import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Reference, ReferencePayload } from "@/features/profile/types";

export const referenceService = createCrudService<Reference, ReferencePayload>("/references");
