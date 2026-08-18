import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { cvImportService } from "@/features/cv-import/services/cv-import-service";
import type { ImportConfirmPayload } from "@/features/cv-import/types";

const SESSIONS_KEY = ["cv-import-sessions"];

export function useImportSession(id: string) {
  return useQuery({
    queryKey: [...SESSIONS_KEY, id],
    queryFn: () => cvImportService.get(id),
  });
}

export function useUploadCv() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => cvImportService.upload(file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: SESSIONS_KEY }),
  });
}

export function useConfirmImportSession(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ImportConfirmPayload) => cvImportService.confirm(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SESSIONS_KEY });
      queryClient.invalidateQueries({ queryKey: [...SESSIONS_KEY, id] });
    },
  });
}

export function useRejectImportSession(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => cvImportService.reject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SESSIONS_KEY });
      queryClient.invalidateQueries({ queryKey: [...SESSIONS_KEY, id] });
    },
  });
}
