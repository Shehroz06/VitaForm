import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { hackathonService } from "@/features/profile/services/hackathon-service";
import type { Hackathon, HackathonPayload } from "@/features/profile/types";

export const {
  useList: useHackathonList,
  useCreate: useCreateHackathon,
  useUpdate: useUpdateHackathon,
  useDelete: useDeleteHackathon,
} = createCrudHooks<Hackathon, HackathonPayload>("hackathons", hackathonService);
