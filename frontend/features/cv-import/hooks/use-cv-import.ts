import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { cvImportService } from "@/features/cv-import/services/cv-import-service";
import type { ImportConfirmPayload } from "@/features/cv-import/types";
import { PROFILE_QUERY_KEY } from "@/features/profile/hooks/use-crud-resource";

const SESSIONS_KEY = ["cv-import-sessions"];
// Confirming an import can create rows in any of these resources depending
// on what the CV contained -- invalidate them all rather than tracking
// exactly which ones a given session touched.
const IMPORTABLE_RESOURCE_KEYS = [
  ["education"],
  ["experience"],
  ["projects"],
  ["skills"],
  PROFILE_QUERY_KEY,
];

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
      for (const queryKey of IMPORTABLE_RESOURCE_KEYS) {
        queryClient.invalidateQueries({ queryKey });
      }
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
