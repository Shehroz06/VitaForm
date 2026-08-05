"use client";

import { Download, FileOutput } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useExportResume, useResumeVersions } from "@/features/resumes/hooks/use-resume-content";
import { ApiError } from "@/services/api-client";

export function VersionHistory({ resumeId }: { resumeId: string }) {
  const { data: versions, isLoading, isError } = useResumeVersions(resumeId);
  const exportResume = useExportResume(resumeId);

  const handleExport = () => {
    exportResume.mutate(undefined, {
      onSuccess: (file) => {
        toast.success("Resume exported.");
        window.open(file.url, "_blank", "noopener,noreferrer");
      },
      onError: (error) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to export resume.");
      },
    });
  };

  return (
    <div className="flex flex-col gap-3 border-t pt-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Version history</h2>
        <Button onClick={handleExport} disabled={exportResume.isPending}>
          <FileOutput className="size-4" />
          {exportResume.isPending ? "Exporting..." : "Export PDF"}
        </Button>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading versions...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load version history.</p>}

      <div className="flex flex-col gap-2">
        {versions?.map((version) => (
          <div
            key={version.id}
            className="flex items-center justify-between rounded-lg border p-3 text-sm"
          >
            <div>
              <p className="font-medium">Version {version.version_number}</p>
              <p className="text-xs text-muted-foreground">
                Saved {new Date(version.created_at).toLocaleString()}
                {version.rendered_at &&
                  ` · exported ${new Date(version.rendered_at).toLocaleString()}`}
              </p>
            </div>
            {version.rendered_file_id && (
              <Button variant="ghost" size="icon" asChild aria-label="Download PDF">
                <a
                  href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/files/${version.rendered_file_id}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  <Download className="size-4" />
                </a>
              </Button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
