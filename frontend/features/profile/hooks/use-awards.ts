import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { awardService } from "@/features/profile/services/award-service";
import type { Award, AwardPayload } from "@/features/profile/types";

export const {
  useList: useAwardList,
  useCreate: useCreateAward,
  useUpdate: useUpdateAward,
  useDelete: useDeleteAward,
} = createCrudHooks<Award, AwardPayload>("awards", awardService);
