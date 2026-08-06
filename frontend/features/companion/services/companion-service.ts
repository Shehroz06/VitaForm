import type {
  CoverLetter,
  GenerateCoverLetterPayload,
  GenerateLinkedinPayload,
  LinkedinGeneration,
} from "@/features/companion/types";
import { apiClient } from "@/services/api-client";

export const coverLetterService = {
  list: () => apiClient.get<CoverLetter[]>("/cover-letters"),
  get: (id: string) => apiClient.get<CoverLetter>(`/cover-letters/${id}`),
  remove: (id: string) => apiClient.delete<{ message: string }>(`/cover-letters/${id}`),
  generate: (payload: GenerateCoverLetterPayload) =>
    apiClient.post<CoverLetter>("/ai/generate-cover-letter", payload),
};

export const linkedinService = {
  list: () => apiClient.get<LinkedinGeneration[]>("/linkedin-generations"),
  get: (id: string) => apiClient.get<LinkedinGeneration>(`/linkedin-generations/${id}`),
  remove: (id: string) => apiClient.delete<{ message: string }>(`/linkedin-generations/${id}`),
  generate: (payload: GenerateLinkedinPayload) =>
    apiClient.post<LinkedinGeneration>("/ai/generate-linkedin", payload),
};
