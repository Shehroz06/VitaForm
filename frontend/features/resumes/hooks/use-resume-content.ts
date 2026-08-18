import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { resumeService } from "@/features/resumes/services/resume-service";
import type { ResumeContent } from "@/features/resumes/types";

export function useResumeContent(resumeId: string) {
  return useQuery({
    queryKey: ["resumes", resumeId, "content"],
    queryFn: () => resumeService.getContent(resumeId),
    enabled: Boolean(resumeId),
  });
}

export function useUpdateResumeContent(resumeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (content: ResumeContent) => resumeService.updateContent(resumeId, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes", resumeId, "content"] });
      queryClient.invalidateQueries({ queryKey: ["resumes", resumeId, "versions"] });
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
    },
  });
}

/**
 * Updates the current version's content in place (no new version row) --
 * the debounced autosave path, distinct from useUpdateResumeContent's
 * explicit "save a checkpoint" behavior. No query invalidation: the local
 * builder state that was just persisted is already the source of truth on
 * screen, so there's nothing to refetch.
 */
export function useAutosaveResumeContent(resumeId: string) {
  return useMutation({
    mutationFn: (content: ResumeContent) => resumeService.autosaveContent(resumeId, content),
  });
}

export function useResumeVersions(resumeId: string) {
  return useQuery({
    queryKey: ["resumes", resumeId, "versions"],
    queryFn: () => resumeService.listVersions(resumeId),
    enabled: Boolean(resumeId),
  });
}

export function useResumeVersion(resumeId: string, versionId: string | null) {
  return useQuery({
    queryKey: ["resumes", resumeId, "versions", versionId],
    queryFn: () => resumeService.getVersion(resumeId, versionId as string),
    enabled: Boolean(resumeId) && Boolean(versionId),
  });
}

export function useExportResume(resumeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => resumeService.export(resumeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes", resumeId, "versions"] });
    },
  });
}
