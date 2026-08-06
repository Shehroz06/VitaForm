import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { coverLetterService, linkedinService } from "@/features/companion/services/companion-service";
import type { GenerateCoverLetterPayload, GenerateLinkedinPayload } from "@/features/companion/types";

const COVER_LETTERS_KEY = ["cover-letters"];
const LINKEDIN_KEY = ["linkedin-generations"];

export function useCoverLetterList() {
  return useQuery({ queryKey: COVER_LETTERS_KEY, queryFn: coverLetterService.list });
}

export function useGenerateCoverLetter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: GenerateCoverLetterPayload) => coverLetterService.generate(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: COVER_LETTERS_KEY }),
  });
}

export function useDeleteCoverLetter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => coverLetterService.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: COVER_LETTERS_KEY }),
  });
}

export function useLinkedinList() {
  return useQuery({ queryKey: LINKEDIN_KEY, queryFn: linkedinService.list });
}

export function useGenerateLinkedin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: GenerateLinkedinPayload) => linkedinService.generate(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: LINKEDIN_KEY }),
  });
}

export function useDeleteLinkedinGeneration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => linkedinService.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: LINKEDIN_KEY }),
  });
}
