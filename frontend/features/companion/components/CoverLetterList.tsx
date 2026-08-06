"use client";

import { Copy, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useDeleteCoverLetter, useCoverLetterList } from "@/features/companion/hooks/use-companion";
import type { CoverLetter } from "@/features/companion/types";

export function CoverLetterList() {
  const { data: letters, isLoading, isError } = useCoverLetterList();

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading cover letters...</p>;
  if (isError) return <p className="text-sm text-destructive">Failed to load cover letters.</p>;
  if (letters && letters.length === 0) {
    return <p className="text-sm text-muted-foreground">No cover letters generated yet.</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      {letters?.map((letter) => (
        <CoverLetterCard key={letter.id} letter={letter} />
      ))}
    </div>
  );
}

function CoverLetterCard({ letter }: { letter: CoverLetter }) {
  const deleteCoverLetter = useDeleteCoverLetter();

  const handleCopy = async () => {
    await navigator.clipboard.writeText(letter.body);
    toast.success("Copied to clipboard.");
  };

  const handleDelete = () => {
    if (!window.confirm(`Delete the cover letter for "${letter.company_name}"?`)) return;
    deleteCoverLetter.mutate(letter.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <div className="flex flex-col gap-2 rounded-lg border p-3">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-medium">
            {letter.role_title} · {letter.company_name}
          </p>
          <p className="text-xs text-muted-foreground">
            {new Date(letter.created_at).toLocaleString()}
          </p>
        </div>
        <div className="flex gap-1">
          <Button variant="ghost" size="icon" onClick={handleCopy} aria-label="Copy">
            <Copy className="size-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleDelete} aria-label="Delete">
            <Trash2 className="size-4" />
          </Button>
        </div>
      </div>
      <p className="whitespace-pre-line text-sm text-muted-foreground">{letter.body}</p>
    </div>
  );
}
