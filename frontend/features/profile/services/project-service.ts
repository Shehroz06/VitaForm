import { createCrudService } from "@/features/profile/services/crud-service-factory";
import type { Project, ProjectPayload } from "@/features/profile/types";

export const projectService = createCrudService<Project, ProjectPayload>("/projects");
