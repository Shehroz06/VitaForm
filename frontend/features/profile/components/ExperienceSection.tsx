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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  useCreateExperience,
  useDeleteExperience,
  useExperienceList,
  useUpdateExperience,
} from "@/features/profile/hooks/use-experience";
import { type ExperienceFormValues, experienceSchema } from "@/features/profile/schemas";
import type { EmploymentType, Experience } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

const EMPLOYMENT_TYPE_LABELS: Record<EmploymentType, string> = {
  full_time: "Full-time",
  part_time: "Part-time",
  internship: "Internship",
  contract: "Contract",
  freelance: "Freelance",
  volunteer: "Volunteer",
};

const emptyValues: ExperienceFormValues = {
  company_name: "",
  job_title: "",
  employment_type: "full_time",
  location: "",
  description: "",
  start_date: "",
  end_date: "",
  is_current: false,
};

export function ExperienceSection() {
  const { data: items, isLoading, isError } = useExperienceList();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Experience | null>(null);

  const openCreate = () => {
    setEditing(null);
    setOpen(true);
  };
  const openEdit = (item: Experience) => {
    setEditing(item);
    setOpen(true);
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Experience</h2>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm" onClick={openCreate}>
              <Plus className="size-4" /> Add
            </Button>
          </DialogTrigger>
          <ExperienceDialogContent editing={editing} onDone={() => setOpen(false)} />
        </Dialog>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading experience...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load experience.</p>}
      {items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No experience added yet.</p>
      )}

      <div className="flex flex-col gap-2">
        {items?.map((item) => (
          <ExperienceCard key={item.id} item={item} onEdit={() => openEdit(item)} />
        ))}
      </div>
    </section>
  );
}

function ExperienceCard({ item, onEdit }: { item: Experience; onEdit: () => void }) {
  const deleteExperience = useDeleteExperience();

  const handleDelete = () => {
    if (!window.confirm(`Delete "${item.job_title} at ${item.company_name}"?`)) return;
    deleteExperience.mutate(item.id, {
      onError: () => toast.error("Failed to delete."),
    });
  };

  return (
    <div className="flex items-start justify-between rounded-xl bg-card p-3.5 ring-1 ring-foreground/10 transition-colors hover:bg-muted/40">
      <div>
        <p className="font-medium">{item.job_title}</p>
        <p className="text-sm text-muted-foreground">
          {item.company_name} · {EMPLOYMENT_TYPE_LABELS[item.employment_type]}
        </p>
        <p className="text-xs text-muted-foreground">
          {item.start_date} – {item.is_current ? "Present" : (item.end_date ?? "—")}
          {item.location ? ` · ${item.location}` : ""}
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

function ExperienceDialogContent({
  editing,
  onDone,
}: {
  editing: Experience | null;
  onDone: () => void;
}) {
  const createExperience = useCreateExperience();
  const updateExperience = useUpdateExperience();
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ExperienceFormValues>({
    resolver: zodResolver(experienceSchema),
    values: editing ? toFormValues(editing) : emptyValues,
  });
  const isCurrent = watch("is_current");
  const employmentType = watch("employment_type");
  const isPending = createExperience.isPending || updateExperience.isPending;

  const onSubmit = (values: ExperienceFormValues) => {
    const payload = {
      ...values,
      location: values.location || null,
      description: values.description || null,
      end_date: values.is_current ? null : values.end_date || null,
    };

    const mutation = editing
      ? updateExperience.mutateAsync({ id: editing.id, payload })
      : createExperience.mutateAsync(payload);

    mutation
      .then(() => {
        toast.success(editing ? "Experience updated." : "Experience added.");
        onDone();
      })
      .catch((error: unknown) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to save.");
      });
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{editing ? "Edit experience" : "Add experience"}</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="company_name">Company</Label>
            <Input id="company_name" {...register("company_name")} />
            {errors.company_name && (
              <p className="text-sm text-destructive">{errors.company_name.message}</p>
            )}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="job_title">Job title</Label>
            <Input id="job_title" {...register("job_title")} />
            {errors.job_title && (
              <p className="text-sm text-destructive">{errors.job_title.message}</p>
            )}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>Employment type</Label>
            <Select
              value={employmentType}
              onValueChange={(value) => setValue("employment_type", value as EmploymentType)}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(EMPLOYMENT_TYPE_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="location">Location</Label>
            <Input id="location" {...register("location")} />
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
          I currently work here
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

function toFormValues(item: Experience): ExperienceFormValues {
  return {
    company_name: item.company_name,
    job_title: item.job_title,
    employment_type: item.employment_type,
    location: item.location ?? "",
    description: item.description ?? "",
    start_date: item.start_date,
    end_date: item.end_date ?? "",
    is_current: item.is_current,
  };
}
