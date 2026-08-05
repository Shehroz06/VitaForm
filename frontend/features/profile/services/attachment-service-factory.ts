import { apiClient } from "@/services/api-client";

export function createAttachmentService<TItem>(resourcePath: string) {
  return {
    upload: (id: string, file: File) =>
      apiClient.upload<TItem>(`${resourcePath}/${id}/attachment`, file),
    remove: (id: string) =>
      apiClient.delete<{ message: string }>(`${resourcePath}/${id}/attachment`),
  };
}
