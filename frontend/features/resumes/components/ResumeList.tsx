"use client";

import { FileText, Trash2 } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useDeleteResume, useResumeList } from "@/features/resumes/hooks/use-resumes";
import type { Resume } from "@/features/resumes/types";

export function ResumeList() {
  const { data: resumes, isLoading, isError } = useResumeList();

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading resumes...</p>;
  if (isError) return <p className="text-sm text-destructive">Failed to load resumes.</p>;
  if (resumes && resumes.length === 0) {
    return <p className="text-sm text-muted-foreground">No resumes yet. Create your first one.</p>;
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
    <div className="flex items-center justify-between rounded-lg border p-3">
      <Link href={`/resumes/${resume.id}`} className="flex items-center gap-3">
        <FileText className="size-5 text-muted-foreground" />
        <div>
          <p className="font-medium">{resume.title}</p>
          <p className="text-xs text-muted-foreground">
            Version {resume.latest_version_number} · updated{" "}
            {new Date(resume.updated_at).toLocaleDateString()}
          </p>
        </div>
      </Link>
      <Button variant="ghost" size="icon" onClick={handleDelete} aria-label="Delete">
        <Trash2 className="size-4" />
      </Button>
    </div>
  );
}
