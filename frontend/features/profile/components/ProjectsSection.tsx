"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronDown, Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
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
import { cn } from "@/lib/utils";
import {
  useCreateProject,
  useDeleteProject,
  useProjectList,
  useUpdateProject,
} from "@/features/profile/hooks/use-projects";
import { useSkillList } from "@/features/profile/hooks/use-skills";
import { type ProjectFormValues, projectSchema } from "@/features/profile/schemas";
import type { Project, ProjectStatus } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

const STATUS_LABELS: Record<ProjectStatus, string> = {
  in_progress: "In progress",
  completed: "Completed",
  archived: "Archived",
  on_hold: "On hold",
};

const emptyValues: ProjectFormValues = {
  title: "",
  description: "",
  role: "",
  status: "in_progress",
  start_date: "",
  end_date: "",
  repository_url: "",
  demo_url: "",
  is_pinned: false,
  skill_ids: [],
};

export function ProjectsSection() {
  const { data: items, isLoading, isError } = useProjectList();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Project | null>(null);

  const openCreate = () => {
    setEditing(null);
    setOpen(true);
  };
  const openEdit = (item: Project) => {
    setEditing(item);
    setOpen(true);
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Projects</h2>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm" onClick={openCreate}>
              <Plus className="size-4" /> Add
            </Button>
          </DialogTrigger>
          <ProjectDialogContent editing={editing} onDone={() => setOpen(false)} />
        </Dialog>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading projects...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load projects.</p>}
      {items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No projects added yet.</p>
      )}

      <div className="flex flex-col gap-2">
        {items?.map((item) => (
          <ProjectCard key={item.id} item={item} onEdit={() => openEdit(item)} />
        ))}
      </div>
    </section>
  );
}

function ProjectCard({ item, onEdit }: { item: Project; onEdit: () => void }) {
  const deleteProject = useDeleteProject();

  const handleDelete = () => {
    if (!window.confirm(`Delete "${item.title}"?`)) return;
    deleteProject.mutate(item.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <div className="flex items-start justify-between rounded-xl bg-card p-3.5 ring-1 ring-foreground/10 transition-colors hover:bg-muted/40">
      <div className="flex flex-col gap-1">
        <p className="font-medium">{item.title}</p>
        {item.description && <p className="text-sm text-muted-foreground">{item.description}</p>}
        {item.demo_url && (
          <a
            href={item.demo_url}
            target="_blank"
            rel="noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="w-fit text-sm text-primary hover:underline"
          >
            {item.demo_url}
          </a>
        )}
        {item.skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {item.skills.map((skill) => (
              <Badge key={skill.id} variant="secondary">
                {skill.name}
              </Badge>
            ))}
          </div>
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

function ProjectDialogContent({
  editing,
  onDone,
}: {
  editing: Project | null;
  onDone: () => void;
}) {
  const createProject = useCreateProject();
  const updateProject = useUpdateProject();
  const { data: availableSkills } = useSkillList();
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    values: editing ? toFormValues(editing) : emptyValues,
  });
  const status = watch("status");
  const isPinned = watch("is_pinned");
  const skillIds = watch("skill_ids");
  const isPending = createProject.isPending || updateProject.isPending;
  const [showMore, setShowMore] = useState(
    () => !!(editing && (editing.role || editing.status !== "in_progress" || editing.start_date || editing.repository_url || editing.is_pinned)),
  );

  const toggleSkill = (skillId: string, checked: boolean) => {
    setValue("skill_ids", checked ? [...skillIds, skillId] : skillIds.filter((id) => id !== skillId));
  };

  const onSubmit = (values: ProjectFormValues) => {
    const payload = {
      ...values,
      description: values.description || null,
      role: values.role || null,
      start_date: values.start_date || null,
      end_date: values.end_date || null,
      repository_url: values.repository_url || null,
      demo_url: values.demo_url || null,
    };

    const mutation = editing
      ? updateProject.mutateAsync({ id: editing.id, payload })
      : createProject.mutateAsync(payload);

    mutation
      .then(() => {
        toast.success(editing ? "Project updated." : "Project added.");
        onDone();
      })
      .catch((error: unknown) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to save.");
      });
  };

  return (
    <DialogContent className="max-h-[85vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>{editing ? "Edit project" : "Add project"}</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="title">Title</Label>
          <Input id="title" {...register("title")} />
          {errors.title && <p className="text-sm text-destructive">{errors.title.message}</p>}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="description">Description</Label>
          <Textarea id="description" rows={3} {...register("description")} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="demo_url">URL</Label>
          <Input id="demo_url" placeholder="https://" {...register("demo_url")} />
          {errors.demo_url && <p className="text-sm text-destructive">{errors.demo_url.message}</p>}
        </div>

        {availableSkills && availableSkills.length > 0 && (
          <div className="flex flex-col gap-1.5">
            <Label>Skills used (optional)</Label>
            <div className="flex flex-wrap gap-3 rounded-xl bg-card p-3.5 ring-1 ring-foreground/10">
              {availableSkills.map((skill) => (
                <label key={skill.id} className="flex items-center gap-1.5 text-sm">
                  <Checkbox
                    checked={skillIds.includes(skill.id)}
                    onCheckedChange={(checked) => toggleSkill(skill.id, checked === true)}
                  />
                  {skill.name}
                </label>
              ))}
            </div>
          </div>
        )}

        <button
          type="button"
          onClick={() => setShowMore((v) => !v)}
          className="flex w-fit items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ChevronDown className={cn("size-4 transition-transform", showMore && "rotate-180")} />
          More details
        </button>

        {showMore && (
          <div className="flex flex-col gap-4 border-t border-border pt-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="role">Your role</Label>
                <Input id="role" {...register("role")} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label>Status</Label>
                <Select
                  value={status}
                  onValueChange={(value) => setValue("status", value as ProjectStatus)}
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
                <Label htmlFor="start_date">Start date</Label>
                <Input id="start_date" type="date" {...register("start_date")} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="end_date">End date</Label>
                <Input id="end_date" type="date" {...register("end_date")} />
                {errors.end_date && (
                  <p className="text-sm text-destructive">{errors.end_date.message}</p>
                )}
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="repository_url">Repository URL</Label>
              <Input id="repository_url" placeholder="https://" {...register("repository_url")} />
              {errors.repository_url && (
                <p className="text-sm text-destructive">{errors.repository_url.message}</p>
              )}
            </div>
            <label className="flex items-center gap-2 text-sm">
              <Checkbox
                checked={isPinned}
                onCheckedChange={(checked) => setValue("is_pinned", checked === true)}
              />
              Pin this project
            </label>
          </div>
        )}
        <DialogFooter>
          <Button type="submit" disabled={isPending}>
            {isPending ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}

function toFormValues(item: Project): ProjectFormValues {
  return {
    title: item.title,
    description: item.description ?? "",
    role: item.role ?? "",
    status: item.status,
    start_date: item.start_date ?? "",
    end_date: item.end_date ?? "",
    repository_url: item.repository_url ?? "",
    demo_url: item.demo_url ?? "",
    is_pinned: item.is_pinned,
    skill_ids: item.skills.map((skill) => skill.id),
  };
}
