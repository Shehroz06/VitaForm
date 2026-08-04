import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { experienceService } from "@/features/profile/services/experience-service";
import type { Experience, ExperiencePayload } from "@/features/profile/types";

export const {
  useList: useExperienceList,
  useCreate: useCreateExperience,
  useUpdate: useUpdateExperience,
  useDelete: useDeleteExperience,
} = createCrudHooks<Experience, ExperiencePayload>("experience", experienceService);
