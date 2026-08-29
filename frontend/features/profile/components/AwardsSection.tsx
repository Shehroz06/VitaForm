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
  useAwardList,
  useCreateAward,
  useDeleteAward,
  useUpdateAward,
} from "@/features/profile/hooks/use-awards";
import { type AwardFormValues, awardSchema } from "@/features/profile/schemas";
import type { Award } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

const emptyValues: AwardFormValues = {
  title: "",
  issuer: "",
  date_received: "",
  description: "",
};

export function AwardsSection() {
  const { data: items, isLoading, isError } = useAwardList();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Award | null>(null);

  const openCreate = () => {
    setEditing(null);
    setOpen(true);
  };
  const openEdit = (item: Award) => {
    setEditing(item);
    setOpen(true);
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Awards</h2>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm" onClick={openCreate}>
              <Plus className="size-4" /> Add
            </Button>
          </DialogTrigger>
          <AwardDialogContent editing={editing} onDone={() => setOpen(false)} />
        </Dialog>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading awards...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load awards.</p>}
      {items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No awards added yet.</p>
      )}

      <div className="flex flex-col gap-2">
        {items?.map((item) => (
          <AwardCard key={item.id} item={item} onEdit={() => openEdit(item)} />
        ))}
      </div>
    </section>
  );
}

function AwardCard({ item, onEdit }: { item: Award; onEdit: () => void }) {
  const deleteAward = useDeleteAward();

  const handleDelete = () => {
    if (!window.confirm(`Delete "${item.title}"?`)) return;
    deleteAward.mutate(item.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <div className="flex items-start justify-between rounded-xl bg-card p-3.5 ring-1 ring-foreground/10 transition-colors hover:bg-muted/40">
      <div>
        <p className="font-medium">{item.title}</p>
        <p className="text-sm text-muted-foreground">
          {[item.issuer, item.date_received].filter(Boolean).join(" · ")}
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

function AwardDialogContent({ editing, onDone }: { editing: Award | null; onDone: () => void }) {
  const createAward = useCreateAward();
  const updateAward = useUpdateAward();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AwardFormValues>({
    resolver: zodResolver(awardSchema),
    values: editing ? toFormValues(editing) : emptyValues,
  });
  const isPending = createAward.isPending || updateAward.isPending;

  const onSubmit = (values: AwardFormValues) => {
    const payload = {
      ...values,
      issuer: values.issuer || null,
      date_received: values.date_received || null,
      description: values.description || null,
    };

    const mutation = editing
      ? updateAward.mutateAsync({ id: editing.id, payload })
      : createAward.mutateAsync(payload);

    mutation
      .then(() => {
        toast.success(editing ? "Award updated." : "Award added.");
        onDone();
      })
      .catch((error: unknown) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to save.");
      });
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{editing ? "Edit award" : "Add award"}</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="title">Title</Label>
          <Input id="title" {...register("title")} />
          {errors.title && <p className="text-sm text-destructive">{errors.title.message}</p>}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="issuer">Issuer</Label>
            <Input id="issuer" {...register("issuer")} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="date_received">Date received</Label>
            <Input id="date_received" type="date" {...register("date_received")} />
          </div>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="description">Description</Label>
          <Textarea id="description" rows={3} {...register("description")} />
          <p className="text-xs text-muted-foreground">
            Wrap a phrase in **double asterisks** to render it bold on your resume.
          </p>
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

function toFormValues(item: Award): AwardFormValues {
  return {
    title: item.title,
    issuer: item.issuer ?? "",
    date_received: item.date_received ?? "",
    description: item.description ?? "",
  };
}
