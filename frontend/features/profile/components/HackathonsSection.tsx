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
  useCreateHackathon,
  useDeleteHackathon,
  useHackathonList,
  useUpdateHackathon,
} from "@/features/profile/hooks/use-hackathons";
import { type HackathonFormValues, hackathonSchema } from "@/features/profile/schemas";
import type { Hackathon } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

const emptyValues: HackathonFormValues = {
  name: "",
  project_name: "",
  event_date: "",
  result: "",
  url: "",
  description: "",
};

export function HackathonsSection() {
  const { data: items, isLoading, isError } = useHackathonList();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Hackathon | null>(null);

  const openCreate = () => {
    setEditing(null);
    setOpen(true);
  };
  const openEdit = (item: Hackathon) => {
    setEditing(item);
    setOpen(true);
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Hackathons</h2>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm" onClick={openCreate}>
              <Plus className="size-4" /> Add
            </Button>
          </DialogTrigger>
          <HackathonDialogContent editing={editing} onDone={() => setOpen(false)} />
        </Dialog>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading hackathons...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load hackathons.</p>}
      {items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No hackathons added yet.</p>
      )}

      <div className="flex flex-col gap-2">
        {items?.map((item) => (
          <HackathonCard key={item.id} item={item} onEdit={() => openEdit(item)} />
        ))}
      </div>
    </section>
  );
}

function HackathonCard({ item, onEdit }: { item: Hackathon; onEdit: () => void }) {
  const deleteHackathon = useDeleteHackathon();

  const handleDelete = () => {
    if (!window.confirm(`Delete "${item.name}"?`)) return;
    deleteHackathon.mutate(item.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <div className="flex items-start justify-between rounded-lg border p-3">
      <div>
        <p className="font-medium">{item.name}</p>
        <p className="text-sm text-muted-foreground">
          {[item.project_name, item.event_date, item.result].filter(Boolean).join(" · ")}
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

function HackathonDialogContent({
  editing,
  onDone,
}: {
  editing: Hackathon | null;
  onDone: () => void;
}) {
  const createHackathon = useCreateHackathon();
  const updateHackathon = useUpdateHackathon();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<HackathonFormValues>({
    resolver: zodResolver(hackathonSchema),
    values: editing ? toFormValues(editing) : emptyValues,
  });
  const isPending = createHackathon.isPending || updateHackathon.isPending;

  const onSubmit = (values: HackathonFormValues) => {
    const payload = {
      ...values,
      project_name: values.project_name || null,
      event_date: values.event_date || null,
      result: values.result || null,
      url: values.url || null,
      description: values.description || null,
    };

    const mutation = editing
      ? updateHackathon.mutateAsync({ id: editing.id, payload })
      : createHackathon.mutateAsync(payload);

    mutation
      .then(() => {
        toast.success(editing ? "Hackathon updated." : "Hackathon added.");
        onDone();
      })
      .catch((error: unknown) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to save.");
      });
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{editing ? "Edit hackathon" : "Add hackathon"}</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name">Event name</Label>
            <Input id="name" {...register("name")} />
            {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="project_name">Project name</Label>
            <Input id="project_name" {...register("project_name")} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="event_date">Date</Label>
            <Input id="event_date" type="date" {...register("event_date")} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="result">Result</Label>
            <Input id="result" placeholder="Winner" {...register("result")} />
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

function toFormValues(item: Hackathon): HackathonFormValues {
  return {
    name: item.name,
    project_name: item.project_name ?? "",
    event_date: item.event_date ?? "",
    result: item.result ?? "",
    url: item.url ?? "",
    description: item.description ?? "",
  };
}
