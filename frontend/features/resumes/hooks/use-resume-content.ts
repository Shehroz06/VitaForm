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
