import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { leadershipRoleService } from "@/features/profile/services/leadership-role-service";
import type { LeadershipRole, LeadershipRolePayload } from "@/features/profile/types";

export const {
  useList: useLeadershipRoleList,
  useCreate: useCreateLeadershipRole,
  useUpdate: useUpdateLeadershipRole,
  useDelete: useDeleteLeadershipRole,
} = createCrudHooks<LeadershipRole, LeadershipRolePayload>(
  "leadership-roles",
  leadershipRoleService,
);
