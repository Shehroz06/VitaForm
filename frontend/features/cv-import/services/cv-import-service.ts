import type {
  ImportConfirmPayload,
  ImportConfirmResult,
  ImportSession,
} from "@/features/cv-import/types";
import { apiClient } from "@/services/api-client";

export const cvImportService = {
  list: () => apiClient.get<ImportSession[]>("/cv-import/sessions"),
  get: (id: string) => apiClient.get<ImportSession>(`/cv-import/sessions/${id}`),
  upload: (file: File) => apiClient.upload<ImportSession>("/cv-import/sessions", file),
  confirm: (id: string, payload: ImportConfirmPayload) =>
    apiClient.post<ImportConfirmResult>(`/cv-import/sessions/${id}/confirm`, payload),
  reject: (id: string) => apiClient.post<ImportSession>(`/cv-import/sessions/${id}/reject`),
  remove: (id: string) => apiClient.delete<void>(`/cv-import/sessions/${id}`),
};
