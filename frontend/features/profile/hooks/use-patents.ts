import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { patentService } from "@/features/profile/services/patent-service";
import type { Patent, PatentPayload } from "@/features/profile/types";

export const {
  useList: usePatentList,
  useCreate: useCreatePatent,
  useUpdate: useUpdatePatent,
  useDelete: useDeletePatent,
} = createCrudHooks<Patent, PatentPayload>("patents", patentService);
