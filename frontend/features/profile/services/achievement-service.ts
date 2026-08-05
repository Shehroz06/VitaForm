import { createAttachmentService } from "@/features/profile/services/attachment-service-factory";
import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Achievement, AchievementPayload } from "@/features/profile/types";

export const achievementService = createCrudService<Achievement, AchievementPayload>(
  "/achievements",
);

export const achievementAttachmentService = createAttachmentService<Achievement>("/achievements");
