import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { projectService } from "@/features/profile/services/project-service";
import type { Project, ProjectPayload } from "@/features/profile/types";

export const {
  useList: useProjectList,
  useCreate: useCreateProject,
  useUpdate: useUpdateProject,
  useDelete: useDeleteProject,
} = createCrudHooks<Project, ProjectPayload>("projects", projectService);
