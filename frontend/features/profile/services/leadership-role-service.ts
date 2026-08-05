import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { LeadershipRole, LeadershipRolePayload } from "@/features/profile/types";

export const leadershipRoleService = createCrudService<LeadershipRole, LeadershipRolePayload>(
  "/leadership-roles",
);
