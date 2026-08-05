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
  useAchievementList,
  useCreateAchievement,
  useDeleteAchievement,
  useUpdateAchievement,
} from "@/features/profile/hooks/use-achievements";
import { type AchievementFormValues, achievementSchema } from "@/features/profile/schemas";
import type { Achievement } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

const emptyValues: AchievementFormValues = {
  title: "",
  issuer: "",
  date_achieved: "",
  description: "",
};

export function AchievementsSection() {
  const { data: items, isLoading, isError } = useAchievementList();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Achievement | null>(null);

  const openCreate = () => {
    setEditing(null);
    setOpen(true);
  };
  const openEdit = (item: Achievement) => {
    setEditing(item);
    setOpen(true);
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Achievements</h2>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm" onClick={openCreate}>
              <Plus className="size-4" /> Add
            </Button>
          </DialogTrigger>
          <AchievementDialogContent editing={editing} onDone={() => setOpen(false)} />
        </Dialog>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading achievements...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load achievements.</p>}
      {items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No achievements added yet.</p>
      )}

      <div className="flex flex-col gap-2">
        {items?.map((item) => (
          <AchievementCard key={item.id} item={item} onEdit={() => openEdit(item)} />
        ))}
      </div>
    </section>
  );
}

function AchievementCard({ item, onEdit }: { item: Achievement; onEdit: () => void }) {
  const deleteAchievement = useDeleteAchievement();

  const handleDelete = () => {
    if (!window.confirm(`Delete "${item.title}"?`)) return;
    deleteAchievement.mutate(item.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <div className="flex items-start justify-between rounded-lg border p-3">
      <div>
        <p className="font-medium">{item.title}</p>
        <p className="text-sm text-muted-foreground">
          {[item.issuer, item.date_achieved].filter(Boolean).join(" · ")}
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

function AchievementDialogContent({
  editing,
  onDone,
}: {
  editing: Achievement | null;
  onDone: () => void;
}) {
  const createAchievement = useCreateAchievement();
  const updateAchievement = useUpdateAchievement();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AchievementFormValues>({
    resolver: zodResolver(achievementSchema),
    values: editing ? toFormValues(editing) : emptyValues,
  });
  const isPending = createAchievement.isPending || updateAchievement.isPending;

  const onSubmit = (values: AchievementFormValues) => {
    const payload = {
      ...values,
      issuer: values.issuer || null,
      date_achieved: values.date_achieved || null,
      description: values.description || null,
    };

    const mutation = editing
      ? updateAchievement.mutateAsync({ id: editing.id, payload })
      : createAchievement.mutateAsync(payload);

    mutation
      .then(() => {
        toast.success(editing ? "Achievement updated." : "Achievement added.");
        onDone();
      })
      .catch((error: unknown) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to save.");
      });
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{editing ? "Edit achievement" : "Add achievement"}</DialogTitle>
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
            <Label htmlFor="date_achieved">Date</Label>
            <Input id="date_achieved" type="date" {...register("date_achieved")} />
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

function toFormValues(item: Achievement): AchievementFormValues {
  return {
    title: item.title,
    issuer: item.issuer ?? "",
    date_achieved: item.date_achieved ?? "",
    description: item.description ?? "",
  };
}
