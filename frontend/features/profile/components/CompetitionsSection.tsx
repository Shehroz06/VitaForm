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
  useCompetitionList,
  useCreateCompetition,
  useDeleteCompetition,
  useUpdateCompetition,
} from "@/features/profile/hooks/use-competitions";
import { type CompetitionFormValues, competitionSchema } from "@/features/profile/schemas";
import type { Competition } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

const emptyValues: CompetitionFormValues = {
  name: "",
  event_date: "",
  result: "",
  description: "",
};

export function CompetitionsSection() {
  const { data: items, isLoading, isError } = useCompetitionList();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Competition | null>(null);

  const openCreate = () => {
    setEditing(null);
    setOpen(true);
  };
  const openEdit = (item: Competition) => {
    setEditing(item);
    setOpen(true);
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Competitions</h2>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm" onClick={openCreate}>
              <Plus className="size-4" /> Add
            </Button>
          </DialogTrigger>
          <CompetitionDialogContent editing={editing} onDone={() => setOpen(false)} />
        </Dialog>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading competitions...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load competitions.</p>}
      {items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No competitions added yet.</p>
      )}

      <div className="flex flex-col gap-2">
        {items?.map((item) => (
          <CompetitionCard key={item.id} item={item} onEdit={() => openEdit(item)} />
        ))}
      </div>
    </section>
  );
}

function CompetitionCard({ item, onEdit }: { item: Competition; onEdit: () => void }) {
  const deleteCompetition = useDeleteCompetition();

  const handleDelete = () => {
    if (!window.confirm(`Delete "${item.name}"?`)) return;
    deleteCompetition.mutate(item.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <div className="flex items-start justify-between rounded-xl bg-card p-3.5 ring-1 ring-foreground/10 transition-colors hover:bg-muted/40">
      <div>
        <p className="font-medium">{item.name}</p>
        <p className="text-sm text-muted-foreground">
          {[item.event_date, item.result].filter(Boolean).join(" · ")}
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

function CompetitionDialogContent({
  editing,
  onDone,
}: {
  editing: Competition | null;
  onDone: () => void;
}) {
  const createCompetition = useCreateCompetition();
  const updateCompetition = useUpdateCompetition();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CompetitionFormValues>({
    resolver: zodResolver(competitionSchema),
    values: editing ? toFormValues(editing) : emptyValues,
  });
  const isPending = createCompetition.isPending || updateCompetition.isPending;

  const onSubmit = (values: CompetitionFormValues) => {
    const payload = {
      ...values,
      event_date: values.event_date || null,
      result: values.result || null,
      description: values.description || null,
    };

    const mutation = editing
      ? updateCompetition.mutateAsync({ id: editing.id, payload })
      : createCompetition.mutateAsync(payload);

    mutation
      .then(() => {
        toast.success(editing ? "Competition updated." : "Competition added.");
        onDone();
      })
      .catch((error: unknown) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to save.");
      });
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{editing ? "Edit competition" : "Add competition"}</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="name">Name</Label>
          <Input id="name" {...register("name")} />
          {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="event_date">Date</Label>
            <Input id="event_date" type="date" {...register("event_date")} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="result">Result</Label>
            <Input id="result" placeholder="Finalist" {...register("result")} />
          </div>
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

function toFormValues(item: Competition): CompetitionFormValues {
  return {
    name: item.name,
    event_date: item.event_date ?? "",
    result: item.result ?? "",
    description: item.description ?? "",
  };
}
