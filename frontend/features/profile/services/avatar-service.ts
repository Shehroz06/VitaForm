import type { FileAttachment } from "@/features/profile/types";
import { apiClient } from "@/services/api-client";

export const avatarService = {
  upload: (file: File) => apiClient.upload<FileAttachment>("/files/avatar", file),
  remove: () => apiClient.delete<void>("/files/avatar"),
};
