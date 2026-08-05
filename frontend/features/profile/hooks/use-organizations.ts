import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { organizationService } from "@/features/profile/services/organization-service";
import type { Organization, OrganizationPayload } from "@/features/profile/types";

export const {
  useList: useOrganizationList,
  useCreate: useCreateOrganization,
  useUpdate: useUpdateOrganization,
  useDelete: useDeleteOrganization,
} = createCrudHooks<Organization, OrganizationPayload>("organizations", organizationService);
