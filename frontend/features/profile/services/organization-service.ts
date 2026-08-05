import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Organization, OrganizationPayload } from "@/features/profile/types";

export const organizationService = createCrudService<Organization, OrganizationPayload>(
  "/organizations",
);
