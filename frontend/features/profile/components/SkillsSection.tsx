"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, X } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
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
import {
  useCreateSkill,
  useDeleteSkill,
  useSkillList,
} from "@/features/profile/hooks/use-skills";
import { type SkillFormValues, skillSchema } from "@/features/profile/schemas";
import type { Skill, SkillCategory, SkillLevel } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

const CATEGORY_LABELS: Record<SkillCategory, string> = {
  technical: "Technical",
  soft: "Soft skill",
  tool: "Tool",
  other: "Other",
};

const LEVEL_LABELS: Record<SkillLevel, string> = {
  beginner: "Beginner",
  intermediate: "Intermediate",
  advanced: "Advanced",
  expert: "Expert",
};

const emptyValues: SkillFormValues = { name: "", category: "technical", level: undefined };

export function SkillsSection() {
  const { data: items, isLoading, isError } = useSkillList();
  const [open, setOpen] = useState(false);
  const deleteSkill = useDeleteSkill();

  const handleDelete = (skill: Skill) => {
    if (!window.confirm(`Remove "${skill.name}"?`)) return;
    deleteSkill.mutate(skill.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Skills</h2>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="size-4" /> Add
            </Button>
          </DialogTrigger>
          <SkillDialogContent onDone={() => setOpen(false)} />
        </Dialog>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading skills...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load skills.</p>}
      {items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No skills added yet.</p>
      )}

      <div className="flex flex-wrap gap-2">
        {items?.map((skill) => (
          <Badge key={skill.id} variant="outline" className="gap-1.5 py-1.5 pr-1">
            {skill.name}
            {skill.level ? ` · ${LEVEL_LABELS[skill.level]}` : ""}
            <button
              type="button"
              onClick={() => handleDelete(skill)}
              aria-label={`Remove ${skill.name}`}
              className="rounded-full p-0.5 hover:bg-muted"
            >
              <X className="size-3" />
            </button>
          </Badge>
        ))}
      </div>
    </section>
  );
}

function SkillDialogContent({ onDone }: { onDone: () => void }) {
  const createSkill = useCreateSkill();
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<SkillFormValues>({ resolver: zodResolver(skillSchema), defaultValues: emptyValues });
  const category = watch("category");
  const level = watch("level");

  const onSubmit = (values: SkillFormValues) => {
    createSkill.mutate(
      { ...values, level: values.level ?? null },
      {
        onSuccess: () => {
          toast.success("Skill added.");
          onDone();
        },
        onError: (error) => {
          toast.error(error instanceof ApiError ? error.message : "Failed to save.");
        },
      },
    );
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Add skill</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="name">Name</Label>
          <Input id="name" placeholder="Python" {...register("name")} />
          {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>Category</Label>
            <Select
              value={category}
              onValueChange={(value) => setValue("category", value as SkillCategory)}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Level (optional)</Label>
            <Select
              value={level}
              onValueChange={(value) => setValue("level", value as SkillLevel)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select level" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(LEVEL_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button type="submit" disabled={createSkill.isPending}>
            {createSkill.isPending ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}
