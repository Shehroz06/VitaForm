"use client";

import { FileOutput, Sparkles } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  useComputeAtsScore,
  useJob,
  useLatestAtsScore,
} from "@/features/jobs/hooks/use-jobs";
import { ApiError } from "@/services/api-client";

export function JobDetail({ jobId }: { jobId: string }) {
  const { data: job, isLoading, isError } = useJob(jobId);
  const { data: score, isLoading: isScoreLoading, isError: hasNoScore } = useLatestAtsScore(jobId);
  const computeScore = useComputeAtsScore(jobId);

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading job...</p>;
  if (isError || !job) return <p className="text-sm text-destructive">Failed to load job.</p>;

  const handleComputeScore = () => {
    computeScore.mutate(undefined, {
      onError: (error) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to compute ATS score.");
      },
    });
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">{job.title}</h1>
        <p className="text-sm text-muted-foreground">
          {[job.company_name, job.location].filter(Boolean).join(" · ")}
        </p>
      </div>

      <Button asChild className="self-start">
        <Link href={`/resumes?jobId=${job.id}`}>
          <Sparkles className="size-4" /> Generate targeted resume
        </Link>
      </Button>

      <div className="flex flex-col gap-2">
        <h2 className="text-sm font-semibold text-muted-foreground">Required skills</h2>
        <div className="flex flex-wrap gap-1.5">
          {job.required_skills.length === 0 && (
            <p className="text-sm text-muted-foreground">None identified.</p>
          )}
          {job.required_skills.map((skill) => (
            <Badge key={skill} variant="default">
              {skill}
            </Badge>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <h2 className="text-sm font-semibold text-muted-foreground">Preferred skills</h2>
        <div className="flex flex-wrap gap-1.5">
          {job.preferred_skills.length === 0 && (
            <p className="text-sm text-muted-foreground">None identified.</p>
          )}
          {job.preferred_skills.map((skill) => (
            <Badge key={skill} variant="outline">
              {skill}
            </Badge>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-3 border-t pt-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">ATS match score</h2>
          <Button onClick={handleComputeScore} disabled={computeScore.isPending} variant="outline">
            <FileOutput className="size-4" />
            {computeScore.isPending ? "Scoring..." : "Compute ATS score"}
          </Button>
        </div>

        {isScoreLoading && <p className="text-sm text-muted-foreground">Loading...</p>}
        {hasNoScore && !isScoreLoading && (
          <p className="text-sm text-muted-foreground">
            No score yet -- click &quot;Compute ATS score&quot; to check your profile against this
            job.
          </p>
        )}
        {score && (
          <div className="flex flex-col gap-3 rounded-xl bg-card p-4 ring-1 ring-foreground/10">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold">{score.overall_score}</span>
              <span className="text-sm text-muted-foreground">/ 100</span>
            </div>
            {score.matched_skills.length > 0 && (
              <div>
                <p className="text-xs font-medium text-muted-foreground">Matched</p>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {score.matched_skills.map((skill) => (
                    <Badge key={skill} variant="default">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {score.missing_skills.length > 0 && (
              <div>
                <p className="text-xs font-medium text-muted-foreground">Missing</p>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {score.missing_skills.map((skill) => (
                    <Badge key={skill} variant="destructive">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {score.recommendations.length > 0 && (
              <ul className="list-inside list-disc text-sm text-muted-foreground">
                {score.recommendations.map((rec) => (
                  <li key={rec}>{rec}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      <div className="flex flex-col gap-2 border-t pt-6">
        <h2 className="text-sm font-semibold text-muted-foreground">Original job description</h2>
        <p className="whitespace-pre-line rounded-xl bg-card p-4 ring-1 ring-foreground/10 text-sm">{job.raw_text}</p>
      </div>
    </div>
  );
}
