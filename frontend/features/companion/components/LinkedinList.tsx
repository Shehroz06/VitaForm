"use client";

import { Copy, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  useDeleteLinkedinGeneration,
  useLinkedinList,
} from "@/features/companion/hooks/use-companion";
import type { LinkedinGeneration } from "@/features/companion/types";

export function LinkedinList() {
  const { data: generations, isLoading, isError } = useLinkedinList();

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading...</p>;
  if (isError) return <p className="text-sm text-destructive">Failed to load LinkedIn content.</p>;
  if (generations && generations.length === 0) {
    return <p className="text-sm text-muted-foreground">No LinkedIn content generated yet.</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      {generations?.map((generation) => (
        <LinkedinCard key={generation.id} generation={generation} />
      ))}
    </div>
  );
}

function LinkedinCard({ generation }: { generation: LinkedinGeneration }) {
  const deleteGeneration = useDeleteLinkedinGeneration();

  const handleCopy = async () => {
    await navigator.clipboard.writeText(`${generation.headline}\n\n${generation.about}`);
    toast.success("Copied to clipboard.");
  };

  const handleDelete = () => {
    if (!window.confirm("Delete this LinkedIn generation?")) return;
    deleteGeneration.mutate(generation.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <div className="flex flex-col gap-2 rounded-lg border p-3">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-medium">{generation.headline}</p>
          <p className="text-xs text-muted-foreground">
            {new Date(generation.created_at).toLocaleString()}
            {generation.target_role && ` · targeting ${generation.target_role}`}
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
      <p className="whitespace-pre-line text-sm text-muted-foreground">{generation.about}</p>
    </div>
  );
}
