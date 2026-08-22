import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { resumeService, resumeTemplateService } from "@/features/resumes/services/resume-service";
import type {
  Resume,
  ResumeCreatePayload,
  ResumeGeneratePayload,
  ResumeStyle,
} from "@/features/resumes/types";

export const {
  useList: useResumeList,
  useCreate: useCreateResume,
  useUpdate: useUpdateResume,
  useDelete: useDeleteResume,
} = createCrudHooks<Resume, ResumeCreatePayload>("resumes", resumeService);

export function useResume(id: string) {
  return useQuery({
    queryKey: ["resumes", id],
    queryFn: () => resumeService.get(id),
    enabled: Boolean(id),
  });
}

export function useResumeTemplates() {
  return useQuery({ queryKey: ["resume-templates"], queryFn: resumeTemplateService.list });
}

/** Real render of a template filled with the caller's own profile, for the
 * pre-resume-creation template browser. `enabled` gates it on the relevant
 * card actually being visible/selected, so this doesn't fire a render per
 * template on every keystroke of picking a color. */
export function useTemplateSamplePreview(templateId: string, style: ResumeStyle, enabled: boolean) {
  return useQuery({
    queryKey: ["resume-templates", templateId, "sample-preview", style],
    queryFn: () => resumeTemplateService.previewSample(templateId, style),
    enabled: enabled && Boolean(templateId),
  });
}

export function useGenerateResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ResumeGeneratePayload) => resumeService.generate(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["resumes"] }),
  });
}
