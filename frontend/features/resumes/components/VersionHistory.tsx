"use client";

import { Download, History } from "lucide-react";
import { toast } from "sonner";
import { useResumeVersions } from "@/features/resumes/hooks/use-resume-content";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/services/api-client";

export function VersionHistory({ resumeId }: { resumeId: string }) {
  const { data: versions, isLoading, isError } = useResumeVersions(resumeId);

  return (
    <div className="flex flex-col gap-3 rounded-xl bg-card p-4 ring-1 ring-foreground/10">
      <div className="flex items-center gap-2">
        <History className="size-4 text-muted-foreground" />
        <h2 className="text-sm font-medium text-foreground">Version history</h2>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading versions...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load version history.</p>}

      <div className="flex flex-col gap-1.5">
        {versions?.map((version) => (
          <div
            key={version.id}
            className="flex items-center justify-between rounded-lg px-2.5 py-2 text-sm transition-colors hover:bg-muted"
          >
            <div>
              <p className="font-medium text-foreground">Version {version.version_number}</p>
              <p className="text-xs text-muted-foreground">
                Saved {new Date(version.created_at).toLocaleString()}
                {version.rendered_at &&
                  ` · exported ${new Date(version.rendered_at).toLocaleString()}`}
              </p>
            </div>
            {version.rendered_file_id && (
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label="Download PDF"
                onClick={() =>
                  apiClient
                    .downloadFile(
                      `/files/${version.rendered_file_id}`,
                      `resume-v${version.version_number}.pdf`,
                    )
                    .catch(() => toast.error("Failed to download PDF."))
                }
              >
                <Download className="size-4" />
              </Button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
