"use client";

import { Sparkles } from "lucide-react";
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
import { Textarea } from "@/components/ui/textarea";
import { useGenerateResume, useResumeTemplates } from "@/features/resumes/hooks/use-resumes";
import { ApiError } from "@/services/api-client";

const MIN_JOB_DESCRIPTION_LENGTH = 50;

export interface GenerateResumeInitialValues {
  jobDescription?: string;
  targetRole?: string;
  targetCompany?: string;
}

export function GenerateResumeDialog({
  autoOpen = false,
  initialValues,
}: {
  autoOpen?: boolean;
  initialValues?: GenerateResumeInitialValues;
}) {
  const { data: templates } = useResumeTemplates();
  const generateResume = useGenerateResume();
  const [open, setOpen] = useState(autoOpen);
  const [templateId, setTemplateId] = useState("");
  const [jobDescription, setJobDescription] = useState(initialValues?.jobDescription ?? "");
  const [targetRole, setTargetRole] = useState(initialValues?.targetRole ?? "");
  const [targetCompany, setTargetCompany] = useState(initialValues?.targetCompany ?? "");

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (next) {
      setTemplateId(templates?.[0]?.id ?? "");
      setJobDescription(initialValues?.jobDescription ?? "");
      setTargetRole(initialValues?.targetRole ?? "");
      setTargetCompany(initialValues?.targetCompany ?? "");
    }
  };

  const effectiveTemplateId = templateId || templates?.[0]?.id || "";

  const handleGenerate = () => {
    if (!effectiveTemplateId || jobDescription.trim().length < MIN_JOB_DESCRIPTION_LENGTH) return;

    generateResume.mutate(
      {
        template_id: effectiveTemplateId,
        job_description: jobDescription.trim(),
        target_role: targetRole.trim() || null,
        target_company: targetCompany.trim() || null,
      },
      {
        onSuccess: (file) => {
          toast.success("Resume generated.");
          setOpen(false);
          window.open(file.url, "_blank", "noopener,noreferrer");
        },
        onError: (error) => {
          toast.error(
            error instanceof ApiError ? error.message : "Failed to generate resume with AI.",
          );
        },
      },
    );
  };

  const isJobDescriptionTooShort = jobDescription.trim().length < MIN_JOB_DESCRIPTION_LENGTH;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Sparkles className="size-4" /> Generate with AI
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Generate a resume with AI</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="target-role">Target role</Label>
              <Input
                id="target-role"
                placeholder="Backend Engineer"
                value={targetRole}
                onChange={(event) => setTargetRole(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="target-company">Target company</Label>
              <Input
                id="target-company"
                placeholder="Acme Corp"
                value={targetCompany}
                onChange={(event) => setTargetCompany(event.target.value)}
              />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Template</Label>
            <Select value={effectiveTemplateId} onValueChange={setTemplateId}>
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
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="job-description">Job description</Label>
            <Textarea
              id="job-description"
              rows={8}
              placeholder="Paste the job description here..."
              value={jobDescription}
              onChange={(event) => setJobDescription(event.target.value)}
            />
            {isJobDescriptionTooShort && jobDescription.length > 0 && (
              <p className="text-xs text-muted-foreground">
                At least {MIN_JOB_DESCRIPTION_LENGTH} characters needed.
              </p>
            )}
          </div>
        </div>
        <DialogFooter>
          <Button
            onClick={handleGenerate}
            disabled={generateResume.isPending || !effectiveTemplateId || isJobDescriptionTooShort}
          >
            {generateResume.isPending ? "Generating... this can take up to a minute" : "Generate"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
