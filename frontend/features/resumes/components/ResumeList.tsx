"use client";

import { Eye, FileText, Trash2 } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useDeleteResume, useResumeList } from "@/features/resumes/hooks/use-resumes";
import type { Resume } from "@/features/resumes/types";

export function ResumeList() {
  const { data: resumes, isLoading, isError } = useResumeList();

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading resumes...</p>;
  if (isError) return <p className="text-sm text-destructive">Failed to load resumes.</p>;
  if (resumes && resumes.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
          <FileText className="size-6 text-muted-foreground" />
          <p className="text-sm font-medium">No resumes yet</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {resumes?.map((resume) => (
        <ResumeCard key={resume.id} resume={resume} />
      ))}
    </div>
  );
}

function ResumeCard({ resume }: { resume: Resume }) {
  const deleteResume = useDeleteResume();

  const handleDelete = () => {
    if (!window.confirm(`Delete "${resume.title}"?`)) return;
    deleteResume.mutate(resume.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <div className="flex items-center justify-between rounded-xl bg-card p-3.5 ring-1 ring-foreground/10 transition-colors hover:bg-muted/40">
      <Link href={`/resumes/${resume.id}`} className="flex min-w-0 flex-1 items-center gap-3">
        <FileText className="size-5 shrink-0 text-muted-foreground" />
        <div className="min-w-0">
          <p className="truncate font-medium">{resume.title}</p>
          <p className="text-xs text-muted-foreground">
            Version {resume.latest_version_number} · updated{" "}
            {new Date(resume.updated_at).toLocaleDateString()}
          </p>
        </div>
      </Link>
      <div className="flex shrink-0 items-center gap-1">
        <Button variant="ghost" size="icon" asChild aria-label="Preview">
          <Link href={`/resumes/${resume.id}`}>
            <Eye className="size-4" />
          </Link>
        </Button>
        <Button variant="ghost" size="icon" onClick={handleDelete} aria-label="Delete">
          <Trash2 className="size-4" />
        </Button>
      </div>
    </div>
  );
}
