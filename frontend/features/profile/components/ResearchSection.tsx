"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  useCreateResearch,
  useDeleteResearch,
  useResearchList,
  useUpdateResearch,
} from "@/features/profile/hooks/use-research";
import { type ResearchFormValues, researchSchema } from "@/features/profile/schemas";
import type { Research } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

const emptyValues: ResearchFormValues = {
  title: "",
  publication_venue: "",
  publication_date: "",
  url: "",
  description: "",
};

export function ResearchSection() {
  const { data: items, isLoading, isError } = useResearchList();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Research | null>(null);

  const openCreate = () => {
    setEditing(null);
    setOpen(true);
  };
  const openEdit = (item: Research) => {
    setEditing(item);
    setOpen(true);
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Research</h2>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm" onClick={openCreate}>
              <Plus className="size-4" /> Add
            </Button>
          </DialogTrigger>
          <ResearchDialogContent editing={editing} onDone={() => setOpen(false)} />
        </Dialog>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading research...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load research.</p>}
      {items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No research added yet.</p>
      )}

      <div className="flex flex-col gap-2">
        {items?.map((item) => (
          <ResearchCard key={item.id} item={item} onEdit={() => openEdit(item)} />
        ))}
      </div>
    </section>
  );
}

function ResearchCard({ item, onEdit }: { item: Research; onEdit: () => void }) {
  const deleteResearch = useDeleteResearch();

  const handleDelete = () => {
    if (!window.confirm(`Delete "${item.title}"?`)) return;
    deleteResearch.mutate(item.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <div className="flex items-start justify-between rounded-lg border p-3">
      <div>
        <p className="font-medium">{item.title}</p>
        <p className="text-sm text-muted-foreground">
          {[item.publication_venue, item.publication_date].filter(Boolean).join(" · ")}
        </p>
        {item.description && (
          <p className="mt-1 text-sm text-muted-foreground">{item.description}</p>
        )}
      </div>
      <div className="flex gap-1">
        <Button variant="ghost" size="icon" onClick={onEdit} aria-label="Edit">
          <Pencil className="size-4" />
        </Button>
        <Button variant="ghost" size="icon" onClick={handleDelete} aria-label="Delete">
          <Trash2 className="size-4" />
        </Button>
      </div>
    </div>
  );
}

function ResearchDialogContent({
  editing,
  onDone,
}: {
  editing: Research | null;
  onDone: () => void;
}) {
  const createResearch = useCreateResearch();
  const updateResearch = useUpdateResearch();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResearchFormValues>({
    resolver: zodResolver(researchSchema),
    values: editing ? toFormValues(editing) : emptyValues,
  });
  const isPending = createResearch.isPending || updateResearch.isPending;

  const onSubmit = (values: ResearchFormValues) => {
    const payload = {
      ...values,
      publication_venue: values.publication_venue || null,
      publication_date: values.publication_date || null,
      url: values.url || null,
      description: values.description || null,
    };

    const mutation = editing
      ? updateResearch.mutateAsync({ id: editing.id, payload })
      : createResearch.mutateAsync(payload);

    mutation
      .then(() => {
        toast.success(editing ? "Research updated." : "Research added.");
        onDone();
      })
      .catch((error: unknown) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to save.");
      });
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{editing ? "Edit research" : "Add research"}</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="title">Title</Label>
          <Input id="title" {...register("title")} />
          {errors.title && <p className="text-sm text-destructive">{errors.title.message}</p>}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="publication_venue">Publication venue</Label>
            <Input id="publication_venue" {...register("publication_venue")} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="publication_date">Publication date</Label>
            <Input id="publication_date" type="date" {...register("publication_date")} />
          </div>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="url">URL</Label>
          <Input id="url" placeholder="https://" {...register("url")} />
          {errors.url && <p className="text-sm text-destructive">{errors.url.message}</p>}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="description">Description</Label>
          <Textarea id="description" rows={3} {...register("description")} />
        </div>
        <DialogFooter>
          <Button type="submit" disabled={isPending}>
            {isPending ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}

function toFormValues(item: Research): ResearchFormValues {
  return {
    title: item.title,
    publication_venue: item.publication_venue ?? "",
    publication_date: item.publication_date ?? "",
    url: item.url ?? "",
    description: item.description ?? "",
  };
}
