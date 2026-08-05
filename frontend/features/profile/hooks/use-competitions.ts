import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { competitionService } from "@/features/profile/services/competition-service";
import type { Competition, CompetitionPayload } from "@/features/profile/types";

export const {
  useList: useCompetitionList,
  useCreate: useCreateCompetition,
  useUpdate: useUpdateCompetition,
  useDelete: useDeleteCompetition,
} = createCrudHooks<Competition, CompetitionPayload>("competitions", competitionService);
