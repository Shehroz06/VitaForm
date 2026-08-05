import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { certificationService } from "@/features/profile/services/certification-service";
import type { Certification, CertificationPayload } from "@/features/profile/types";

export const {
  useList: useCertificationList,
  useCreate: useCreateCertification,
  useUpdate: useUpdateCertification,
  useDelete: useDeleteCertification,
} = createCrudHooks<Certification, CertificationPayload>("certifications", certificationService);
