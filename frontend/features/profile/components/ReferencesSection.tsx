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
  useCreateReference,
  useDeleteReference,
  useReferenceList,
  useUpdateReference,
} from "@/features/profile/hooks/use-references";
import { type ReferenceFormValues, referenceSchema } from "@/features/profile/schemas";
import type { Reference } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

const emptyValues: ReferenceFormValues = {
  name: "",
  relationship: "",
  contact_email: "",
  contact_phone: "",
  description: "",
};

export function ReferencesSection() {
  const { data: items, isLoading, isError } = useReferenceList();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Reference | null>(null);

  const openCreate = () => {
    setEditing(null);
    setOpen(true);
  };
  const openEdit = (item: Reference) => {
    setEditing(item);
    setOpen(true);
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">References</h2>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm" onClick={openCreate}>
              <Plus className="size-4" /> Add
            </Button>
          </DialogTrigger>
          <ReferenceDialogContent editing={editing} onDone={() => setOpen(false)} />
        </Dialog>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading references...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load references.</p>}
      {items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No references added yet.</p>
      )}

      <div className="flex flex-col gap-2">
        {items?.map((item) => (
          <ReferenceCard key={item.id} item={item} onEdit={() => openEdit(item)} />
        ))}
      </div>
    </section>
  );
}

function ReferenceCard({ item, onEdit }: { item: Reference; onEdit: () => void }) {
  const deleteReference = useDeleteReference();

  const handleDelete = () => {
    if (!window.confirm(`Delete "${item.name}"?`)) return;
    deleteReference.mutate(item.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <div className="flex items-start justify-between rounded-lg border p-3">
      <div>
        <p className="font-medium">{item.name}</p>
        <p className="text-sm text-muted-foreground">
          {[item.relationship, item.contact_email, item.contact_phone]
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

function ReferenceDialogContent({
  editing,
  onDone,
}: {
  editing: Reference | null;
  onDone: () => void;
}) {
  const createReference = useCreateReference();
  const updateReference = useUpdateReference();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ReferenceFormValues>({
    resolver: zodResolver(referenceSchema),
    values: editing ? toFormValues(editing) : emptyValues,
  });
  const isPending = createReference.isPending || updateReference.isPending;

  const onSubmit = (values: ReferenceFormValues) => {
    const payload = {
      ...values,
      relationship: values.relationship || null,
      contact_email: values.contact_email || null,
      contact_phone: values.contact_phone || null,
      description: values.description || null,
    };

    const mutation = editing
      ? updateReference.mutateAsync({ id: editing.id, payload })
      : createReference.mutateAsync(payload);

    mutation
      .then(() => {
        toast.success(editing ? "Reference updated." : "Reference added.");
        onDone();
      })
      .catch((error: unknown) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to save.");
      });
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{editing ? "Edit reference" : "Add reference"}</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name">Name</Label>
            <Input id="name" {...register("name")} />
            {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="relationship">Relationship</Label>
            <Input id="relationship" placeholder="Former Manager" {...register("relationship")} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="contact_email">Email</Label>
            <Input id="contact_email" type="email" {...register("contact_email")} />
            {errors.contact_email && (
              <p className="text-sm text-destructive">{errors.contact_email.message}</p>
            )}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="contact_phone">Phone</Label>
            <Input id="contact_phone" {...register("contact_phone")} />
          </div>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="description">Notes</Label>
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

function toFormValues(item: Reference): ReferenceFormValues {
  return {
    name: item.name,
    relationship: item.relationship ?? "",
    contact_email: item.contact_email ?? "",
    contact_phone: item.contact_phone ?? "",
    description: item.description ?? "",
  };
}
