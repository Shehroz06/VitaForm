import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { jobService } from "@/features/jobs/services/job-service";
import type { JobDescriptionCreatePayload } from "@/features/jobs/types";

const JOBS_KEY = ["jobs"];

export function useJobList() {
  return useQuery({ queryKey: JOBS_KEY, queryFn: jobService.list });
}

export function useJob(id: string) {
  return useQuery({
    queryKey: ["jobs", id],
    queryFn: () => jobService.get(id),
    enabled: Boolean(id),
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: JobDescriptionCreatePayload) => jobService.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: JOBS_KEY }),
  });
}

export function useDeleteJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => jobService.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: JOBS_KEY }),
  });
}

export function useAnalyzeJob() {
  return useMutation({ mutationFn: (rawText: string) => jobService.analyze(rawText) });
}

export function useLatestAtsScore(jobId: string) {
  return useQuery({
    queryKey: ["jobs", jobId, "ats-score"],
    queryFn: () => jobService.getLatestAtsScore(jobId),
    enabled: Boolean(jobId),
    retry: false,
  });
}

export function useComputeAtsScore(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => jobService.computeAtsScore(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs", jobId, "ats-score"] });
    },
  });
}
