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
  useCreateLanguage,
  useDeleteLanguage,
  useLanguageList,
} from "@/features/profile/hooks/use-languages";
import { type LanguageFormValues, languageSchema } from "@/features/profile/schemas";
import type { Language, LanguageProficiency } from "@/features/profile/types";
import { ApiError } from "@/services/api-client";

const PROFICIENCY_LABELS: Record<LanguageProficiency, string> = {
  basic: "Basic",
  conversational: "Conversational",
  professional: "Professional",
  fluent: "Fluent",
  native: "Native",
};

const emptyValues: LanguageFormValues = { name: "", proficiency: "basic" };

export function LanguagesSection() {
  const { data: items, isLoading, isError } = useLanguageList();
  const [open, setOpen] = useState(false);
  const deleteLanguage = useDeleteLanguage();

  const handleDelete = (language: Language) => {
    if (!window.confirm(`Remove "${language.name}"?`)) return;
    deleteLanguage.mutate(language.id, { onError: () => toast.error("Failed to delete.") });
  };

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Languages</h2>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="size-4" /> Add
            </Button>
          </DialogTrigger>
          <LanguageDialogContent onDone={() => setOpen(false)} />
        </Dialog>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading languages...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load languages.</p>}
      {items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No languages added yet.</p>
      )}

      <div className="flex flex-wrap gap-2">
        {items?.map((language) => (
          <Badge key={language.id} variant="outline" className="gap-1.5 py-1.5 pr-1">
            {language.name} · {PROFICIENCY_LABELS[language.proficiency]}
            <button
              type="button"
              onClick={() => handleDelete(language)}
              aria-label={`Remove ${language.name}`}
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

function LanguageDialogContent({ onDone }: { onDone: () => void }) {
  const createLanguage = useCreateLanguage();
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<LanguageFormValues>({
    resolver: zodResolver(languageSchema),
    defaultValues: emptyValues,
  });
  const proficiency = watch("proficiency");

  const onSubmit = (values: LanguageFormValues) => {
    createLanguage.mutate(values, {
      onSuccess: () => {
        toast.success("Language added.");
        onDone();
      },
      onError: (error) => {
        toast.error(error instanceof ApiError ? error.message : "Failed to save.");
      },
    });
  };

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Add language</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="name">Language</Label>
          <Input id="name" placeholder="French" {...register("name")} />
          {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Proficiency</Label>
          <Select
            value={proficiency}
            onValueChange={(value) => setValue("proficiency", value as LanguageProficiency)}
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(PROFICIENCY_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <DialogFooter>
          <Button type="submit" disabled={createLanguage.isPending}>
            {createLanguage.isPending ? "Saving..." : "Save"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}
