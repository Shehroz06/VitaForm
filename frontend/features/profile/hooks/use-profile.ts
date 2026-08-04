import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { PROFILE_QUERY_KEY } from "@/features/profile/hooks/use-crud-resource";
import { profileService } from "@/features/profile/services/profile-service";
import type { ProfileUpdatePayload } from "@/features/profile/types";

export function useProfile() {
  return useQuery({ queryKey: PROFILE_QUERY_KEY, queryFn: profileService.getMe });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProfileUpdatePayload) => profileService.updateMe(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROFILE_QUERY_KEY }),
  });
}
