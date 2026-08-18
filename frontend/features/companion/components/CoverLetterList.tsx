"use client";

import { Copy, Search, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useDeleteCoverLetter, useCoverLetterList } from "@/features/companion/hooks/use-companion";
import type { CoverLetter } from "@/features/companion/types";

export function CoverLetterList() {
  const { data: letters, isLoading, isError } = useCoverLetterList();
  const [query, setQuery] = useState("");

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading cover letters...</p>;
  if (isError) return <p className="text-sm text-destructive">Failed to load cover letters.</p>;
  if (letters && letters.length === 0) {
    return <p className="text-sm text-muted-foreground">No cover letters generated yet.</p>;
  }

  const filtered = query.trim()
    ? letters?.filter((letter) =>
        `${letter.role_title} ${letter.company_name}`.toLowerCase().includes(query.toLowerCase()),
      )
    : letters;

  return (
    <div className="flex flex-col gap-3">
      {letters && letters.length > 4 && (
        <div className="relative">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by role or company..."
            className="pl-9"
          />
        </div>
      )}
      <div className="flex flex-col gap-3">
        {filtered?.map((letter) => (
          <CoverLetterCard key={letter.id} letter={letter} />
        ))}
        {filtered?.length === 0 && (
          <p className="text-sm text-muted-foreground">No cover letters match &quot;{query}&quot;.</p>
        )}
      </div>
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
    <div className="flex flex-col gap-2 rounded-xl bg-card p-3.5 ring-1 ring-foreground/10 transition-colors hover:bg-muted/40">
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
