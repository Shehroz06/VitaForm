import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { educationService } from "@/features/profile/services/education-service";
import type { Education, EducationPayload } from "@/features/profile/types";

export const {
  useList: useEducationList,
  useCreate: useCreateEducation,
  useUpdate: useUpdateEducation,
  useDelete: useDeleteEducation,
} = createCrudHooks<Education, EducationPayload>("education", educationService);
