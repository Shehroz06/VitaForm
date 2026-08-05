import type {
  ExportedResumeFile,
  Resume,
  ResumeContent,
  ResumeCreatePayload,
  ResumeGeneratePayload,
  ResumeTemplate,
  ResumeUpdatePayload,
  ResumeVersion,
  ResumeVersionSummary,
} from "@/features/resumes/types";
import { apiClient } from "@/services/api-client";

export const resumeTemplateService = {
  list: () => apiClient.get<ResumeTemplate[]>("/resume-templates"),
};

export const resumeService = {
  list: () => apiClient.get<Resume[]>("/resumes"),
  create: (payload: ResumeCreatePayload) => apiClient.post<Resume>("/resumes", payload),
  generate: (payload: ResumeGeneratePayload) =>
    apiClient.post<ExportedResumeFile>("/resumes/generate", payload),
  get: (id: string) => apiClient.get<Resume>(`/resumes/${id}`),
  update: (id: string, payload: Partial<ResumeUpdatePayload>) =>
    apiClient.patch<Resume>(`/resumes/${id}`, payload),
  remove: (id: string) => apiClient.delete<{ message: string }>(`/resumes/${id}`),
  getContent: (id: string) => apiClient.get<ResumeVersion>(`/resumes/${id}/content`),
  updateContent: (id: string, content: ResumeContent) =>
    apiClient.put<ResumeVersion>(`/resumes/${id}/content`, content),
  listVersions: (id: string) => apiClient.get<ResumeVersionSummary[]>(`/resumes/${id}/versions`),
  getVersion: (id: string, versionId: string) =>
    apiClient.get<ResumeVersion>(`/resumes/${id}/versions/${versionId}`),
  export: (id: string) => apiClient.post<ExportedResumeFile>(`/resumes/${id}/export`),
};
