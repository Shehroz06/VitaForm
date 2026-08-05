"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
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
  useCreateLeadershipRole,
  useDeleteLeadershipRole,
  useLeadershipRoleList,
  useUpdateLeadershipRole,
} from "@/features/profile/hooks/use-leadership-roles";
import {
  type LeadershipRoleFormValues,
  leadershipRoleSchema,
} from "@/features/profile/schemas";
import type { LeadershipRole } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

const emptyValues: LeadershipRoleFormValues = {
  organization_name: "",
  title: "",
  start_date: "",
  end_date: "",
  is_current: false,
  description: "",
};

export function LeadershipRolesSection() {
  const { data: items, isLoading, isError } = useLeadershipRoleList();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<LeadershipRole | null>(null);

  const openCreate = () => {
    setEditing(null);
    setOpen(true);
  };
  const openEdit = (item: LeadershipRole) => {
    setEditing(item);
    setOpen(true);
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Leadership</h2>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm" onClick={openCreate}>
              <Plus className="size-4" /> Add
            </Button>
          </DialogTrigger>
          <LeadershipDialogContent editing={editing} onDone={() => setOpen(false)} />
        </Dialog>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading leadership roles...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load leadership roles.</p>}
      {items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No leadership roles added yet.</p>
      )}

      <div className="flex flex-col gap-2">
        {items?.map((item) => (
          <LeadershipCard key={item.id} item={item} onEdit={() => openEdit(item)} />
        ))}
      </div>
    </section>
  );
}

function LeadershipCard({ item, onEdit }: { item: LeadershipRole; onEdit: () => void }) {
  const deleteRole = useDeleteLeadershipRole();

  const handleDelete = () => {
    if (!window.confirm(`Delete "${item.title} at ${item.organization_name}"?`)) return;
    deleteRole.mutate(item.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <div className="flex items-start justify-between rounded-lg border p-3">
      <div>
        <p className="font-medium">{item.title}</p>
        <p className="text-sm text-muted-foreground">{item.organization_name}</p>
        <p className="text-xs text-muted-foreground">
          {item.start_date} – {item.is_current ? "Present" : (item.end_date ?? "—")}
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

function LeadershipDialogContent({
  editing,
  onDone,
}: {
  editing: LeadershipRole | null;
  onDone: () => void;
}) {
  const createRole = useCreateLeadershipRole();
  const updateRole = useUpdateLeadershipRole();
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<LeadershipRoleFormValues>({
    resolver: zodResolver(leadershipRoleSchema),
    values: editing ? toFormValues(editing) : emptyValues,
  });
  const isCurrent = watch("is_current");
  const isPending = createRole.isPending || updateRole.isPending;

  const onSubmit = (values: LeadershipRoleFormValues) => {
    const payload = {
      ...values,
      description: values.description || null,
      end_date: values.is_current ? null : values.end_date || null,
    };

    const mutation = editing
      ? updateRole.mutateAsync({ id: editing.id, payload })
      : createRole.mutateAsync(payload);

    mutation
      .then(() => {
        toast.success(editing ? "Leadership role updated." : "Leadership role added.");
        onDone();
      })
      .catch((error: unknown) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to save.");
      });
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{editing ? "Edit leadership role" : "Add leadership role"}</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="organization_name">Organization</Label>
            <Input id="organization_name" {...register("organization_name")} />
            {errors.organization_name && (
              <p className="text-sm text-destructive">{errors.organization_name.message}</p>
            )}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="title">Title</Label>
            <Input id="title" {...register("title")} />
            {errors.title && <p className="text-sm text-destructive">{errors.title.message}</p>}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="start_date">Start date</Label>
            <Input id="start_date" type="date" {...register("start_date")} />
            {errors.start_date && (
              <p className="text-sm text-destructive">{errors.start_date.message}</p>
            )}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="end_date">End date</Label>
            <Input id="end_date" type="date" disabled={isCurrent} {...register("end_date")} />
            {errors.end_date && (
              <p className="text-sm text-destructive">{errors.end_date.message}</p>
            )}
          </div>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <Checkbox
            checked={isCurrent}
            onCheckedChange={(checked) => setValue("is_current", checked === true)}
          />
          Currently in this role
        </label>
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

function toFormValues(item: LeadershipRole): LeadershipRoleFormValues {
  return {
    organization_name: item.organization_name,
    title: item.title,
    start_date: item.start_date,
    end_date: item.end_date ?? "",
    is_current: item.is_current,
    description: item.description ?? "",
  };
}
