"use client";

import { Mail } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useGenerateCoverLetter } from "@/features/companion/hooks/use-companion";
import { ApiError } from "@/services/api-client";

export function GenerateCoverLetterForm() {
  const generateCoverLetter = useGenerateCoverLetter();
  const [companyName, setCompanyName] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const [hiringManager, setHiringManager] = useState("");
  const [jobDescriptionText, setJobDescriptionText] = useState("");

  const handleGenerate = () => {
    if (!companyName.trim() || !roleTitle.trim()) return;
    generateCoverLetter.mutate(
      {
        company_name: companyName.trim(),
        role_title: roleTitle.trim(),
        hiring_manager: hiringManager.trim() || null,
        job_description_text: jobDescriptionText.trim() || null,
      },
      {
        onSuccess: () => {
          toast.success("Cover letter generated.");
          setCompanyName("");
          setRoleTitle("");
          setHiringManager("");
          setJobDescriptionText("");
        },
        onError: (error) => {
          toast.error(
            error instanceof ApiError ? error.message : "Failed to generate cover letter.",
          );
        },
      },
    );
  };

  return (
    <div className="flex flex-col gap-4 rounded-2xl bg-card p-5 ring-1 ring-foreground/10">
      <div className="flex items-center gap-2">
        <span className="flex size-8 items-center justify-center rounded-lg bg-accent text-accent-foreground">
          <Mail className="size-4" />
        </span>
        <div>
          <h2 className="font-heading text-base font-medium text-foreground">
            Generate a cover letter
          </h2>
          <p className="text-sm text-muted-foreground">
            Built from the same profile data as your resume — no retyping.
          </p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="cl-company">Company</Label>
          <Input
            id="cl-company"
            placeholder="Acme Corp"
            value={companyName}
            onChange={(event) => setCompanyName(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="cl-role">Role</Label>
          <Input
            id="cl-role"
            placeholder="Backend Engineer"
            value={roleTitle}
            onChange={(event) => setRoleTitle(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label htmlFor="cl-hiring-manager">Hiring manager (optional)</Label>
          <Input
            id="cl-hiring-manager"
            placeholder="Jane Doe"
            value={hiringManager}
            onChange={(event) => setHiringManager(event.target.value)}
          />
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="cl-job-description">Job description (optional)</Label>
        <Textarea
          id="cl-job-description"
          rows={5}
          placeholder="Paste the job description to tailor the letter..."
          value={jobDescriptionText}
          onChange={(event) => setJobDescriptionText(event.target.value)}
        />
      </div>

      <Button
        onClick={handleGenerate}
        disabled={generateCoverLetter.isPending || !companyName.trim() || !roleTitle.trim()}
        className="self-start"
      >
        {generateCoverLetter.isPending ? "Generating..." : "Generate with AI"}
      </Button>
    </div>
  );
}
