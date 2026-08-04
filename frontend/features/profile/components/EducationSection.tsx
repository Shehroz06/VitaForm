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
  useCreateEducation,
  useDeleteEducation,
  useEducationList,
  useUpdateEducation,
} from "@/features/profile/hooks/use-education";
import { type EducationFormValues, educationSchema } from "@/features/profile/schemas";
import type { Education } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

const emptyValues: EducationFormValues = {
  institution_name: "",
  degree: "",
  field_of_study: "",
  grade: "",
  description: "",
  start_date: "",
  end_date: "",
  is_current: false,
};

export function EducationSection() {
  const { data: items, isLoading, isError } = useEducationList();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Education | null>(null);

  const openCreate = () => {
    setEditing(null);
    setOpen(true);
  };
  const openEdit = (item: Education) => {
    setEditing(item);
    setOpen(true);
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Education</h2>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm" onClick={openCreate}>
              <Plus className="size-4" /> Add
            </Button>
          </DialogTrigger>
          <EducationDialogContent editing={editing} onDone={() => setOpen(false)} />
        </Dialog>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading education...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load education.</p>}
      {items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No education added yet.</p>
      )}

      <div className="flex flex-col gap-2">
        {items?.map((item) => (
          <EducationCard key={item.id} item={item} onEdit={() => openEdit(item)} />
        ))}
      </div>
    </section>
  );
}

function EducationCard({ item, onEdit }: { item: Education; onEdit: () => void }) {
  const deleteEducation = useDeleteEducation();

  const handleDelete = () => {
    if (!window.confirm(`Delete "${item.institution_name}"?`)) return;
    deleteEducation.mutate(item.id, {
      onError: () => toast.error("Failed to delete."),
    });
  };

  return (
    <div className="flex items-start justify-between rounded-lg border p-3">
      <div>
        <p className="font-medium">{item.institution_name}</p>
        <p className="text-sm text-muted-foreground">
          {item.degree}
          {item.field_of_study ? ` · ${item.field_of_study}` : ""}
        </p>
        <p className="text-xs text-muted-foreground">
          {item.start_date} – {item.is_current ? "Present" : (item.end_date ?? "—")}
          {item.grade ? ` · ${item.grade}` : ""}
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

function EducationDialogContent({
  editing,
  onDone,
}: {
  editing: Education | null;
  onDone: () => void;
}) {
  const createEducation = useCreateEducation();
  const updateEducation = useUpdateEducation();
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<EducationFormValues>({
    resolver: zodResolver(educationSchema),
    values: editing ? toFormValues(editing) : emptyValues,
  });
  const isCurrent = watch("is_current");
  const isPending = createEducation.isPending || updateEducation.isPending;

  const onSubmit = (values: EducationFormValues) => {
    const payload = {
      ...values,
      field_of_study: values.field_of_study || null,
      grade: values.grade || null,
      description: values.description || null,
      end_date: values.is_current ? null : values.end_date || null,
    };

    const mutation = editing
      ? updateEducation.mutateAsync({ id: editing.id, payload })
      : createEducation.mutateAsync(payload);

    mutation
      .then(() => {
        toast.success(editing ? "Education updated." : "Education added.");
        onDone();
      })
      .catch((error: unknown) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to save.");
      });
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{editing ? "Edit education" : "Add education"}</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="institution_name">Institution</Label>
          <Input id="institution_name" {...register("institution_name")} />
          {errors.institution_name && (
            <p className="text-sm text-destructive">{errors.institution_name.message}</p>
          )}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="degree">Degree</Label>
            <Input id="degree" {...register("degree")} />
            {errors.degree && <p className="text-sm text-destructive">{errors.degree.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="field_of_study">Field of study</Label>
            <Input id="field_of_study" {...register("field_of_study")} />
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
          Currently studying here
        </label>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="grade">Grade</Label>
          <Input id="grade" placeholder="3.9 GPA" {...register("grade")} />
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

function toFormValues(item: Education): EducationFormValues {
  return {
    institution_name: item.institution_name,
    degree: item.degree,
    field_of_study: item.field_of_study ?? "",
    grade: item.grade ?? "",
    description: item.description ?? "",
    start_date: item.start_date,
    end_date: item.end_date ?? "",
    is_current: item.is_current,
  };
}
