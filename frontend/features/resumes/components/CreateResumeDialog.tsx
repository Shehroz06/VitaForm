"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
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
import { useCreateResume, useResumeTemplates } from "@/features/resumes/hooks/use-resumes";
import { ApiError } from "@/services/api-client";

export function CreateResumeDialog() {
  const router = useRouter();
  const { data: templates } = useResumeTemplates();
  const createResume = useCreateResume();
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [templateId, setTemplateId] = useState("");

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (next) {
      setTitle("");
      setTemplateId(templates?.[0]?.id ?? "");
    }
  };

  const handleCreate = () => {
    if (!title.trim() || !templateId) return;
    createResume.mutate(
      { title: title.trim(), template_id: templateId },
      {
        onSuccess: (resume) => {
          toast.success("Resume created.");
          setOpen(false);
          router.push(`/resumes/${resume.id}`);
        },
        onError: (error) => {
          toast.error(error instanceof ApiError ? error.message : "Failed to create resume.");
        },
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>New resume</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create a resume</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="resume-title">Title</Label>
            <Input
              id="resume-title"
              placeholder="Software Engineer Resume"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Template</Label>
            <Select value={templateId} onValueChange={setTemplateId}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Choose a template" />
              </SelectTrigger>
              <SelectContent>
                {templates?.map((template) => (
                  <SelectItem key={template.id} value={template.id}>
                    {template.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button
            onClick={handleCreate}
            disabled={createResume.isPending || !title.trim() || !templateId}
          >
            {createResume.isPending ? "Creating..." : "Create"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
