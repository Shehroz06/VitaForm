"use client";

import { Briefcase, Trash2 } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useDeleteJob, useJobList } from "@/features/jobs/hooks/use-jobs";
import type { JobDescription } from "@/features/jobs/types";

export function JobList() {
  const { data: jobs, isLoading, isError } = useJobList();

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading jobs...</p>;
  if (isError) return <p className="text-sm text-destructive">Failed to load jobs.</p>;
  if (jobs && jobs.length === 0) {
    return <p className="text-sm text-muted-foreground">No jobs saved yet.</p>;
  }

  return (
    <div className="flex flex-col gap-2">
      {jobs?.map((job) => (
        <JobCard key={job.id} job={job} />
      ))}
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
    <div className="flex items-center justify-between rounded-lg border p-3">
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
      <Button variant="ghost" size="icon" onClick={handleDelete} aria-label="Delete">
        <Trash2 className="size-4" />
      </Button>
    </div>
  );
}
