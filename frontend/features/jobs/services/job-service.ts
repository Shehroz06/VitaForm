import type {
  AtsScore,
  JobAnalysis,
  JobDescription,
  JobDescriptionCreatePayload,
} from "@/features/jobs/types";
import { apiClient } from "@/services/api-client";

export const jobService = {
  list: () => apiClient.get<JobDescription[]>("/jobs"),
  create: (payload: JobDescriptionCreatePayload) =>
    apiClient.post<JobDescription>("/jobs", payload),
  get: (id: string) => apiClient.get<JobDescription>(`/jobs/${id}`),
  remove: (id: string) => apiClient.delete<void>(`/jobs/${id}`),
  analyze: (rawText: string) =>
    apiClient.post<JobAnalysis>("/jobs/analyze", { raw_text: rawText }),
  computeAtsScore: (id: string) => apiClient.post<AtsScore>(`/jobs/${id}/ats-score`),
  getLatestAtsScore: (id: string) => apiClient.get<AtsScore>(`/jobs/${id}/ats-score`),
};
