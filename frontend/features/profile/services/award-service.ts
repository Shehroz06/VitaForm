import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Award, AwardPayload } from "@/features/profile/types";

export const awardService = createCrudService<Award, AwardPayload>("/awards");
