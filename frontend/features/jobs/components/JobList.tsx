"use client";

import { Briefcase, Search, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useDeleteJob, useJobList, useLatestAtsScore } from "@/features/jobs/hooks/use-jobs";
import type { JobDescription } from "@/features/jobs/types";
import { cn } from "@/lib/utils";

export function JobList() {
  const { data: jobs, isLoading, isError } = useJobList();
  const [query, setQuery] = useState("");

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading jobs...</p>;
  if (isError) return <p className="text-sm text-destructive">Failed to load jobs.</p>;
  if (jobs && jobs.length === 0) {
    return <p className="text-sm text-muted-foreground">No jobs saved yet.</p>;
  }

  const filtered = query.trim()
    ? jobs?.filter((job) =>
        [job.title, job.company_name].filter(Boolean).join(" ").toLowerCase().includes(query.toLowerCase()),
      )
    : jobs;

  return (
    <div className="flex flex-col gap-3">
      {jobs && jobs.length > 4 && (
        <div className="relative">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search jobs by title or company..."
            className="pl-9"
          />
        </div>
      )}
      <div className="flex flex-col gap-2">
        {filtered?.map((job) => <JobCard key={job.id} job={job} />)}
        {filtered?.length === 0 && (
          <p className="text-sm text-muted-foreground">No jobs match &quot;{query}&quot;.</p>
        )}
      </div>
    </div>
  );
}

function JobCard({ job }: { job: JobDescription }) {
  const deleteJob = useDeleteJob();

  const handleDelete = () => {
    if (!window.confirm(`Delete "${job.title}"?`)) return;
    deleteJob.mutate(job.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <div className="flex items-center justify-between rounded-xl bg-card p-3.5 ring-1 ring-foreground/10 transition-colors hover:bg-muted/40">
      <Link href={`/jobs/${job.id}`} className="flex items-center gap-3">
        <Briefcase className="size-5 text-muted-foreground" />
        <div>
          <p className="font-medium">{job.title}</p>
          <p className="text-xs text-muted-foreground">
            {[
              job.company_name,
              job.location,
              `${job.required_skills.length} required skills identified`,
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
        </div>
      </Link>
      <div className="flex items-center gap-2">
        <AtsScoreBadge jobId={job.id} />
        <Button variant="ghost" size="icon" onClick={handleDelete} aria-label="Delete">
          <Trash2 className="size-4" />
        </Button>
      </div>
    </div>
  );
}

/**
 * Reuses the same ATS scoring engine/endpoint already computed on the job
 * detail page (features/jobs/ats_scorer.py via GET /jobs/{id}/ats-score) --
 * this is purely a read of whatever's already there, not a new compute
 * trigger, so opening the list never fires N parallel scoring calls.
 */
function AtsScoreBadge({ jobId }: { jobId: string }) {
  const { data: score, isLoading, isError } = useLatestAtsScore(jobId);

  if (isLoading) return null;
  if (isError || !score) {
    return <span className="text-xs text-muted-foreground">Not scored</span>;
  }

  const tone =
    score.overall_score >= 80
      ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400"
      : score.overall_score >= 40
        ? "bg-amber-500/15 text-amber-600 dark:text-amber-400"
        : "bg-destructive/15 text-destructive";

  return (
    <span className={cn("shrink-0 rounded-full px-2 py-1 text-xs font-semibold", tone)}>
      {score.overall_score}/100
    </span>
  );
}
