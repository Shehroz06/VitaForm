"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Paperclip, Pencil, Plus, Trash2, X } from "lucide-react";
import { useRef, useState } from "react";
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
  useRemoveAchievementAttachment,
  useUpdateAchievement,
  useUploadAchievementAttachment,
} from "@/features/profile/hooks/use-achievements";
import { type AchievementFormValues, achievementSchema } from "@/features/profile/schemas";
import type { Achievement } from "@/features/profile/types";
import { apiClient, ApiError } from "@/services/api-client";

const MAX_ATTACHMENT_SIZE_BYTES = 10 * 1024 * 1024;
const ALLOWED_ATTACHMENT_TYPES = new Set(["image/jpeg", "image/png", "application/pdf"]);

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
    <div className="flex flex-col gap-2 rounded-xl bg-card p-3.5 ring-1 ring-foreground/10 transition-colors hover:bg-muted/40">
      <div className="flex items-start justify-between">
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
      <AchievementAttachment item={item} />
    </div>
  );
}

function AchievementAttachment({ item }: { item: Achievement }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const uploadAttachment = useUploadAchievementAttachment();
  const removeAttachment = useRemoveAchievementAttachment();
  const isPending = uploadAttachment.isPending || removeAttachment.isPending;

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    if (!ALLOWED_ATTACHMENT_TYPES.has(file.type)) {
      toast.error("Attachment must be a JPG, PNG, or PDF file.");
      return;
    }
    if (file.size > MAX_ATTACHMENT_SIZE_BYTES) {
      toast.error("Attachment must be 10MB or smaller.");
      return;
    }

    uploadAttachment.mutate(
      { id: item.id, file },
      {
        onSuccess: () => toast.success("Attachment uploaded."),
        onError: (error) => {
          toast.error(error instanceof ApiError ? error.message : "Failed to upload attachment.");
        },
      },
    );
  };

  const handleRemove = () => {
    removeAttachment.mutate(item.id, {
      onSuccess: () => toast.success("Attachment removed."),
      onError: () => toast.error("Failed to remove attachment."),
    });
  };

  return (
    <div className="flex items-center gap-2 text-sm">
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,application/pdf"
        className="hidden"
        onChange={handleFileChange}
      />
      {item.file_id ? (
        <>
          <Paperclip className="size-4 text-muted-foreground" />
          <button
            type="button"
            className="text-primary underline"
            onClick={() =>
              apiClient
                .openInNewTab(`/files/${item.file_id}`)
                .catch(() => toast.error("Failed to open attachment."))
            }
          >
            View attachment
          </button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="size-6"
            disabled={isPending}
            onClick={handleRemove}
            aria-label="Remove attachment"
          >
            {removeAttachment.isPending ? (
              <Loader2 className="size-3 animate-spin" />
            ) : (
              <X className="size-3" />
            )}
          </Button>
        </>
      ) : (
        <Button
          type="button"
          variant="link"
          size="sm"
          className="h-auto p-0"
          disabled={isPending}
          onClick={() => inputRef.current?.click()}
        >
          {uploadAttachment.isPending ? (
            <Loader2 className="size-3 animate-spin" />
          ) : (
            <Paperclip className="size-3" />
          )}
          Attach file
        </Button>
      )}
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
