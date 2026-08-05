import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Competition, CompetitionPayload } from "@/features/profile/types";

export const competitionService = createCrudService<Competition, CompetitionPayload>(
  "/competitions",
);
