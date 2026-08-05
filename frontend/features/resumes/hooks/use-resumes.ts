import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createCrudHooks } from "@/features/profile/hooks/use-crud-resource";
import { resumeService, resumeTemplateService } from "@/features/resumes/services/resume-service";
import type { Resume, ResumeCreatePayload, ResumeGeneratePayload } from "@/features/resumes/types";

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

export function useGenerateResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ResumeGeneratePayload) => resumeService.generate(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["resumes"] }),
  });
}
