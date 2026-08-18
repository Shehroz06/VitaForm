"use client";

import { Briefcase } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useCreateJob } from "@/features/jobs/hooks/use-jobs";
import { ApiError } from "@/services/api-client";

const MIN_RAW_TEXT_LENGTH = 50;

export function SaveJobForm() {
  const router = useRouter();
  const createJob = useCreateJob();
  const [title, setTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [location, setLocation] = useState("");
  const [rawText, setRawText] = useState("");

  const isTextTooShort = rawText.trim().length < MIN_RAW_TEXT_LENGTH;

  const handleSave = () => {
    if (!title.trim() || isTextTooShort) return;
    createJob.mutate(
      {
        title: title.trim(),
        raw_text: rawText.trim(),
        company_name: companyName.trim() || null,
        location: location.trim() || null,
      },
      {
        onSuccess: (job) => {
          toast.success("Job saved and analyzed.");
          router.push(`/jobs/${job.id}`);
        },
        onError: (error) => {
          toast.error(error instanceof ApiError ? error.message : "Failed to save job.");
        },
      },
    );
  };

  return (
    <div className="flex flex-col gap-4 rounded-2xl bg-card p-5 ring-1 ring-foreground/10">
      <div className="flex items-center gap-2">
        <span className="flex size-8 items-center justify-center rounded-lg bg-accent text-accent-foreground">
          <Briefcase className="size-4" />
        </span>
        <div>
          <h2 className="font-heading text-base font-medium text-foreground">Save a job</h2>
          <p className="text-sm text-muted-foreground">
            We&apos;ll extract keywords and score it against your profile.
          </p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="job-title">Job title</Label>
          <Input
            id="job-title"
            placeholder="Backend Engineer"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="job-company">Company</Label>
          <Input
            id="job-company"
            placeholder="Acme Corp"
            value={companyName}
            onChange={(event) => setCompanyName(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label htmlFor="job-location">Location</Label>
          <Input
            id="job-location"
            placeholder="Remote"
            value={location}
            onChange={(event) => setLocation(event.target.value)}
          />
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="job-raw-text">Job description</Label>
        <Textarea
          id="job-raw-text"
          rows={6}
          placeholder="Paste the job description here..."
          value={rawText}
          onChange={(event) => setRawText(event.target.value)}
        />
        {isTextTooShort && rawText.length > 0 && (
          <p className="text-xs text-muted-foreground">
            At least {MIN_RAW_TEXT_LENGTH} characters needed.
          </p>
        )}
      </div>

      <Button
        onClick={handleSave}
        disabled={createJob.isPending || !title.trim() || isTextTooShort}
        className="self-start"
      >
        {createJob.isPending ? "Saving..." : "Save & analyze"}
      </Button>
    </div>
  );
}
