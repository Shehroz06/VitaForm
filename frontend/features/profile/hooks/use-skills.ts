import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { skillService } from "@/features/profile/services/skill-service";
import type { Skill, SkillPayload } from "@/features/profile/types";

export const {
  useList: useSkillList,
  useCreate: useCreateSkill,
  useUpdate: useUpdateSkill,
  useDelete: useDeleteSkill,
} = createCrudHooks<Skill, SkillPayload>("skills", skillService);
