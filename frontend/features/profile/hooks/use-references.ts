import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { referenceService } from "@/features/profile/services/reference-service";
import type { Reference, ReferencePayload } from "@/features/profile/types";

export const {
  useList: useReferenceList,
  useCreate: useCreateReference,
  useUpdate: useUpdateReference,
  useDelete: useDeleteReference,
} = createCrudHooks<Reference, ReferencePayload>("references", referenceService);
