import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { volunteerExperienceService } from "@/features/profile/services/volunteer-experience-service";
import type { VolunteerExperience, VolunteerExperiencePayload } from "@/features/profile/types";

export const {
  useList: useVolunteerExperienceList,
  useCreate: useCreateVolunteerExperience,
  useUpdate: useUpdateVolunteerExperience,
  useDelete: useDeleteVolunteerExperience,
} = createCrudHooks<VolunteerExperience, VolunteerExperiencePayload>(
  "volunteer-experience",
  volunteerExperienceService,
);
