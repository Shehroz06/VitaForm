import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { resumeService } from "@/features/resumes/services/resume-service";
import type { ResumeContent, RewriteTextPayload } from "@/features/resumes/types";

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
 * explicit "save a checkpoint" behavior. The local builder state that was
 * just persisted is already the source of truth for the *editable* fields
 * on screen, so there's nothing to refetch there -- but the rendered
 * preview image (useResumePreview) is a server-computed artifact of that
 * content, so it does need invalidating.
 */
export function useAutosaveResumeContent(resumeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (content: ResumeContent) => resumeService.autosaveContent(resumeId, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes", resumeId, "preview"] });
    },
  });
}

/**
 * Rasterized PNGs of every page of the resume as it would actually export
 * (see backend's GET /resumes/{id}/preview) -- the single source of truth
 * the builder's live preview renders, rather than a second, hand-maintained
 * React implementation of each template that can silently drift from the
 * real one. Fetches page 1 first to learn the real page count, then the
 * rest in parallel, so a resume that overflows one page can actually be
 * scrolled through instead of silently cropping to page 1.
 * keepPreviousData avoids a flash-to-blank while a new render is in flight
 * after an edit.
 */
export function useResumePreview(resumeId: string) {
  return useQuery({
    queryKey: ["resumes", resumeId, "preview"],
    queryFn: async () => {
      const first = await resumeService.getPreview(resumeId, 1);
      const rest = await Promise.all(
        Array.from({ length: first.pageCount - 1 }, (_, i) =>
          resumeService.getPreview(resumeId, i + 2),
        ),
      );
      return { pages: [first, ...rest], pageCount: first.pageCount };
    },
    enabled: Boolean(resumeId),
    placeholderData: keepPreviousData,
  });
}

/**
 * Real backend render of a candidate template for the picker's comparison
 * cards -- `enabled` gates it on the picker dialog actually being open, so
 * this never fires (6 real renders, one per template) until the user asks
 * to compare templates.
 */
export function useTemplatePreview(resumeId: string, content: ResumeContent, templateId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["resumes", resumeId, "preview-with", templateId, content],
    queryFn: () => resumeService.previewWith(resumeId, content, templateId),
    enabled: enabled && Boolean(resumeId) && Boolean(templateId),
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

// No cache invalidation: stateless, doesn't touch saved content -- the
// caller applies the returned text to local builder state itself, the same
// as typing an edit, and it flows to the server on the next autosave.
export function useRewriteResumeText(resumeId: string) {
  return useMutation({
    mutationFn: (payload: RewriteTextPayload) => resumeService.rewriteText(resumeId, payload),
  });
}

export function useAutofitResume(resumeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => resumeService.autofit(resumeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes", resumeId, "preview"] });
    },
  });
}

export function useAutofitResumeAggressive(resumeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => resumeService.autofitAggressive(resumeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes", resumeId, "preview"] });
    },
  });
}
