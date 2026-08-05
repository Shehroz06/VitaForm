import { createAttachmentService } from "@/features/profile/services/attachment-service-factory";
import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Certification, CertificationPayload } from "@/features/profile/types";

export const certificationService = createCrudService<Certification, CertificationPayload>(
  "/certifications",
);

export const certificationAttachmentService = createAttachmentService<Certification>(
  "/certifications",
);
