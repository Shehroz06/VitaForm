import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { researchService } from "@/features/profile/services/research-service";
import type { Research, ResearchPayload } from "@/features/profile/types";

export const {
  useList: useResearchList,
  useCreate: useCreateResearch,
  useUpdate: useUpdateResearch,
  useDelete: useDeleteResearch,
} = createCrudHooks<Research, ResearchPayload>("research", researchService);
