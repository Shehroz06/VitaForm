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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  useCreatePatent,
  useDeletePatent,
  usePatentList,
  useUpdatePatent,
} from "@/features/profile/hooks/use-patents";
import { type PatentFormValues, patentSchema } from "@/features/profile/schemas";
import type { Patent, PatentStatus } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

const STATUS_LABELS: Record<PatentStatus, string> = {
  filed: "Filed",
  pending: "Pending",
  granted: "Granted",
  rejected: "Rejected",
};

const emptyValues: PatentFormValues = {
  title: "",
  patent_number: "",
  status: "filed",
  filing_date: "",
  url: "",
  description: "",
};

export function PatentsSection() {
  const { data: items, isLoading, isError } = usePatentList();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Patent | null>(null);

  const openCreate = () => {
    setEditing(null);
    setOpen(true);
  };
  const openEdit = (item: Patent) => {
    setEditing(item);
    setOpen(true);
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Patents</h2>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm" onClick={openCreate}>
              <Plus className="size-4" /> Add
            </Button>
          </DialogTrigger>
          <PatentDialogContent editing={editing} onDone={() => setOpen(false)} />
        </Dialog>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading patents...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load patents.</p>}
      {items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No patents added yet.</p>
      )}

      <div className="flex flex-col gap-2">
        {items?.map((item) => (
          <PatentCard key={item.id} item={item} onEdit={() => openEdit(item)} />
        ))}
      </div>
    </section>
  );
}

function PatentCard({ item, onEdit }: { item: Patent; onEdit: () => void }) {
  const deletePatent = useDeletePatent();

  const handleDelete = () => {
    if (!window.confirm(`Delete "${item.title}"?`)) return;
    deletePatent.mutate(item.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <div className="flex items-start justify-between rounded-lg border p-3">
      <div>
        <p className="font-medium">{item.title}</p>
        <p className="text-sm text-muted-foreground">
          {[STATUS_LABELS[item.status], item.patent_number, item.filing_date]
            .filter(Boolean)
            .join(" · ")}
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

function PatentDialogContent({
  editing,
  onDone,
}: {
  editing: Patent | null;
  onDone: () => void;
}) {
  const createPatent = useCreatePatent();
  const updatePatent = useUpdatePatent();
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<PatentFormValues>({
    resolver: zodResolver(patentSchema),
    values: editing ? toFormValues(editing) : emptyValues,
  });
  const status = watch("status");
  const isPending = createPatent.isPending || updatePatent.isPending;

  const onSubmit = (values: PatentFormValues) => {
    const payload = {
      ...values,
      patent_number: values.patent_number || null,
      filing_date: values.filing_date || null,
      url: values.url || null,
      description: values.description || null,
    };

    const mutation = editing
      ? updatePatent.mutateAsync({ id: editing.id, payload })
      : createPatent.mutateAsync(payload);

    mutation
      .then(() => {
        toast.success(editing ? "Patent updated." : "Patent added.");
        onDone();
      })
      .catch((error: unknown) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to save.");
      });
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{editing ? "Edit patent" : "Add patent"}</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="title">Title</Label>
          <Input id="title" {...register("title")} />
          {errors.title && <p className="text-sm text-destructive">{errors.title.message}</p>}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="patent_number">Patent number</Label>
            <Input id="patent_number" {...register("patent_number")} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Status</Label>
            <Select
              value={status}
              onValueChange={(value) => setValue("status", value as PatentStatus)}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(STATUS_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="filing_date">Filing date</Label>
            <Input id="filing_date" type="date" {...register("filing_date")} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="url">URL</Label>
            <Input id="url" placeholder="https://" {...register("url")} />
            {errors.url && <p className="text-sm text-destructive">{errors.url.message}</p>}
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

function toFormValues(item: Patent): PatentFormValues {
  return {
    title: item.title,
    patent_number: item.patent_number ?? "",
    status: item.status,
    filing_date: item.filing_date ?? "",
    url: item.url ?? "",
    description: item.description ?? "",
  };
}
