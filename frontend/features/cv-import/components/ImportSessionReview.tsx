"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  useConfirmImportSession,
  useImportSession,
  useRejectImportSession,
} from "@/features/cv-import/hooks/use-cv-import";
import { describeItem, SECTION_LABELS, type ImportSession } from "@/features/cv-import/types";
import { ApiError } from "@/services/api-client";

interface ReviewState {
  bioIncluded: boolean;
  sections: Record<string, boolean[]>;
}

function toReviewState(session: ImportSession): ReviewState {
  return {
    bioIncluded: session.proposed_data.bio != null,
    sections: Object.fromEntries(
      Object.entries(session.proposed_data.sections).map(([key, items]) => [
        key,
        items.map(() => true),
      ]),
    ),
  };
}

export function ImportSessionReview({ sessionId }: { sessionId: string }) {
  const { data: session, isLoading, isError } = useImportSession(sessionId);

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading import session...</p>;
  }
  if (isError || !session) {
    return <p className="text-sm text-destructive">Failed to load import session.</p>;
  }
  if (session.status === "failed") {
    return (
      <p className="text-sm text-destructive">
        {session.error_message ?? "This import failed to parse."}
      </p>
    );
  }
  if (session.status !== "pending") {
    return (
      <p className="text-sm text-muted-foreground">
        This import was already {session.status}. Upload a new PDF to import again.
      </p>
    );
  }

  return <ImportSessionReviewForm key={session.id} session={session} />;
}

function ImportSessionReviewForm({ session }: { session: ImportSession }) {
  const router = useRouter();
  const confirm = useConfirmImportSession(session.id);
  const reject = useRejectImportSession(session.id);
  const [state, setState] = useState<ReviewState>(() => toReviewState(session));

  const toggleBio = () => setState((prev) => ({ ...prev, bioIncluded: !prev.bioIncluded }));

  const toggleItem = (sectionKey: string, index: number) => {
    setState((prev) => ({
      ...prev,
      sections: {
        ...prev.sections,
        [sectionKey]: (prev.sections[sectionKey] ?? []).map((included, i) =>
          i === index ? !included : included,
        ),
      },
    }));
  };

  const handleConfirm = () => {
    const sections: Record<string, Record<string, unknown>[]> = {};
    for (const [key, items] of Object.entries(session.proposed_data.sections)) {
      const included = items.filter((_, index) => state.sections[key]?.[index]);
      if (included.length > 0) sections[key] = included;
    }
    confirm.mutate(
      { bio: state.bioIncluded ? session.proposed_data.bio : null, sections },
      {
        onSuccess: (result) => {
          const total = Object.values(result.created_counts).reduce((a, b) => a + b, 0);
          toast.success(`Added ${total} item${total === 1 ? "" : "s"} to your profile.`);
          router.push("/profile");
        },
        onError: (error) => {
          toast.error(error instanceof ApiError ? error.message : "Failed to confirm import.");
        },
      },
    );
  };

  const handleReject = () => {
    reject.mutate(undefined, {
      onSuccess: () => {
        toast.success("Import discarded.");
        router.push("/profile");
      },
      onError: (error) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to discard import.");
      },
    });
  };

  const sectionEntries = Object.entries(session.proposed_data.sections);
  const isEmpty = sectionEntries.length === 0 && !session.proposed_data.bio;

  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-muted-foreground">
        From <span className="font-medium">{session.source_filename}</span>. Uncheck anything you
        don&apos;t want added — nothing here is saved to your profile until you confirm.
      </p>

      {session.proposed_data.bio && (
        <div className="rounded-xl bg-card p-3.5 ring-1 ring-foreground/10 transition-colors hover:bg-muted/40">
          <label className="flex items-center gap-2 text-sm font-medium">
            <Checkbox checked={state.bioIncluded} onCheckedChange={toggleBio} />
            Bio (only added if your profile bio is currently empty)
          </label>
          <p className="mt-2 pl-6 text-sm text-muted-foreground">{session.proposed_data.bio}</p>
        </div>
      )}

      {isEmpty && (
        <p className="text-sm text-muted-foreground">
          No structured data was found in this PDF.
        </p>
      )}

      {sectionEntries.map(([key, items]) => (
        <div key={key} className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold text-muted-foreground">
            {SECTION_LABELS[key] ?? key}
          </h2>
          <div className="flex flex-col gap-2">
            {items.map((item, index) => {
              const { title, subtitle } = describeItem(item);
              return (
                <label
                  key={index}
                  className="flex items-start gap-2 rounded-xl bg-card p-3.5 ring-1 ring-foreground/10 transition-colors hover:bg-muted/40 text-sm"
                >
                  <Checkbox
                    checked={state.sections[key]?.[index] ?? true}
                    onCheckedChange={() => toggleItem(key, index)}
                  />
                  <span>
                    <span className="font-medium">{title}</span>
                    {subtitle && <span className="text-muted-foreground"> — {subtitle}</span>}
                  </span>
                </label>
              );
            })}
          </div>
        </div>
      ))}

      <div className="flex gap-3">
        <Button onClick={handleConfirm} disabled={confirm.isPending || isEmpty}>
          {confirm.isPending ? "Adding..." : "Confirm & add to profile"}
        </Button>
        <Button variant="outline" onClick={handleReject} disabled={reject.isPending}>
          Discard
        </Button>
      </div>
    </div>
  );
}
