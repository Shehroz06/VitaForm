import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Hackathon, HackathonPayload } from "@/features/profile/types";

export const hackathonService = createCrudService<Hackathon, HackathonPayload>("/hackathons");
