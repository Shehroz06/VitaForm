import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Achievement, AchievementPayload } from "@/features/profile/types";

export const achievementService = createCrudService<Achievement, AchievementPayload>(
  "/achievements",
);
