import { useMutation, useQueryClient } from "@tanstack/react-query";
import { PROFILE_QUERY_KEY } from "@/features/profile/hooks/use-crud-resource";
import { avatarService } from "@/features/profile/services/avatar-service";

export function useUploadAvatar() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => avatarService.upload(file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROFILE_QUERY_KEY }),
  });
}

export function useRemoveAvatar() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => avatarService.remove(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROFILE_QUERY_KEY }),
  });
}
