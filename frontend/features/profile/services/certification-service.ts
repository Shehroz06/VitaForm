import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Certification, CertificationPayload } from "@/features/profile/types";

export const certificationService = createCrudService<Certification, CertificationPayload>(
  "/certifications",
);
