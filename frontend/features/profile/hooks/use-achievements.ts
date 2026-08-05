import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { achievementService } from "@/features/profile/services/achievement-service";
import type { Achievement, AchievementPayload } from "@/features/profile/types";

export const {
  useList: useAchievementList,
  useCreate: useCreateAchievement,
  useUpdate: useUpdateAchievement,
  useDelete: useDeleteAchievement,
} = createCrudHooks<Achievement, AchievementPayload>("achievements", achievementService);
