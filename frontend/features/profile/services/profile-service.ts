import { apiClient } from "@/services/api-client";
import type { Profile, ProfileUpdatePayload } from "@/features/profile/types";

export const profileService = {
  getMe: () => apiClient.get<Profile>("/profiles/me"),
  updateMe: (payload: ProfileUpdatePayload) =>
    apiClient.patch<Profile>("/profiles/me", payload),
};
